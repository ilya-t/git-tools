#!/usr/bin/env python3

# usage:
# python3 git.rebase_onto.py output_branch_name basement_branch file_with_branches_to_cherry_pick
# file_with_branches_to_cherry_pick is file which name is used to assemble branch.
# its contents used to cherry-pick revisions one-by-one
import os
import sys
import subprocess

FALLBACK_BRANCH = 'master'
DRY_RUN = False


class Picker:
    def __init__(self,
                 log_file=os.path.abspath(os.path.dirname(__file__)) + '/assembly.log',
                 input_provider=lambda : input().lower(),
                 cwd=os.path.abspath(''),
                 suppress_prompts=False,
                 verbose_ouput=True):
        self.input_provider = input_provider
        self.log_file = log_file
        self.cwd = cwd

        if suppress_prompts:
            self.input_provider = lambda : 'yes'
        self.verbose = verbose_ouput

    def run(self, target_branch, basement_branch='origin/master', branches_to_cherry_pick=[]):
        if self.upToDate(target_branch, basement_branch, branches_to_cherry_pick):
            print('Branch "'+target_branch+'" already up-to-date with basement "'+basement_branch+'"')
            return False

        tmp_branch = 'tmp/' + target_branch
        self.run_cmd('git checkout ' + basement_branch, print_output=False)
        self.run_cmd('git branch -d ' + tmp_branch, print_output=False, fallback=lambda: None)

        print('Building at: ' + tmp_branch + ' (based on ' + basement_branch + ')')
        print('=========================================')
        self.print('Branches to cherry-pick: ' + branches_to_cherry_pick.__str__())
        self.run_cmd('git checkout -b ' + tmp_branch + ' ' + basement_branch)

        cherry_picks = 0

        for line in branches_to_cherry_pick:
            self.cherry_pick_by_branch(line, tmp_branch)
            cherry_picks += 1

        print('=========================================')
        print('Assembling complete. Take a look: ')
        # os.system to show pretty output about commits
        self.run_simple_cmd('git log --oneline -' + str(cherry_picks + 1))
        print('=========================================')

        if self.query_yes_no('Is branch assembled properly?') == 'yes':
            self.run_cmd('git branch -D ' + target_branch, log_output=True, print_output=False)
            self.run_cmd('git checkout -b ' + target_branch)
            self.run_cmd('git branch -D ' + tmp_branch, print_output=False)
            self.log('Branch rebased: ' + target_branch + ' (on top of ' + basement_branch + ')')
            self.log('=========================================')
            print('Done! You are now on: ' + target_branch + ' (on top of ' + basement_branch + ')\n')
            return True
        else:
            self.print('Cleaning temporary branch: ' + tmp_branch)
            self.run_cmd('git checkout ' + FALLBACK_BRANCH + ' && git br -D ' + tmp_branch)
            self.print('Done!')
            return True

    def upToDate(self, target_branch, basement_branch, branches_to_cherry_pick):
        current_basement = target_branch + '~'+ (len(branches_to_cherry_pick)).__str__()

        current_hash = self.capture_output('git rev-parse ' + current_basement)
        new_hash = self.capture_output('git rev-parse ' + basement_branch)

        return current_hash == new_hash

    def capture_output(self, cmd):
        return subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)

    def cherry_pick_by_branch(self, branch, tmp_branch):
        print('Cherry-picking current ' + branch)
        # printing commit message
        self.run_cmd('git show -s --format=%B $(git rev-parse ' + branch + ')')
        self.run_cmd('git cherry-pick $(git rev-parse ' + branch + ')',
                     fallback=lambda: self.try_continue_cherry_pick(tmp_branch),
                     print_output=self.verbose)

    def run_cmd(self, command, fallback=None, log_output=False, print_output=True):
        if DRY_RUN:
            self.print('cmd: ' + command)
            return

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
                    self.print(line)

            if log_output:
                for line in output:
                    self.log(line)

        if result != 0:
            if fallback is None:
                raise Exception('shell command failed: ' + command + '\n with: ' + error.__str__())
            else:
                fallback()

    def try_continue_cherry_pick(self, tmp_branch):
        abort_cherry_pick = 'git cherry-pick --abort && git checkout ' + FALLBACK_BRANCH + ' && git br -D ' + tmp_branch

        if self.query_yes_no(
                'Cherry pick failed! Resolve conflicts as usual and finish cherry pick by `git cherry-pick --continue`. Ready?') == 'yes':
            return
        else:
            self.run_cmd(abort_cherry_pick)

    def run_simple_cmd(self, cmd):
        os.system('cd ' + self.cwd + ' && ' + cmd)

    def query_yes_no(self, question, default='yes'):
        '''Ask a yes/no question via raw_input() and return their answer.

        'question' is a string that is presented to the user.
        'default' is the presumed answer if the user just hits <Enter>.
            It must be 'yes' (the default), 'no' or None (meaning
            an answer is required of the user).

        The 'answer' return value is one of 'yes' or 'no'.
        '''
        valid = {'yes': 'yes', 'y': 'yes', 'ye': 'yes',
                 'no': 'no', 'n': 'no'}
        if default is None:
            prompt = ' [y/n] '
        elif default == 'yes':
            prompt = ' [Y/n] '
        elif default == 'no':
            prompt = ' [y/N] '
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while 1:
            sys.stdout.write(question + prompt)
            choice = self.input_provider()
            if default is not None and choice == '':
                return default
            elif choice in valid.keys():
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' " \
                                 "(or 'y' or 'n').\n")

    def print(self, line):
        if self.verbose:
            print(line)

    def log(self, line):
        with open(self.log_file, mode='a') as log_file:
            print(line, file = log_file)



def parse_args(args):
    target_branch = args[0]
    basement_branch = args[1]
    branches_to_cherry_pick = args[2:len(args)]

    Picker().run(target_branch, basement_branch, branches_to_cherry_pick)


if __name__ == '__main__':
    sys_args = sys.argv[1:] if len(sys.argv) > 1 else None
    if DRY_RUN and sys_args is None:
        parse_args(['test_branch', 'origin/master', 'branch_to_cherry_pick~1', 'branch_to_cherry_pick'])
    else:
        parse_args(sys_args)
pass
