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


def extract_branches(builder_config) -> [dict]:
    builder = workflow_updater.WorkflowBuilder(builder_config, CWD)
    shadow_branches = []
    for item in builder.config:
        branch = item['output_branch']
        for i, commit_content in enumerate(reversed(item['branch_contents'])):
            intermediate = {
                    'title': '  * shadow/'+branch+'/'+str(i),
                    'name': 'shadow/'+branch+'/'+str(i),
                    'commit':  commit_content.get('commit_message'),
                    'ref': branch+'~'+str(i)
            }
            is_head = i == 0
            if is_head:
                intermediate['title'] = branch
                intermediate['name'] = branch

            shadow_branches.append(intermediate)
    return shadow_branches


def find_shadow_branch(branch: str, backing_branches: [dict]) -> dict:
    for bb in backing_branches:
        if bb['name'] == branch:
            return bb


def prepare_shadow_branch(branch: dict):
    # TODO: could be better
    os.system('cd '+CWD+' && git checkout -b '+branch['name']+' '+branch['ref'])
    pass


def main(args: [str]) -> None:
    builder_branches: [str] = None
    shadow_branches: [dict] = []
    if args and len(args) > 0 and os.path.isfile(args[0]):
        shadow_branches = extract_branches(args[0])

    if args is None:
        branch_filter = BranchFilter(
            custom_branches=None,
            synthetic_branches=shadow_branches
        )
    else:
        arg_queue = Queue()
        for arg in args:
            arg_queue.put(arg)

        branch_filter = BranchFilter(custom_branches=builder_branches,
                                     synthetic_branches=shadow_branches,
                                     input_provider=lambda: mixed_input(arg_queue))

    checkout_branch = branch_filter.find_one()

    shadow_branch = find_shadow_branch(checkout_branch, shadow_branches)
    if shadow_branch:
        prepare_shadow_branch(shadow_branch)
    os.system('git checkout ' + checkout_branch)
    print("With message: '" + branch_filter.head_commits[checkout_branch]+"'")
    pass


if __name__ == '__main__':
    main(sys.argv[1:] if len(sys.argv) > 1 else None)