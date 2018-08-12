#!/usr/bin/env python3
import os
import shutil
import subprocess
import unittest

import clean_merged
import test_env

'git checkout master'
'git merge dev'
'git merge hotfix --message="this is merge commit"'
TEST_DIR = os.path.dirname(os.path.dirname(__file__)) + '/tests'

REPO_DIR = TEST_DIR + '/repo'
TEST_LOG_FILE = TEST_DIR + '/delete_test.log'


class CleanMergedTestCase(test_env.TestEnvTestCase):
    def setUp(self):
        super().setUp()
        self.run_cmd(
            'git checkout master',
            'git merge dev',
            'git merge hotfix --message "hotifx merged after dev"'
        )

        clean_merged.Cleaner(cwd=self.test_repo_dir)

    def test_dev_deleted(self):
        self.assertNotIn('dev', self.capture_cmd_output('git branch'),
                         'Merged branch "dev" not deleted!')

    def test_hotfix_deleted(self):
        self.assertNotIn('hotfix', self.capture_cmd_output('git branch'),
                         'Merged branch "hotfix" not deleted!')

    def test_master_exists(self):
        self.assertIn('master', self.capture_cmd_output('git branch'),
                         'Branch "master" deleted, but shoult be kept!')

    def test_feature_branches_exists(self):
        self.assertIn('feature_1', self.capture_cmd_output('git branch'),
                         'Branch "feature_1" deleted, but shoult be kept!')
        self.assertIn('feature_2', self.capture_cmd_output('git branch'),
                         'Branch "feature_1" deleted, but shoult be kept!')

    def capture_cmd_output(self, command):
        with subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              cwd=REPO_DIR) as p:
            stdout, stderr = p.communicate()
            return stdout

    def run_cmd(self, *commands):
        for command in commands:
            with subprocess.Popen(command,
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True,
                                  cwd=REPO_DIR) as p:
                retcode = p.wait()
                if retcode != 0:
                    for line in p.stdout.readlines():
                        print(line)
                    self.fail('failed to execute command:' + command)


if __name__ == '__main__':
    unittest.main()
