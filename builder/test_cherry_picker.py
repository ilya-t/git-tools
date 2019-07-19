#!/usr/bin/env python3
import os

import test_env


class TestF1UpdateUnderF2(test_env.RepoTestCase):

    def setUp(self):
        super().setUp()
        self.undertest = test_env.repo_picker(
            target_branch='feature_2',
            basement_branch='feature_1',
            branches_to_cherry_pick=['feature_2']
        )

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

    def test_everything_is_up_to_date(self):
        self.assertTrue(self.undertest.up_to_date())

    def test_non_existing_branch_created(self):
        self.undertest = test_env.repo_picker(
            target_branch='new_branch',
            basement_branch='dev',
            branches_to_cherry_pick=['hotfix']
        )
        self.cherry_pick()

        self.assertTrue(os.path.exists(test_env.REPO_DIR + '/hotfix_file'))

    def test_cherry_pick_can_be_empty(self):
        self.undertest = test_env.repo_picker(
            target_branch='new_branch_on_top',
            basement_branch='feature_1',
            branches_to_cherry_pick=[]
        )
        self.cherry_pick()

        self.assertTrue(os.path.exists(test_env.REPO_DIR + '/f1_file'))

    def amend_f1_and_ch_f2(self):
        self.run_cmd(
            "git checkout feature_1",
            "echo 'f1 updated' > f1_file",
            "git commit --all --amend --message 'upd f1'",
            "git checkout feature_2"
        )

    def cherry_pick(self):
        self.undertest.run()
