#!/usr/bin/env python3
import os
import sys
import cherry_picker
import yaml

CWD = os.path.abspath('')
BASEMENT = 'basement_branch'
CHANGES = 'branches_to_cherry_pick'
OUTPUT = 'output_branch'
LOG_FILE = os.path.abspath(os.path.dirname(__file__)) + '/assembly.log'


def start_flow(config, input_provider):
    log('\n==== Updating branches at: {} ===='.format(CWD))
    affected = []

    for item in config:
        result = cherry_picker.Picker(cwd=CWD,
                                      input_provider=input_provider,
                                      verbose_ouput=False) \
            .run(item[OUTPUT], item[BASEMENT], item[CHANGES])

        if (result):
            affected.append(item[OUTPUT])

    print('All Done! How about to push changes?')
    for branch in affected:
        print('    git push origin '+branch+':'+branch+' --force')
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

        results.append({
            OUTPUT: branch_to_rebuild,
            BASEMENT: basement,
            CHANGES: cherry_picks
        })
        basement = branch_to_rebuild

    return results


def log(msg):
    with open(file=LOG_FILE, mode='a') as log_file:
        print(msg, file=log_file)


def process_config(yaml_config, input_provider = lambda: input().lower()):
    with open(yaml_config, 'r') as config_file:
        try:
            config = yaml.load(config_file)
            start_flow(parse_yaml(config), input_provider)
        except yaml.YAMLError as exc:
            raise Exception(exc)


if __name__ == '__main__':
    sys_args = sys.argv[1:] if len(sys.argv) > 1 else None
    process_config(sys_args[0])
pass
