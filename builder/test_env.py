#!/usr/bin/env python3
import os
import shutil
import subprocess
import unittest
import cherry_picker

TEST_DIR = os.path.dirname(os.path.dirname(__file__)) + '/tests'

REPO_DIR = TEST_DIR + '/repo'
TEST_LOG_FILE = TEST_DIR + '/test.log'


def repo_picker():
    return cherry_picker.Picker(log_file=TEST_LOG_FILE,
                                cwd=REPO_DIR,
                                verbose_ouput=True,
                                suppress_prompts=True)


def capture_cmd_output(command):
    with subprocess.Popen(command,
        shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True,
                          cwd=REPO_DIR) as p:
        stdout, stderr = p.communicate()
        return stdout


class RepoTestCase(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.init_repo()
        self.assertTrue(os.path.exists(REPO_DIR + '/README.md'))

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        if os.path.exists(REPO_DIR):
            shutil.rmtree(REPO_DIR)

        if os.path.exists(TEST_LOG_FILE):
            os.remove(TEST_LOG_FILE)

    def init_repo(self):
        if not os.path.exists(REPO_DIR):
            os.makedirs(REPO_DIR)
        self.run_cmd(TEST_DIR + '/init.sh')

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