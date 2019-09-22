#!/usr/bin/env python3

# usage:
# python3 git.rebase_onto.py output_branch_name basement_branch file_with_branches_to_cherry_pick
# file_with_branches_to_cherry_pick is file which name is used to assemble branch.
# its contents used to cherry-pick revisions one-by-one
import datetime
import os
import sys
import subprocess

FALLBACK_BRANCH = 'master'


def always_confirm():
    return 'yes'


class Picker:
    def __init__(self,
                 target_branch=None,
                 basement_branch='origin/master',
                 branches_to_cherry_pick=[],
                 log_file=os.path.abspath(os.path.dirname(__file__)) + '/assembly.log',
                 input_provider=lambda: input().lower(),
                 cwd=os.path.abspath(''),
                 verbose_ouput=True,
                 dry_run=False,
                 assume_assembled_properly=False):
        self.target_branch = target_branch
        self.basement_branch = basement_branch
        self.branches_to_cherry_pick = branches_to_cherry_pick
        self.input_provider = input_provider
        self.log_file = log_file
        self.cwd = cwd
        self.dry_run = dry_run
        self.assume_assembled_properly = assume_assembled_properly
        self.verbose = verbose_ouput
        self.cmd_timing = []

    def run(self):
        if not self.target_branch:
            raise Exception('Target branch unspecified!')
        tmp_branch = 'tmp/' + self.target_branch

        self.tmp_branch_acquire(tmp_branch)

        if self.tmp_branch_build(tmp_branch, self._default_cherry_pick):
            self.tmp_branch_release(tmp_branch)
            return True
        else:
            return False

    def tmp_branch_build(self, tmp_branch, steps):
        if steps(self, tmp_branch):
            return True
        else:
            self._mission_abort(tmp_branch)
            return False

    def tmp_branch_release(self, tmp_branch):
        self.run_cmd('git branch -D ' + tmp_branch, print_output=False)

    def tmp_branch_acquire(self, tmp_branch):
        self.run_cmd('git checkout ' + self.basement_branch, print_output=False)
        self.run_cmd('git branch -D ' + tmp_branch, print_output=False, log_output=True, fallback=lambda: None)
        print('Building at: ' + tmp_branch + ' (based on ' + self.basement_branch + ')')
        print('=========================================')
        self.print('Branches to cherry-pick: ' + str(self.branches_to_cherry_pick))
        self.run_cmd('git checkout -b ' + tmp_branch + ' ' + self.basement_branch)

    def _default_cherry_pick(self, _, tmp_branch):
        cherry_picks = 0

        for line in self.branches_to_cherry_pick:
            if not self.cherry_pick_by_branch(line, tmp_branch):
                return False
            cherry_picks += 1
        print('=========================================')
        print('Assembling complete. Take a look: ')
        # os.system to show pretty output about commits
        self.run_simple_cmd('git --no-pager log --oneline -' + str(cherry_picks + 1))
        print('=========================================')
        if self.can_commit_assemble():
            self.run_cmd('git branch -D ' + self.target_branch, log_output=True, print_output=False, fallback=lambda: None)
            self.run_cmd('git checkout -b ' + self.target_branch)
            self.log('Branch assembled: ' + self.target_branch + ' (on top of ' + self.basement_branch + ')')
            self.log('=========================================')
            print('Done! You are now on: ' + self.target_branch + ' (on top of ' + self.basement_branch + ')\n')
            return True
        else:
            return False

    def _mission_abort(self, tmp_branch):
        print('Cleaning temporary branch: ' + tmp_branch)
        self.run_cmd('git checkout ' + FALLBACK_BRANCH + ' && git br -D ' + tmp_branch)
        self.print('Done!')

    def can_commit_assemble(self):
        if self.dry_run:
            return False

        if self.assume_assembled_properly:
            return True
        return self.query_yes_no('Is branch assembled properly?') == 'yes'

    # def up_to_date(self, target_branch, commits_to_basement, basement_branch):
    #     pass

    def up_to_date(self):
        if not self.target_branch:
            raise Exception('Target branch unspecified!')

        cherry_picks_count = len(self.branches_to_cherry_pick)
        current_basement = self.target_branch + '~' + str(cherry_picks_count)

        commit_count = int(self.capture_output('git rev-list --count ' + self.target_branch, fallback=lambda: '-1'))

        if commit_count == -1: # branch not exists so it needs to be updated
            return False

        if commit_count < cherry_picks_count: # branch has less commits than expected
            return False

        current_hash = self.capture_output('git rev-parse ' + current_basement)
        new_hash = self.capture_output('git rev-parse ' + self.basement_branch)

        return current_hash == new_hash # current branch head is not ahead

    def capture_output(self, cmd, fallback=None):
        try:
            return subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(e.output)
            if not fallback:
                raise e
            else:
                return fallback()
    pass

    def cherry_pick_by_branch(self, commit, tmp_branch):
        print('Cherry-picking current ' + commit)
        # printing commit message
        # TODO(add revision check)
        self.run_cmd('git show -s --format=%B $(git rev-parse ' + commit + ')')

        retcode = self.run_cmd('git cherry-pick $(git rev-parse ' + commit + ')',
                               fallback=lambda: self.try_continue_cherry_pick(tmp_branch),
                               print_output=self.verbose)
        return retcode == 0

    def run_cmd(self, command, fallback=None, log_output=False, print_output=True):
        with subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              cwd=self.cwd) as p:
            flow_start = datetime.datetime.now()
            result = p.wait()
            self._record_execution_time(flow_start, command)
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
                raise Exception('shell command "' + command + '" failed:\n' +
                                ''.join(error) if isinstance(error, list) else str(error))
            else:
                return fallback()
        else:
            return result

    def try_continue_cherry_pick(self, tmp_branch):
        abort_cherry_pick = 'git cherry-pick --abort'

        if self.query_yes_no(
                'Cherry pick failed! Resolve conflicts as usual and finish cherry pick by `git cherry-pick --continue`. Ready?') == 'yes':
            return 0
        else:
            print('Rolling back cherry-pick process!')
            self.run_cmd(abort_cherry_pick)
            print('Done! You are now on: ' + FALLBACK_BRANCH)
            return -1

    def run_simple_cmd(self, cmd):
        flow_start = datetime.datetime.now()
        os.system('cd ' + self.cwd + ' && ' + cmd)
        self._record_execution_time(flow_start, cmd)

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
            print(line, file=log_file)

    def _record_execution_time(self, time_start, cmd):
        flow_seconds = (datetime.datetime.now() - time_start).total_seconds()
        seconds = round(flow_seconds, 1)
        self.cmd_timing.append([cmd, seconds])


def parse_args(args):
    target_branch = args[0]
    basement_branch = args[1]
    branches_to_cherry_pick = args[2:len(args)]

    Picker(target_branch, basement_branch, branches_to_cherry_pick)\
        .run()


if __name__ == '__main__':
    sys_args = sys.argv[1:] if len(sys.argv) > 1 else None
    parse_args(sys_args)
pass
