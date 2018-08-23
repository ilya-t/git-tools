#!/usr/bin/env python3
import os
import subprocess
import sys
import colorama

class Cleaner:

    def __init__(self,
                 log_file=os.path.dirname(__file__) + '/delete.log',
                 cwd=os.path.abspath(''),
                 upstream='origin/master',
                 suppress_prompt=False
                 ):
        self.log_file = log_file
        self.cwd = find_dot_git(cwd)
        self.upstream = upstream
        self.suppress_prompt = suppress_prompt

    def run(self):
        branches_str = self.capture_output('git branch')
        self.current_branch = self.capture_output('git rev-parse --abbrev-ref HEAD').splitlines()[0]
        self.all_branches = branches_str.replace('* ', '').replace(' ', '').splitlines()
        self.merged_branches = list(filter(self.is_merged, self.all_branches))
        self.unmerged_branches = list(filter(lambda branch: branch not in self.merged_branches, self.all_branches))

        if len(self.merged_branches) == 0:
            print('All existing branches already merged!')

        self.head_commits = {}

        list(map(self.get_commit, self.all_branches))

        print('Merged to upstream '+self.upstream+':')

        print(colorama.Fore.RED)
        for merged in self.merged_branches:
            self.print_branch_desc(merged)
        print(colorama.Fore.RESET)

        print('Not yet merged to upstream '+self.upstream+':')
        print(colorama.Fore.GREEN)
        for branch in self.unmerged_branches:
            self.print_branch_desc(branch)
        print(colorama.Fore.RESET)

        if self.suppress_prompt or query_yes_no('Delete merged branches?'):
            print('\nDeleting:')
            for merged in self.merged_branches:
                if merged != self.current_branch:
                    self.git_branch_minus_D(merged)

    def get_commit(self, branch):
        full_commit_log = self.capture_output('git show -s --format=%B $(git rev-parse ' + branch + '~0)')
        fisrt_return = full_commit_log.index('\n')
        self.head_commits[branch] = full_commit_log[0:fisrt_return]

    def is_merged(self, branch):
        return self.capture_output('git log '+branch+' --not '+self.upstream) == ''

    def capture_output(self, cmd):
        return subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)

    def print_branch_desc(self, branch):
        branch_with_max_len = max(self.all_branches, key=len)
        padding_str = ''

        for i in range(0, len(branch_with_max_len) - len(branch)):
            padding_str = padding_str + ' '

        output = branch + padding_str + ' | ' + self.head_commits[branch]
        print(output)

    def git_branch_minus_D(self, _branch):
        self.run_cmd('git branch -D '+_branch, log_output=True)
        pass

    def run_cmd(self, command, fallback=None, log_output=False, print_output=True):
        with subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              cwd=self.cwd) as p:
            result = p.wait()
            output = p.stdout.readlines()
            error = p.stderr.readlines()

            if print_output or result != 0:
                for line in output:
                    print(line)


            if log_output:
                with open(self.log_file, mode='a') as f:
                    for line in output:
                        print(line, file=f)

        if result != 0:
            if fallback is None:
                raise Exception('shell command failed: ' + command + '\n with: ' + error.__str__())
            else:
                fallback()


def find_dot_git(path):
    candidate = os.path.abspath(path)

    if (os.path.exists(candidate + '/.git')):
        return candidate
    else:
        return find_dot_git(os.path.dirname(candidate))


REPO_PATH = find_dot_git('.')

def query_yes_no(question, default='yes'):
    '''Ask a yes/no question via raw_input() and return their answer.

    'question' is a string that is presented to the user.
    'default' is the presumed answer if the user just hits <Enter>.
        It must be 'yes' (the default), 'no' or None (meaning
        an answer is required of the user).

    The 'answer' return value is one of 'yes' or 'no'.
    '''
    valid = {'yes': 'yes', 'y': 'yes', 'ye': 'yes',
             'no': 'no', 'n': 'no'}
    if default == None:
        prompt = ' [y/n] '
    elif default == 'yes':
        prompt = ' [Y/n] '
    elif default == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " \
                             "(or 'y' or 'n').\n")
pass


if __name__ == '__main__':
    args = sys.argv[1:]

    if len(sys.argv) > 1:
        Cleaner(upstream=args[0]).run()
    else:
        Cleaner(cwd='/home/i-ts/workspace/browser-android/browser').run()
