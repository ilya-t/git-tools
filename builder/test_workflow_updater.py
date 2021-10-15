#!/usr/bin/env python3
import os
import subprocess
import unittest
from queue import Queue

import cherry_picker
import testenv
import workflow_updater
from workflow_updater import WorkflowBuilder


class WorkFlowTestCase(testenv.RepoTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()  # comment to keep test env
        pass

    def amend(self, branch, amended_file):
        self._repo_helper.amend(branch, amended_file)

    def assertCommitMessage(self, branch, expected_message):
        self._repo_helper.assertCommitMessage(branch, expected_message)

    def assertFileAmended(self, file):
        self._repo_helper.assertFileAmended(file)


class MultiAmendTestCase(WorkFlowTestCase):
    def setUp(self):
        super().setUp()
        self.amend(branch='feature_1', amended_file='f1_file')
        self.amend(branch='dev', amended_file='dev_file')
        self.amend(branch='feature_2', amended_file='f2_file')
        self.run_cmd('git checkout feature_2')
        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/single_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=cherry_picker.always_confirm).start()

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

        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/multi_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=cherry_picker.always_confirm).start()

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
        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/single_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=cherry_picker.always_confirm).start()
        self.assertFileAmended('f1_file')

    def test_cherry_pick_conflicts_abort_should_stop_flow(self):
        self.run_cmd(
            'git checkout feature_1',
            'echo conflict > f2_file',
            'git add f2_file',
            'git commit --amend --message "add f1 and f2 files"'
        )

        self.set_input('no')

        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/single_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=lambda: self.pop_input()).start()

        self.assertEqual('', self.capture_cmd_output('git status --short'))
        self.assertIn(member='master', container=self.capture_cmd_output('git rev-parse --abbrev-ref HEAD'))

    def test_cherry_pick_decline_should_stop_flow(self):
        self.amend(branch='dev', amended_file='dev_file')
        self.set_input('no')

        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/single_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=lambda: self.pop_input()).start()

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
        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/single_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=lambda: self.pop_input()).start()
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

        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/single_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=lambda: self.pop_input()).start()
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
        WorkflowBuilder(yaml_config=testenv.TEST_DIR + '/single_base_workspace.yml',
                        cwd=testenv.REPO_DIR,
                        input_provider=lambda: self.pop_input()).start()
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


class MultiReposTestCase(WorkFlowTestCase):
    def setUp(self):
        super().setUp()
        self._repo1 = testenv.RepoHelper(self, '/tmp/test_repos/repo1')
        self._repo1.init_repo()
        self._repo1.amend(branch='dev', amended_file='dev_file')
        self._repo1.amend(branch='hotfix', amended_file='hotfix_file')

        self._repo2 = testenv.RepoHelper(self, '/tmp/test_repos/repo2')
        self._repo2.init_repo()
        self._repo2.amend(branch='feature_1', amended_file='f1_file')
        self._repo2.amend(branch='hotfix', amended_file='hotfix_file')
        WorkflowBuilder(
            yaml_config=testenv.TEST_DIR + '/multi_repo_workspace.yml',
            cwd = self._repo1._repo_dir,
            input_provider=cherry_picker.always_confirm
        ).start()
        WorkflowBuilder(
            yaml_config=testenv.TEST_DIR + '/multi_repo_workspace.yml',
            cwd = self._repo2._repo_dir,
            input_provider=cherry_picker.always_confirm
        ).start()

    def test_repo1_processed_with_repo1_config(self):
        self._repo1.assertCommitMessage(branch='dev', expected_message='edited by repo1 config')

    def test_repo2_processed_with_repo2_config(self):
        self._repo2.assertCommitMessage(branch='dev', expected_message='edited by repo2 config')

if __name__ == '__main__':
    unittest.main()
