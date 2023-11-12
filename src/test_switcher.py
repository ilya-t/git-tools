#!/usr/bin/env python3
from queue import Queue

import testenv
from run_switcher import Switcher


class TestSwitcher(testenv.RepoTestCase):
    def setUp(self):
        super().setUp()
        self.input_queue = Queue()
        self.under_test = self.create_sut()

    def create_sut(self):
        return Switcher(cwd=testenv.REPO_DIR,
                        initial_input=None,
                        workflow_config=testenv.REPO_DIR + '/../single_base_workspace.yml',
                        input_provider=lambda: self.pop_input(),
                        dry_run=False,
                        )

    def test_basic_switching(self):
        self.set_input('dev')
        self.under_test.execute()
        self.repo_helper.assertOnBranch('dev')

        self.set_input('feature_1')
        self.under_test.execute()
        self.repo_helper.assertOnBranch('feature_1')

    def test_switch_with_automatic_rebuild(self):
        self.set_input('dev')
        self.under_test.execute()
        self.repo_helper.assertOnBranch('dev')
        self.repo_helper.amend(branch=None, amended_file='dev_file')

        self.set_input('feature_1')
        self.create_sut().execute()
        self.repo_helper.assertOnBranch('feature_1')
        self.repo_helper.assertFileAmended('dev_file')

    def pop_input(self):
        self.assertFalse(self.input_queue.empty(), 'Queue is empty but input requested!')
        input = self.input_queue.get()
        print(input)
        return input

    def set_input(self, *params):
        for param in params:
            self.input_queue.put(param)
