from __future__ import print_function

import os
import sys
import yaml
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)+'/../builder'))
import workflow_updater
from queue import Queue

from branch_filter import BranchFilter


def mixed_input(params_queue):
    if params_queue.empty():
        return input().lower()
    item = params_queue.get()
    print(item)
    return item


def extract_branches(builder_config) -> list[str]:
    with open(builder_config, 'r') as config_file:
        try:
            config = yaml.load(config_file)
            parsed_config = workflow_updater.parse_yaml(config)
        except yaml.YAMLError as exc:
            raise Exception(exc)

    return list(map(lambda e: e['output_branch'], parsed_config))


def main(args):
    builder_branches = None
    if args and len(args) > 0 and os.path.isfile(args[0]):
        builder_branches = extract_branches(args[0])

    if args is None:
        branch_filter = BranchFilter(
            custom_branches=builder_branches
        )
    else:
        arg_queue = Queue()
        for arg in args:
            arg_queue.put(arg)

        branch_filter = BranchFilter(custom_branches=builder_branches, input_provider=lambda: mixed_input(arg_queue))

    checkout_branch = branch_filter.find_one()
    os.system('git checkout '+ checkout_branch)
    print("With message: '" + branch_filter.head_commits[checkout_branch]+"'")
    pass


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    main(args)