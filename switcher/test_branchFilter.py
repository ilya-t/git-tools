#!/usr/bin/env python3
from queue import Queue

import test_env
from branch_filter import BranchFilter


class TestBranchFilter(test_env.SwitcherTestCase):
    def setUp(self):
        super().setUp()
        self.input_queue = Queue()
        self.under_test = BranchFilter(cwd=self.test_repo_dir,
                                       input_provider=lambda : self.pop_input())

    def test_find_dev_branch_by_commit_message(self):
        self.input_queue.put('dev')
        self.assertEqual('dev', self.under_test.find_one())
        pass

    def test_find_feature1_branch_by_branch_name(self):
        self.input_queue.put('feature')
        self.input_queue.put('_1')
        self.assertEqual('feature_1', self.under_test.find_one())

    def pop_input(self):
        input = self.input_queue.get()
        print(input)
        return input

