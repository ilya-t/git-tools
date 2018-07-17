#!/usr/bin/env python3
import os
import time

import test_env


class TestF1UpdateUnderF2(test_env.RepoTestCase):
    def test_feature2_files_exists(self):
        self.amend_f1_and_ch_f2()
        self.cherry_pick()
        self.assertTrue(os.path.exists(test_env.REPO_DIR + '/f2_file'))

    def test_feature1_files_up_to_date(self):
        self.amend_f1_and_ch_f2()
        self.cherry_pick()

        with open(test_env.REPO_DIR + '/f1_file', mode='r') as f:
            f1_file_body = f.readline()
            f.close()
        self.assertEqual('f1 updated\n', f1_file_body)

    def test_previous_tmp_branch_does_not_harm_picker(self):
        self.amend_f1_and_ch_f2()
        self.run_cmd('git branch tmp/feature_2 master')
        self.cherry_pick()
        self.assertTrue(os.path.exists(test_env.REPO_DIR + '/f2_file'))


    def amend_f1_and_ch_f2(self):
        self.run_cmd(
            "git checkout feature_1",
            "echo 'f1 updated' > f1_file",
            "git commit --all --amend --message 'upd f1'",
            "git checkout feature_2"
        )

    def cherry_pick(self):
        test_env.repo_picker().run(
            target_branch='feature_2',
            basement_branch='feature_1',
            branches_to_cherry_pick=['feature_2']
        )



class TestUpdateOnlyChangedBranches(test_env.RepoTestCase):
    def setUp(self):
        super().setUp()
        self.run_cmd('git checkout feature_2')
        time.sleep(1) # TODO removes flakiness
        self.log_before = self.captureLog()
        print(self.log_before)
        test_env.repo_picker().run(
            target_branch='feature_2',
            basement_branch='feature_1',
            branches_to_cherry_pick=['feature_2']
        )

    def test_commits_unchanged(self):
        log_after = self.captureLog()
        self.assertEqual(self.log_before, log_after,
                         'commits should not change!')

    def captureLog(self):
        return test_env.capture_cmd_output('git log -1')
        # return ''.join(test_env.capture_cmd_output('git log -1'))


