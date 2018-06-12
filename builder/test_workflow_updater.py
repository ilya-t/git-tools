#!/usr/bin/env python3
import os
import unittest

import test_env
import workflow_updater


class WorkFlowTestCase(test_env.RepoTestCase):
    def setUp(self):
        super().setUp()
        workflow_updater.CWD = test_env.REPO_DIR
        workflow_updater.SUPPRESS_PROMPTS_FOR_TESTS = True
    
    def tearDown(self):
        # super().tearDown() # comment to keep test env
        pass

    def amend(self, branch, amended_file):
        self.run_cmd(
            "git checkout " + branch,
            "echo '" + amended_file + " file amended!' > " + amended_file,
            "git commit --all --amend --message 'amended " + amended_file + "'",
        )

    def assertFileAmended(self, file):
        with open(test_env.REPO_DIR + '/' + file, mode='r') as f:
            f1_file_body = f.readline()
            f.close()
        self.assertEqual(file+' file amended!\n', f1_file_body)


class MultiAmendTestCase(WorkFlowTestCase):
    def setUp(self):
        super().setUp()
        self.amend(branch = 'feature_1',amended_file = 'f1_file')
        self.amend(branch = 'dev', amended_file = 'dev_file')
        self.amend(branch = 'feature_2', amended_file = 'f2_file')
        self.run_cmd('git checkout feature_2')
        workflow_updater.parse_args([test_env.TEST_DIR+'/single_base_workspace.yml'])

    def test_feature1_file_amended(self):
        self.assertFileAmended('f1_file')

    def test_feature2_file_amended(self):
        self.assertFileAmended('f2_file')

    def test_dev_file_amended(self):
        self.assertFileAmended('dev_file')

    def test_feature1_deleted_file(self):
        self.assertFalse(os.path.exists(test_env.REPO_DIR+'/f1_to_be_deleted'))


class MultiBasementBranchTestCase(WorkFlowTestCase):
    def setUp(self):
        super().setUp()
        self.amend(branch = 'master',amended_file = 'README.md')
        self.amend(branch = 'feature_1',amended_file = 'f1_file')

        self.dev_log = self.captureLog('dev')
        self.hotfix_log = self.captureLog('hotfix')
        self.f2_log = self.captureLog('feature_2')

        workflow_updater.parse_args([test_env.TEST_DIR+'/multi_base_workspace.yml'])

    def test_feature1_file_amended(self):
        self.run_cmd('git checkout feature_1')
        self.assertFileAmended('f1_file')

    def test_feature1_deleted_file(self):
        self.assertFalse(os.path.exists(test_env.REPO_DIR+'/f1_to_be_deleted'))

    def test_dev_rebased_cause_master_amended(self):
        self.assertNotEquals(self.dev_log, self.captureLog('dev'))

    def test_hotfix_rebased_cause_master_amended(self):
        self.assertNotEquals(self.hotfix_log, self.captureLog('hotfix'))

    def test_feature2_untouched_despite_amends(self):
        self.assertEqual(self.f2_log, self.captureLog('feature_2'))

    def captureLog(self, branch):
        self.run_cmd('git checkout '+branch)
        return test_env.capture_cmd_output('git log -1')



if __name__ == '__main__':
    unittest.main()
