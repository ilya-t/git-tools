#!/usr/bin/env python3
import argparse
import datetime
import os
import subprocess

import yaml

import cherry_picker

CWD = os.path.abspath('')
BASEMENT = 'basement_branch'
CHANGES = 'branches_to_cherry_pick'
OUTPUT = 'output_branch'
LOG_FILE = os.path.abspath(os.path.dirname(__file__)) + '/assembly.log'


def start_flow(config, input_provider, force_update = False, dry_run = False, quiet = False):
    log('\n==== Updating branches at: {} ===='.format(CWD))
    affected = []

    flow_start = datetime.datetime.now()

    for item in config:
        picker = cherry_picker.Picker(target_branch=item[OUTPUT], basement_branch=item[BASEMENT],
                                      branches_to_cherry_pick=item[CHANGES], cwd=CWD, log_file=LOG_FILE,
                                      input_provider=input_provider, verbose_ouput=False, dry_run=dry_run,
                                      assume_assembled_properly=quiet)

        if not force_update and picker.up_to_date():
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
    print('Overall build took: '+seconds+'s')
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
            config=basement_config,
            basement=basement_branch)
        )

    return parsed_config


def extract_rebuild_configs(config, basement):
    """Return the absolute version of a path."""
    results = []
    for rebuild_config in config:
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
        return branch+commit_ref
    else:
        return commit_ref


def log(msg):
    with open(file=LOG_FILE, mode='a') as log_file:
        print(msg, file=log_file)


def process_config(yaml_config,
                   input_provider=lambda: input().lower(),
                   force_update = False,
                   dry_run = False,
                   quiet = False):
    current_branch = capture_current_branch()

    with open(yaml_config, 'r') as config_file:
        try:
            config = yaml.load(config_file)
            start_flow(parse_yaml(config), input_provider, force_update, dry_run, quiet)
        except yaml.YAMLError as exc:
            raise Exception(exc)

    print('Returning back...')
    os.system('git checkout '+current_branch)


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

    args = parser.parse_args()

    process_config(args.config_file, force_update = args.force, dry_run = args.dry_run, quiet=args.quiet)
pass
