#!/usr/bin/env python3
import os
import shutil
import subprocess
from unittest import TestCase

TEST_DIR = os.path.dirname(os.path.dirname(__file__)) + '/tests'
REPO_DIR = TEST_DIR + '/repo'


class TestEnvTestCase(TestCase):
    def setUp(self):
        self.test_repo_dir=REPO_DIR
        self.cleanup()
        self.init_repo()
        self.assertTrue(os.path.exists(REPO_DIR + '/README.md'))

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        if os.path.exists(REPO_DIR):
            shutil.rmtree(REPO_DIR)

    def init_repo(self):
        if not os.path.exists(REPO_DIR):
            os.makedirs(REPO_DIR)
        self.run_cmd(TEST_DIR + '/init.sh')

    def run_cmd(self, *commands):
        for command in commands:
            with    subprocess.Popen(command,
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