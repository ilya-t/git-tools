#!/usr/bin/env python3
import os
import sys
import cherry_picker
import yaml

DRY_RUN = False
CWD = os.path.abspath('')
SUPPRESS_PROMPTS_FOR_TESTS = False
BASEMENT = 'basement_branch'
CHANGES = 'branches_to_cherry_pick'
OUTPUT = 'output_branch'
LOG_FILE = os.path.abspath(os.path.dirname(__file__)) + '/assembly.log'


def start_flow(config):
    log('\n==== Updating branches at: {} ===='.format(CWD))

    for item in config:
        cherry_picker.Picker(cwd=CWD,
                             suppress_prompts=SUPPRESS_PROMPTS_FOR_TESTS,
                             verbose_ouput=False)\
            .run(item[OUTPUT], item[BASEMENT], item[CHANGES])


def parse_yaml(config):
    parsed_config = []
    for basement_branch in config.keys():
        basement = basement_branch

        for rebuild_config in config[basement_branch]:
            branch_to_rebuild = list(rebuild_config.keys())[0]
            cherry_picks = list(rebuild_config.values())[0]

            parsed_config.append({
                OUTPUT : branch_to_rebuild,
                BASEMENT : basement,
                CHANGES : cherry_picks
            })
            basement = branch_to_rebuild

    return parsed_config


def log(msg):
    with open(file=LOG_FILE, mode='a') as log_file:
        print(msg, file=log_file)


def parse_args(args):
    with open(args[0], 'r') as config_file:
        try:
            config = yaml.load(config_file)
            start_flow(parse_yaml(config))
        except yaml.YAMLError as exc:
            raise Exception(exc)


if __name__ == '__main__':
    sys_args = sys.argv[1:] if len(sys.argv) > 1 else None

    if DRY_RUN:
        parse_args(['tests/workspace.yml'])
    else:
        parse_args(sys_args)
pass
