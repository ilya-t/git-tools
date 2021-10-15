#!/usr/bin/env python3
import os
import shutil
import subprocess
import unittest
import cherry_picker

TEST_DIR = os.path.dirname(os.path.dirname(__file__)) + '/tests'

REPO_DIR = TEST_DIR + '/repo'
TEST_LOG_FILE = TEST_DIR + '/test.log'
ENABLE_REPO_CACHING = False

def repo_picker(target_branch, basement_branch, branches_to_cherry_pick):
    branch_contents = list(map(lambda e: {
        cherry_picker.CONTENT_COMMIT: e,
        cherry_picker.CONTENT_MESSAGE: None
    }, branches_to_cherry_pick))
    return cherry_picker.Picker(target_branch=target_branch,
                                basement_branch=basement_branch,
                                branch_contents=branch_contents,
                                log_file=TEST_LOG_FILE,
                                cwd=REPO_DIR,
                                verbose_ouput=True,
                                input_provider=cherry_picker.always_confirm)


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
        self._repo_helper = RepoHelper(self, REPO_DIR)
        self.cleanup()
        self.init_repo()
        self.assertTrue(os.path.exists(REPO_DIR + '/README.md'))

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        self._repo_helper.cleanup()

    def init_repo(self):
        self._repo_helper.init_repo()

    def run_cmd(self, *commands):
        self._repo_helper.run_cmd(*commands)


class RepoHelper:
    def __init__(self, test_case: unittest.TestCase, repo_dir: str):
        self._test_case = test_case
        self._repo_dir: str = repo_dir
        
    def cleanup(self):
        if os.path.exists(self._repo_dir):
            shutil.rmtree(self._repo_dir)

        if os.path.exists(TEST_LOG_FILE):
            os.remove(TEST_LOG_FILE)

    def init_repo(self):
        self.cleanup()
        cached_repo_path = TEST_DIR+'/repo-cache'

        if not os.path.exists(self._repo_dir):
            os.makedirs(self._repo_dir)

        if ENABLE_REPO_CACHING and os.path.exists(cached_repo_path+'/.git'):
            self.run_cmd('cp -R '+cached_repo_path+' '+self._repo_dir)
            return

        self.run_cmd(TEST_DIR + '/init.sh')
        
        if ENABLE_REPO_CACHING:
            if not os.path.exists(cached_repo_path):
                os.makedirs(cached_repo_path)
            self.run_cmd('cp -R '+self._repo_dir + ' '+cached_repo_path)

    def run_cmd(self, *commands):
        for command in commands:
            with subprocess.Popen(command,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True,
                                 cwd=self._repo_dir) as p:
                retcode = p.wait()
                if retcode != 0:
                    self._test_case.fail('failed to execute command:' + command + "\nOutput:\n" +
                              '\n'.join(p.stdout.readlines()) + '\n' +
                              '\n'.join(p.stderr.readlines()))
                # else:
                #     print(p.stdout.readlines())    

    def amend(self, branch: str, amended_file: str):
        self.run_cmd(
            "git checkout " + branch,
            "echo '" + amended_file + " file amended!' > " + amended_file,
            "git commit --all --amend --message 'amended " + amended_file + "'",
        )

    def assertCommitMessage(self, branch: str, expected_message: str):
        self.run_cmd('git checkout ' + branch)
        command = 'git log -1 --oneline'
        with subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              cwd=self._repo_dir) as p:
            retcode = p.wait()
            if retcode != 0:
                self._test_case.fail('failed to execute command:' + command + "\nOutput:\n" +
                          '\n'.join(p.stdout.readlines()) + '\nError output:\n' +
                          '\n'.join(p.stderr.readlines()))
            out = ''.join(p.stdout.readlines())

            self._test_case.assertTrue(expected_message in out, msg='Commit message not contains "' + expected_message + '"! ' +
                                                         'Instead got:' + out)

    def assertFileAmended(self, file: str):
        with open(self._repo_dir + '/' + file, mode='r') as f:
            f1_file_body = f.readline()
            f.close()
        self._test_case.assertEqual(file + ' file amended!\n', f1_file_body)