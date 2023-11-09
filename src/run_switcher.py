from __future__ import print_function

import os
import subprocess
import sys
import workflow_updater
import yaml
from branch_filter import BranchFilter
from queue import Queue

execution_location_path = os.path.abspath('')
DRY_RUN=False

def mixed_input(params_queue):
    if params_queue.empty():
        return input().lower()
    item = params_queue.get()
    return item


def extract_branches(builder_config) -> list[str]:
    return list(map(lambda e: e['output_branch'], builder_config))


def capture_output(cmd: str, fallback=None) -> str:
    try:
        return subprocess.check_output(cmd, cwd=execution_location_path, universal_newlines=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        if fallback:
            return fallback()
        else:
            raise e
pass


def set_hooks_enabled(enabled: bool) -> None:
    git_dir = execution_location_path
    while not os.path.exists(git_dir+'/.git'):
        parent = os.path.dirname(git_dir)
        if parent == git_dir:
            break
        git_dir = parent

    if not os.path.exists(git_dir+'/.git'):
        print('Failed to find git dir at ', execution_location_path)
    if enabled:
        executable = '+x'
    else:
        executable = '-x'
    capture_output(f'chmod {executable} {git_dir}/.git/hooks/*-commit')


def commit(message: str, amend: bool):
    print('-> Disabling hooks')
    set_hooks_enabled(False)

    spec = ''
    amend_arg = ''
    if amend:
        spec = '(to existing commit)'
        amend_arg = '--amend'
    if not message:
        message = 'WORK IN PROGRESS'
    print(f'-> Commiting with message: "{message}" {spec}')
    commit_exception = None
    try:
        if not DRY_RUN:
            print(capture_output(f'git commit --no-verify  --all --message "{message}" {amend_arg}'))
    except Exception as e:
        commit_exception = e

    print('-> Enabling hooks')
    set_hooks_enabled(True)
        

    if commit_exception:
        raise commit_exception
    pass


def checkout(branch):
    print('-> Checking out')
    if not DRY_RUN:
        print(capture_output('git checkout '+branch))
    pass


def soft_reset(depth: int):
    if depth <= 0:
        return
    dst = f'HEAD~{depth}'
    print(f'-> Soft reset to {dst}')

    if not DRY_RUN:
        print(capture_output(f'git reset --soft {dst}'))
    print('Done! Your head is at:')
    print(capture_output(f'git log -1'))
    pass


def get_current_branch() -> str:
    return capture_output('git branch --show-current').removesuffix('\n')


def resolve_head_message(branch_config_item: {}) -> str:
    branch_contents = branch_config_item.get('branch_contents', [])
    if len(branch_contents) == 0:
        return None
    return branch_contents[-1].get('commit_message', None)

def resolve_head_branch_config_item(current_branch: str, builder_config: [{}]) -> str:
    for item in builder_config:
        if item['output_branch'] == current_branch:
            return item

    return None


def should_amend(branch_config: {}) -> bool:
    if not branch_config:
        return False

    basement_branch = branch_config['basement_branch']
    basement_head = capture_output(f'git rev-parse {basement_branch}~0')
    current_head = capture_output('git rev-parse HEAD~0')

    return current_head != basement_head


def main(args):
    builder_branches = None
    builder_config = None

    if DRY_RUN:
        print('<<<DRY-RUN>>>')

    if args and len(args) > 0 and os.path.isfile(args[0]):
        builder = workflow_updater.WorkflowBuilder(
            yaml_config=args[0], 
            cwd=execution_location_path,
            dry_run=True,
        )
        builder_config = builder.config
        builder_branches = extract_branches(builder_config)
        args = args[1:]

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
    current_branch = get_current_branch()

    print(f'-> Checkout target "{checkout_branch}" with message: "{branch_filter.head_commits[checkout_branch]}"')
    if current_branch == checkout_branch:
        print('Already there. Skipping checkout!')
        return
    print('-> Checking diff')
    diff = capture_output('git diff HEAD')
    if len(diff) > 0:
        branch_config = resolve_head_branch_config_item(current_branch, builder_config)
        expected_message=resolve_head_message(branch_config)
        commit(
            message=expected_message,
            amend=should_amend(branch_config)
        )
    else:
        print('-> No uncommited diff. Skipping')

    checkout(checkout_branch)
    if len(args) > 1:
        depth = int(args[1])
        soft_reset(depth)

    print('-> Done!')


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    main(args)