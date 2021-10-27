from __future__ import print_function

import os
import sys
import workflow_updater
from queue import Queue
from branch_filter import BranchFilter

CWD = os.path.abspath('')

def mixed_input(params_queue):
    if params_queue.empty():
        return input().lower()
    item = params_queue.get()
    print(item)
    return item


def extract_branches(builder_config) -> (list[str], dict[str, str]):
    builder = workflow_updater.WorkflowBuilder(builder_config, CWD)
    config_branches = list(map(lambda e: e[workflow_updater.OUTPUT], builder.config))

    backing_branches = []
    for item in builder.config:
        branch = item['output_branch']
        for i, commit_content in enumerate(reversed(item['branch_contents'])):
            backing_branches.append({
                'name': branch+'/shadow/'+str(i),
                'commit':  commit_content.get('commit_message')
            })
    return config_branches, backing_branches


def main(args: [str]) -> None:
    builder_branches = None
    backing_branches = None
    if args and len(args) > 0 and os.path.isfile(args[0]):
        builder_branches, backing_branches = extract_branches(args[0])

    if args is None:
        branch_filter = BranchFilter(
            custom_branches=builder_branches,
            synthetic_branches=backing_branches
        )
    else:
        arg_queue = Queue()
        for arg in args:
            arg_queue.put(arg)

        branch_filter = BranchFilter(custom_branches=builder_branches,
                                     synthetic_branches=backing_branches,
                                     input_provider=lambda: mixed_input(arg_queue))

    checkout_branch = branch_filter.find_one()
    os.system('git checkout '+ checkout_branch)
    print("With message: '" + branch_filter.head_commits[checkout_branch]+"'")
    pass


if __name__ == '__main__':
    main(sys.argv[1:] if len(sys.argv) > 1 else None)