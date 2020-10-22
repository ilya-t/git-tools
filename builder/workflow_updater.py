#!/usr/bin/env python3
import argparse
import datetime
import os
import subprocess
from operator import itemgetter

import yaml

import cherry_picker

CWD = os.path.abspath('')
BASEMENT = 'basement_branch'
BUILD_STEPS = 'build_steps'
STEP_BRANCHES = 'branches'
STEP_COMMIT = 'commit'
CHANGES = 'branches_to_cherry_pick'
OUTPUT = 'output_branch'
LOG_FILE = os.path.abspath(os.path.dirname(__file__)) + '/assembly.log'


class Builder:
    def __init__(self,
                 config_file,
                 input_provider=lambda: input().lower(),
                 force_update=False,
                 dry_run=False,
                 quiet=False,
                 experimental=False):
        super().__init__()
        self._config_file = config_file
        self._input_provider = input_provider
        self._force_update = force_update
        self._dry_run = dry_run
        self._quiet = quiet
        self._experimental_build = experimental

        if self._experimental_build:
            print('WARNING! EXPERIMENTAL BUILD IS ON!')

    def build(self):
        current_branch = capture_current_branch()

        with open(self._config_file, 'r') as config_file:
            try:
                config = yaml.load(config_file)
                if self._experimental_build:
                    self._build_v2(self._parse_yaml(config))
                else:
                    self._start_flow(parse_yaml(config))
            except yaml.YAMLError as exc:
                raise Exception(exc)

        print('Returning back...')
        os.system('git checkout ' + current_branch)

    def _parse_yaml(self, config):
        parsed_config = []

        for basement in config:
            basement_branch = list(basement.keys())[0]
            basement_config = list(basement.values())[0]

            build_steps = []
            branch_rebuild_configs = extract_rebuild_configs(
                branch_build_config=basement_config,
                basement=basement_branch
            )

            for plain_config in branch_rebuild_configs:
                for commit in plain_config[CHANGES]:
                    build_steps.append({
                        STEP_COMMIT: commit,
                        STEP_BRANCHES: []
                    })

                # case when we want so intoduce new branches somewhere
                build_steps[-1][STEP_BRANCHES].append(plain_config[OUTPUT])

            parsed_config.append({
                BASEMENT: basement_branch,
                BUILD_STEPS: build_steps
            })

        return parsed_config

    def _build_v2(self, config):
        log('\n==== Updating branches at: {} ===='.format(CWD))
        affected = []

        flow_start = datetime.datetime.now()
        cmd_timing = []
        cmd_log = []
        reusing_head = False
        for index, single_basement_config in enumerate(config):
            basement_branch = single_basement_config[BASEMENT]
            build_steps = single_basement_config[BUILD_STEPS]

            picker = cherry_picker.Picker(
                basement_branch=basement_branch,
                cwd=CWD,
                log_file=LOG_FILE,
                input_provider=self._input_provider,
                verbose_ouput=False,
                dry_run=self._dry_run,
                assume_assembled_properly=self._quiet)

            tmp_branch = 'tmp/' + basement_branch

            if not reusing_head:
                picker.tmp_branch_acquire(tmp_branch)

            # when next basement is equal so we can skip unnecessary delete+checkout
            reusing_head = config[index+1][BASEMENT] == basement_branch if index + 1 < len(config) else False

            result = picker.tmp_branch_build(
                tmp_branch,
                steps=lambda picker, tmp_branch: self._cherry_pick_and_create_branches(
                    picker, tmp_branch, build_steps, reusing_head),
            )
            # TODO: support up-to-date check
            # if not self._force_update and picker.up_to_date():
            #     print('Branch "' + picker.target_branch + '" already up-to-date with basement "' +
            #           picker.basement_branch + '"')
            #     continue

            if not result:
                # not supported yet
                # affected.append(single_basement_config[OUTPUT])
                # else:
                print('Building cancelled!')
                return

            if not reusing_head:
                picker.tmp_branch_release(tmp_branch)

            cmd_log.append(basement_branch + ' with ' + str(len(build_steps)) + ' steps:')
            cmd_log.extend(picker.cmd_timing)
            cmd_timing.extend(picker.cmd_timing)
        flow_end = datetime.datetime.now()
        flow_seconds = (flow_end - flow_start).total_seconds()
        seconds = str(round(flow_seconds, 1))
        print('Overall build took: ' + seconds + 's')
        print('Command execution timing: ')
        cmd_timing = sorted(cmd_timing, key=itemgetter(1), reverse=True)
        for timing in cmd_timing:
            print('  '+str(timing[1]) + 's: ' + timing[0])

        print('COMMAND LOG:')
        for l in cmd_log:
            print(l)

        if len(affected) > 0:
            print('All Done! How about to push changes?')

            for branch in affected:
                print('    git push origin ' + branch + ':' + branch + ' --force')

        print('')

    def _cherry_pick_and_create_branches(self, picker, tmp_branch, build_steps, reuse_head):
        last_branch = None
        commits_ahead = 0
        for step in build_steps:
            if not picker.cherry_pick_by_branch(step[STEP_COMMIT], tmp_branch):
                return False
            commits_ahead += 1

            for target_branch in step[STEP_BRANCHES]:
                last_branch = target_branch
                if picker.can_commit_assemble():
                    picker.run_cmd('git branch -D ' + target_branch, log_output=True, print_output=False,
                                   fallback=lambda: None)
                    picker.run_cmd('git branch ' + target_branch + ' ' + tmp_branch + '~0')
                    picker.log('Branch assembled: ' + target_branch + '!')
                else:
                    return False

        if reuse_head:
            picker.run_cmd('git reset --hard HEAD~' + str(commits_ahead))
        else:
            picker.run_cmd('git checkout ' + last_branch)
        return True

    def _start_flow(self, config):
        log('\n==== Updating branches at: {} ===='.format(CWD))
        affected = []

        flow_start = datetime.datetime.now()

        for item in config:
            basement_branch = list(item.keys())[0]
            basement_config = item[basement_branch]

            picker = cherry_picker.Picker(
                target_branch=item[OUTPUT],
                basement_branch=item[BASEMENT],
                branches_to_cherry_pick=item[CHANGES],
                cwd=CWD,
                log_file=LOG_FILE,
                input_provider=self._input_provider,
                verbose_ouput=False,
                dry_run=self._dry_run,
                assume_assembled_properly=self._quiet)

            if not self._force_update and picker.up_to_date():
                print('Branch "' + picker.target_branch + '" already up-to-date with basement "' +
                      picker.basement_branch + '"')
                continue

            result = picker.run()

            if result:
                affected.append(item[OUTPUT])
            else:
                print('Building cancelled!')
                return
        flow_end = datetime.datetime.now()
        flow_seconds = (flow_end - flow_start).total_seconds()
        seconds = str(round(flow_seconds, 1))
        print('Overall build took: ' + seconds + 's')
        if len(affected) > 0:
            print('All Done! How about to push changes?')

            for branch in affected:
                print('    git push origin ' + branch + ':' + branch + ' --force')

        print('')


def parse_yaml(config):
    parsed_config = []

    for basement in config:
        basement_branch = list(basement.keys())[0]
        basement_config = list(basement.values())[0]

        parsed_config.extend(extract_rebuild_configs(
            branch_build_config=basement_config,
            basement=basement_branch)
        )

    return parsed_config


def extract_rebuild_configs(branch_build_config, basement):
    results = []
    for rebuild_config in branch_build_config:
        if '~' in rebuild_config:  # short form without list to commit
            branch_to_rebuild = rebuild_config[:rebuild_config.index('~')]
            cherry_picks = [rebuild_config]
        else:
            branch_to_rebuild = list(rebuild_config.keys())[0]
            cherry_picks = list(rebuild_config.values())[0]

            if not cherry_picks:
                cherry_picks = []

        cherry_picks = list(map(lambda commit_ref: as_long_form(commit_ref, branch_to_rebuild), cherry_picks))

        results.append({
            OUTPUT: branch_to_rebuild,
            BASEMENT: basement,
            CHANGES: cherry_picks
        })
        basement = branch_to_rebuild

    return results


def as_long_form(commit_ref, branch):
    if commit_ref[0] == '~':
        return branch + commit_ref
    else:
        return commit_ref


def log(msg):
    with open(file=LOG_FILE, mode='a') as log_file:
        print(msg, file=log_file)


def capture_current_branch():
    cmd = 'git rev-parse --abbrev-ref HEAD'
    output = subprocess.check_output(cmd, cwd=CWD, universal_newlines=True, shell=True)
    return output.splitlines()[0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts branch building based on yaml config.')
    parser.add_argument(dest='config_file', metavar='CONFIG', type=str,
                        help='path to config that describes how to build branch')
    parser.add_argument('--force', action='store_true',
                        help='ignores branch up-to-date state and forces rebuild')
    parser.add_argument('--dry-run', action='store_true',
                        help='starts building process at temporary branches and does not perform any changes to real branches')
    parser.add_argument('--quiet', action='store_true',
                        help='will not ask questions during building process (except failed chery-picks)')
    parser.add_argument('--experimental', action='store_true',
                        help='enables experimental cherry-picking process that creates less temporary branches!')

    args = parser.parse_args()

    Builder(
        config_file=args.config_file,
        force_update=args.force,
        dry_run=args.dry_run,
        quiet=args.quiet,
        experimental=args.experimental
    ).build()
pass
