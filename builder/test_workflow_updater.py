#!/usr/bin/env python3
import os
import subprocess
import unittest
from queue import Queue

import cherry_picker
import testenv
import workflow_updater


class WorkFlowTestCase(testenv.RepoTestCase):
    def setUp(self):
        super().setUp()
        workflow_updater.CWD = testenv.REPO_DIR

    def tearDown(self):
        super().tearDown()  # comment to keep test env
        pass

    def amend(self, branch, amended_file):
        self.run_cmd(
            "git checkout " + branch,
            "echo '" + amended_file + " file amended!' > " + amended_file,
            "git commit --all --amend --message 'amended " + amended_file + "'",
        )

    def assertCommitMessage(self, branch, expected_message):
        self.run_cmd('git checkout ' + branch)
        command = 'git log -1 --oneline'
        with subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              cwd=testenv.REPO_DIR) as p:
            retcode = p.wait()
            if retcode != 0:
                self.fail('failed to execute command:' + command + "\nOutput:\n" +
                          '\n'.join(p.stdout.readlines()) + '\n' +
                          '\n'.join(p.stderr.readlines()))
            out = ''.join(p.stdout.readlines())

            self.assertTrue(expected_message in out, msg='Commit message not contains "' + expected_message + '"! ' +
                                                         'Instead got:' + out)

    def assertFileAmended(self, file):
        with open(testenv.REPO_DIR + '/' + file, mode='r') as f:
            f1_file_body = f.readline()
            f.close()
        self.assertEqual(file + ' file amended!\n', f1_file_body)


class MultiAmendTestCase(WorkFlowTestCase):
    def setUp(self):
        super().setUp()
        self.amend(branch='feature_1', amended_file='f1_file')
        self.amend(branch='dev', amended_file='dev_file')
        self.amend(branch='feature_2', amended_file='f2_file')
        self.run_cmd('git checkout feature_2')
        workflow_updater.process_config(testenv.TEST_DIR + '/single_base_workspace.yml', cherry_picker.always_confirm)

    def test_feature1_file_amended(self):
        self.assertFileAmended('f1_file')

    def test_feature2_file_amended(self):
        self.assertFileAmended('f2_file')

    def test_dev_file_amended(self):
        self.assertFileAmended('dev_file')

    def test_feature1_deleted_file(self):
        self.assertFalse(os.path.exists(testenv.REPO_DIR + '/f1_to_be_deleted'))

    def test_feature1_has_custom_commit_message(self):
        self.assertCommitMessage(branch='feature_1', expected_message='custom commit on "feature_1" branch')

    def test_feature1_has_custom_commit_message_and_valid_content(self):
        self.assertCommitMessage(branch='feature_1~2', expected_message='add f1_to_be_deleted')
        self.assertTrue(os.path.exists(testenv.REPO_DIR + '/f1_to_be_deleted'), 'file not found!')


class MultiBasementBranchTestCase(WorkFlowTestCase):
    def setUp(self):
        super().setUp()
        self.amend(branch='master', amended_file='README.md')
        self.amend(branch='feature_1', amended_file='f1_file')

        self.dev_log = self.captureLog('dev')
        self.hotfix_log = self.captureLog('hotfix')
        self.f2_log = self.captureLog('feature_2')

        workflow_updater.process_config(testenv.TEST_DIR + '/multi_base_workspace.yml', cherry_picker.always_confirm)

    def test_feature1_file_amended(self):
        self.run_cmd('git checkout feature_1')
        self.assertFileAmended('f1_file')

    def test_feature1_deleted_file(self):
        self.assertFalse(os.path.exists(testenv.REPO_DIR + '/f1_to_be_deleted'))

    def test_dev_rebased_cause_master_amended(self):
        self.assertNotEquals(self.dev_log, self.captureLog('dev'))

    def test_hotfix_rebased_cause_master_amended(self):
        self.assertNotEquals(self.hotfix_log, self.captureLog('hotfix'))

    def test_feature2_untouched_despite_amends(self):
        self.assertEqual(self.f2_log, self.captureLog('feature_2'))

    def test_non_existing_branch_created(self):
        self.assertFileExists(branch='non_existing_branch', file_name='hotfix_file')

    def test_non_existing_branch_without_commits_created(self):
        self.assertFileExists(branch='empty_new_branch', file_name='hotfix_file')

    def captureLog(self, branch):
        self.run_cmd('git checkout ' + branch)
        return testenv.capture_cmd_output('git log -1')

    def assertFileExists(self, branch, file_name):
        self.run_cmd('git checkout ' + branch)
        name = testenv.REPO_DIR + '/' + file_name
        self.assertTrue(os.path.exists(name),
                        msg='File "' + file_name + '" not exists in branch "' + branch + '"')
        pass


class ConflictsTestCase(WorkFlowTestCase):
    def setUp(self):
        self.input_queue = Queue()
        super().setUp()
        self.amend(branch='feature_1', amended_file='f1_file')

    def test_already_on_tmp_branch_has_no_effect(self):
        self.run_cmd('git checkout -b tmp/feature_1')
        workflow_updater.process_config(testenv.TEST_DIR + '/single_base_workspace.yml', cherry_picker.always_confirm)
        self.assertFileAmended('f1_file')

    def test_cherry_pick_conflicts_abort_should_stop_flow(self):
        self.run_cmd(
            'git checkout feature_1',
            'echo conflict > f2_file',
            'git add f2_file',
            'git commit --amend --message "add f1 and f2 files"'
        )

        self.set_input('no')

        workflow_updater.process_config(testenv.TEST_DIR + '/single_base_workspace.yml',
                                        input_provider=lambda: self.pop_input())

        self.assertEqual('', self.capture_cmd_output('git status --short'))
        self.assertIn(member='master', container=self.capture_cmd_output('git rev-parse --abbrev-ref HEAD'))

    def test_cherry_pick_decline_should_stop_flow(self):
        self.amend(branch='dev', amended_file='dev_file')
        self.set_input('no')

        workflow_updater.process_config(testenv.TEST_DIR + '/single_base_workspace.yml',
                                        input_provider=lambda: self.pop_input())

        self.assertEqual('', self.capture_cmd_output('git status --short'))
        self.assertIn(member='master', container=self.capture_cmd_output('git rev-parse --abbrev-ref HEAD'))

    def test_build_wont_start_when_have_staged_changes(self):
        self.run_cmd(
            'git checkout feature_1',
            'echo staged > f2_file',
            'git add f2_file'
        )
        self.set_input('no')
        diff_before = self.capture_cmd_output('git status --short')
        workflow_updater.process_config(testenv.TEST_DIR + '/single_base_workspace.yml',
                                        input_provider=lambda: self.pop_input())
        diff_after = self.capture_cmd_output('git status --short')
        self.assertEqual(diff_after, diff_before)

    def test_build_will_commit_staged_changes_to_head(self):
        self.run_cmd(
            'git checkout feature_1',
            'echo staged > f1_extra_file',
            'git add f1_extra_file'
        )
        diff_before = self.capture_cmd_output('git status --short')
        self.assertTrue('f1_extra_file' in diff_before, msg='Diff not contains expected file!\nDiff:'+diff_before)
        self.set_input(
            'yes', # amend commit?
            'yes' # assembled properly?
        )

        workflow_updater.process_config(testenv.TEST_DIR + '/single_base_workspace.yml',
                                        input_provider=lambda: self.pop_input())
        diff_after = self.capture_cmd_output('git status --short')
        self.assertNotEqual(diff_after, diff_before)
        self.assertTrue(os.path.isfile(testenv.REPO_DIR + '/f1_extra_file'))

    def test_build_wont_start_when_have_unstaged_changes(self):
        self.run_cmd(
            'git checkout feature_1',
            'echo changed > f2_file'
        )
        self.set_input('no')
        diff_before = self.capture_cmd_output('git status --short')
        workflow_updater.process_config(testenv.TEST_DIR + '/single_base_workspace.yml',
                                        input_provider=lambda: self.pop_input())
        diff_after = self.capture_cmd_output('git status --short')
        self.assertEqual(diff_after, diff_before)

    def pop_input(self):
        self.assertFalse(self.input_queue.empty(), 'Queue is empty but input requested!')
        input = self.input_queue.get()
        print(input)
        return input

    def set_input(self, *params):
        for param in params:
            self.input_queue.put(param)

    def capture_cmd_output(self, command):
        with subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              cwd=testenv.REPO_DIR) as p:
            stdout, stderr = p.communicate()
            return stdout


if __name__ == '__main__':
    unittest.main()
