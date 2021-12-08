#!/usr/bin/env python3

import os
import subprocess
import colorama

SOURCE_LOCAL = 'locally checked branches'
SOURCE_REMOTE = 'all remote branches'  # no supported yet


class BranchFilter:
    def __init__(self,
                 custom_branches: [str] = None, # custom list of real branches
                 synthetic_branches: [dict] = None, # custom not existent branches
                 input_provider=lambda: input().lower(),
                 cwd=os.path.abspath('')):
        self.cwd = cwd
        self.provide_input = input_provider
        self.all_branches: list[str] = []
        branches_str = self.capture_output('git branch')

        if custom_branches:
            self.all_branches: list[str] = custom_branches
        elif not synthetic_branches:
            # TODO sorted(key=lambda key: sort_case)
            self.all_branches: list[str] = branches_str.replace('* ', '').replace(' ', '').splitlines()
            self.all_branches = sorted(self.all_branches, reverse=True)

        self.head_commits = {} #map here!

        if synthetic_branches:
            for s in synthetic_branches:
                branch_name = s['name']
                commit_msg = s['commit']
                if not commit_msg:
                    commit_msg = self._get_commit_message(s['ref'])
                self.head_commits[branch_name] = commit_msg
                self.all_branches.append(branch_name)

        self.remaining_branches = list(self.all_branches)

        for branch in self.all_branches:
            if branch in self.head_commits:
                continue
            self.head_commits[branch] = self._get_commit_message(branch+'~0')

        self.selected_branches = []
        self.selection_finished = False

    def _get_commit_message(self, revision: str) -> str:
        try:
            full_commit_log = self.capture_output('git show -s --format=%B $(git rev-parse ' + revision + ')')
            fisrt_return = full_commit_log.index('\n')
            full_commit_log = full_commit_log[0:fisrt_return]
        except:
            full_commit_log = '<BRANCH NOT FOUND>'
            pass
        return full_commit_log

    def extend_selected(self, selected):
        self.selected_branches.extend(selected)

    def find_many(self):
        self.run_flow(
            flow_message=lambda: self.print_remains_and_selected(),
            input_handler=lambda input: self.add_remaining_and_check_input(input),
            finish_criterion=lambda: self.selection_finished
        )

        return self.selected_branches

    def find_one(self):
        self.run_flow(
            flow_message=lambda: self.print_remains_or_selected(),
            input_handler=lambda input: self.find_single_branch(input),
            finish_criterion=lambda: len(self.selected_branches) == 1
        )

        return self.selected_branches[0]

    def run_flow(self, flow_message, input_handler, finish_criterion):
        flow_message()

        input_handler(self.provide_input())

        if finish_criterion():
            return

        self.run_flow(flow_message, input_handler, finish_criterion)

    def add_remaining_and_check_input(self, input):
        for candidate in self.all_branches:
            if input == '':
                continue

            if candidate in self.selected_branches:
                continue
            
            if input not in candidate.lower() and input not in self.head_commits[candidate].lower():
                continue

            self.selected_branches.append(candidate)
            self.remaining_branches.remove(candidate)
        self.selection_finished = input == ''

    def find_single_branch(self, input):
        if len(self.selected_branches) == 0:
            filtered_branches = self.all_branches
        else:
            filtered_branches = self.selected_branches
        self.selected_branches = list(
            filter(lambda branch: input in self.head_commits[branch].lower() or input in branch.lower(),
                   filtered_branches))

    def print_remains_and_selected(self):
        print("\nRemaining:")
        for branch in self.remaining_branches:
            self.print_branch_desc(branch)

        print("\nSelected:")
        print(colorama.Fore.RED)
        for branch in self.selected_branches:
            self.print_branch_desc(branch)
        print(colorama.Fore.RESET)
        print('\nType part of branch name or commit message to keep it or empty line to end selection:')

    def print_remains_or_selected(self):
        if len(self.selected_branches) > 0:
            branches_to_print = self.selected_branches
        else:
            branches_to_print = self.remaining_branches

        for branch in branches_to_print:
            self.print_branch_desc(branch)

        print('\n( found:', len(self.selected_branches), ')')
        print('\nType part of branch name or commit message to keep it or empty line to end search:')

    def print_branch_desc(self, branch):
        branch_with_max_len = max(self.all_branches, key=len)
        padding_str = ''

        for i in range(0, len(branch_with_max_len) - len(branch)):
            padding_str = padding_str + ' '
        print(branch + padding_str + ' | ' + self.head_commits[branch])

    def capture_output(self, cmd):
        return subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)
