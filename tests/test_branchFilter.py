#!/usr/bin/env python3
from queue import Queue
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__))+'/switcher')

import test_env
from branch_filter import BranchFilter


class TestBranchFilter(test_env.RepoTestCase):
    def setUp(self):
        super().setUp()
        self.input_queue = Queue()
        self.under_test = BranchFilter(cwd=self.test_repo_dir,
                                       input_provider=lambda : self.pop_input())

    def test_find_dev_branch_by_commit_message_part(self):
        self.set_input('dev_file')
        self.assertEqual('dev', self.under_test.find_one())
        pass

    def test_find_feature1_branch_by_branch_name(self):
        self.set_input('feature', '_1')
        self.assertEqual('feature_1', self.under_test.find_one())

    def test_empty_input_does_not_reset_filtered_branches(self):
        self.set_input('feature', '', '_1')
        self.assertEqual('feature_1', self.under_test.find_one())

    def pop_input(self):
        self.assertFalse(self.input_queue.empty(), 'Queue is empty but input requested!')
        input = self.input_queue.get()
        print(input)
        return input

    def set_input(self, *params):
        for param in params:
            self.input_queue.put(param)
