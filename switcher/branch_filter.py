#!/usr/bin/env python3

import os
import sys
import subprocess

class BranchFilter:
    def __init__(self,
                 cwd=os.path.abspath('')):
        self.cwd = cwd
        branches_str = self.capture_output('git branch')
        self.all_branches = branches_str.replace('* ', '').replace(' ', '').splitlines()
        self.remaining_branches = list(self.all_branches)
        self.head_commits = {}
        self.selected_branches = []
        self.selection_finished = False

        for branch in self.all_branches:
            full_commit_log = self.capture_output('git show -s --format=%B $(git rev-parse ' + branch + '~0)')
            fisrt_return = full_commit_log.index('\n')
            self.head_commits[branch] = full_commit_log[0:fisrt_return]

    def find_many(self):
        self.run_flow(
            flow_message = lambda: self.print_remains_and_selected(),
            input_handler = lambda input: self.add_remaining_and_check_input(input),
            finish_criterion = lambda: self.selection_finished
        )
        
        return self.selected_branches, self.remaining_branches

    def run_flow(self, flow_message, input_handler, finish_criterion):
        flow_message()

        input_handler(input().lower())

        if finish_criterion():
            return
        
        self.run_flow(flow_message, input_handler, finish_criterion)

    def add_remaining_and_check_input(self, input):
        for branch in self.all_branches:
            self.add_remaining_branch(branch, input)
        self.selection_finished = input == ''


    def find_one(self):
        self.run_flow(
            flow_message = lambda: self.print_remains_or_selected(),
            input_handler = lambda input: self.find_single_branch(input),
            finish_criterion = lambda: len(self.selected_branches) == 1
        )
        
        return self.selected_branches[0]

    def find_single_branch(self, input):
        if len(self.selected_branches) == 0:
            filtered_branches = self.all_branches
        else:
            filtered_branches = self.selected_branches
        self.selected_branches = list(filter(lambda branch: input in self.head_commits[branch].lower() , filtered_branches))

    def add_remaining_branch(self, candidate, input):
        if input == '':
            return

        if input not in self.head_commits[candidate].lower():
            return
        
        if candidate in self.selected_branches:
            return
        
        self.selected_branches.append(candidate)
        self.remaining_branches.remove(candidate)

    def print_remains_and_selected(self):
        print("\nRemaining:")
        for branch in self.remaining_branches:
            self.print_branch_desc(branch)

        print("\nSelected:")
        for branch in self.selected_branches:
            self.print_branch_desc(branch)
        print('\nType part of branch name or commit message to keep it or empty line to end selection:')

    def print_remains_or_selected(self):
        if len(self.selected_branches) > 0:
            branches_to_print = self.selected_branches
        else:
            branches_to_print = self.remaining_branches

        for branch in branches_to_print:
            self.print_branch_desc(branch)

        print('\nType part of branch name or commit message to keep it or empty line to end search:')



    def print_branch_desc(self, branch):
        branch_with_max_len = max(self.all_branches, key=len)
        padding_str = ''

        for i in range(0, len(branch_with_max_len) - len(branch)):
            padding_str = padding_str + ' '
        print(branch + padding_str + ' | ' +self.head_commits[branch])


    def capture_output(self, cmd):
        return subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)


if __name__ == '__main__':
    
pass
