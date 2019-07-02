#!/usr/bin/env python3
import os
import subprocess
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)+'/../switcher'))
import branch_filter

class Cleaner:

    def __init__(self,
                 log_file=os.path.dirname(__file__) + '/delete.log',
                 cwd=os.path.abspath(''),
                 upstream='origin/master',
                 suppress_prompt=False,
                 input_provider=lambda : input().lower(),
                 ):
        self.log_file = log_file
        self.cwd = find_dot_git(cwd)
        self.upstream = upstream
        self.suppress_prompt = suppress_prompt
        self.input_provider = input_provider

    def run(self):
        self.current_branch = self.capture_output('git rev-parse --abbrev-ref HEAD').splitlines()[0]
        self.all_branches = self.capture_output('git branch').replace('* ', '').replace(' ', '').splitlines()
        self.merged_branches = list(filter(self.is_merged, self.all_branches))

        if len(self.merged_branches) == 0:
            print('There are no local branches that were merged to upstream('+self.upstream+')!')
        else:
            print('Found '+str(len(self.merged_branches))+' branches that were merged to upstream('+self.upstream+')!')

        bfilter = branch_filter.BranchFilter(cwd=self.cwd, input_provider=self.input_provider)
        bfilter.extend_selected(self.merged_branches)
        self.merged_branches = bfilter.find_many()

        print('\nDeleting:')
        for merged in self.merged_branches:
            if merged != self.current_branch:
                self.git_branch_minus_D(merged)

    def is_merged(self, branch):
        return self.capture_output('git log '+branch+' --not '+self.upstream) == ''

    def capture_output(self, cmd):
        return subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)

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

    if len(sys.argv) > 2:
        Cleaner(cwd=args[0], upstream=args[1]).run()
    elif len(sys.argv) > 1:
        Cleaner(cwd=args[0]).run()
    else:
        Cleaner(cwd='.').run()
