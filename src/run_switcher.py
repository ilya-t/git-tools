from __future__ import print_function

import os
import subprocess
import sys
import workflow_updater
from branch_filter import BranchFilter

execution_location_path = os.path.abspath('')
DRY_RUN = False


class Switcher:
    def __init__(self,
                 dry_run: bool,
                 initial_input: str,
                 workflow_config: str,
                 input_provider=lambda: input().lower(),
                 cwd: str = execution_location_path,
                 ) -> None:
        super().__init__()
        self._cwd = cwd
        self._dry_run = dry_run
        self._initial_input = initial_input
        self._input_provider = input_provider
        self._current_branch = self._get_current_branch()
        # soft reset is disabled cause it will generate longer checkouts
        # under heavy repositories.
        self._soft_reset_after_checkout = False

        if workflow_config and os.path.exists(workflow_config):
            self._builder = workflow_updater.WorkflowBuilder(
                yaml_config=workflow_config,
                cwd=cwd,
                dry_run=dry_run,
                quiet=True,
            )
        else:
            self._builder = None

    def execute(self):
        builder_branches = self._extract_branches()
        if self._initial_input and self._initial_input in builder_branches:
            # we already got exact match!
            checkout_branch = self._initial_input
            print(f'-> Checkout target "{checkout_branch}"')
        else:
            branch_filter = BranchFilter(
                custom_branches=builder_branches,
                initial_input=self._initial_input,
                input_provider=self._input_provider,
                cwd=self._cwd,
            )
            checkout_branch = branch_filter.find_one()
            print(f'-> Checkout target "{checkout_branch}" with message: "{branch_filter.head_commits[checkout_branch]}"')
        if self._current_branch == checkout_branch:
            print('Already there. Skipping checkout!')
            return
        print('-> Checking diff')
        diff = self._capture_output('git diff HEAD')
        if len(diff) > 0:
            branch_config = self._resolve_head_branch_config_item(self._current_branch)
            expected_message = self._resolve_head_message(branch_config)
            self._commit(
                message=expected_message,
                amend=self._should_amend(branch_config)
            )
        else:
            print('-> No uncommited diff. Skipping')

        self._checkout(checkout_branch)
        self._try_soft_reset()

        print('-> Done!')

    def _extract_branches(self) -> list[str]:
        if not self._builder:
            return []
        builder_config = self._builder.config
        output_branches = map(lambda e: e['output_branch'], builder_config)
        return list(filter(lambda b: b != self._current_branch, output_branches)) # maybe keep current branch but change its message or mark it somehow?

    def _get_current_branch(self) -> str:
        return self._capture_output('git branch --show-current').removesuffix('\n')

    def _capture_output(self, cmd: str, fallback=None) -> str:
        try:
            return subprocess.check_output(cmd, cwd=self._cwd, universal_newlines=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(e.output)
            if fallback:
                return fallback()
            else:
                raise e

    def _set_hooks_enabled(self, enabled: bool) -> None:
        git_dir = self._cwd
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
        self._capture_output(f'chmod {executable} {git_dir}/.git/hooks/*-commit')

    def _commit(self, message: str, amend: bool):
        print('-> Disabling hooks')
        self._set_hooks_enabled(False)

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
                message = message.replace(' ', '\ ')
                print(self._capture_output(f'git commit --no-verify  --all --message "{message}" {amend_arg}'))
        except Exception as e:
            commit_exception = e

        print('-> Enabling hooks')
        self._set_hooks_enabled(True)


        if commit_exception:
            raise commit_exception

    def _checkout(self, branch: str):
        if self._builder:
            affected = workflow_updater.filter_affected(branch=self._current_branch, config=self._builder.config)
            if len(affected) > 0:
                update_list = list(map(lambda e: e['output_branch'], affected))
                print(f'-> Going to update dependent branches: {update_list}')
                self._builder.process_items(affected)
        print('-> Checking out')
        if not DRY_RUN:
            print(self._capture_output('git checkout '+branch))

    def _try_soft_reset(self):
        if not self._soft_reset_after_checkout:
            return
        if not self._builder:
            return
        dst = f'HEAD~1'
        print(f'-> Soft reset to {dst}')

        if not DRY_RUN:
            print(self._capture_output(f'git reset --soft {dst}'))
        print('Done!')

    def _resolve_head_message(self, branch_config_item: {}) -> str:
        if not branch_config_item:
            return None
        branch_contents = branch_config_item.get('branch_contents', [])
        if len(branch_contents) == 0:
            return None
        return branch_contents[-1].get('commit_message', None)

    def _resolve_head_branch_config_item(self, current_branch: str) -> {}:
        if not self._builder:
            return None
        builder_config: [{}] = self._builder.config
        for item in builder_config:
            if item['output_branch'] == current_branch:
                return item

        return None

    def _should_amend(self, branch_config: {}) -> bool:
        if not branch_config:
            return False

        basement_branch = branch_config['basement_branch']
        basement_head = self._capture_output(f'git rev-parse {basement_branch}~0')
        current_head = self._capture_output('git rev-parse HEAD~0')

        return current_head != basement_head


def main(args):
    if DRY_RUN:
        print('<<<DRY-RUN>>>')

    if args and len(args) > 0 and os.path.isfile(args[0]):
        workflow_config = args[0]
        args = args[1:]
    else:
        workflow_config = None

    initial_input = ' '.join(args)
    switcher = Switcher(
        dry_run=DRY_RUN,
        initial_input=initial_input,
        workflow_config=workflow_config,
    )
    switcher.execute()


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    main(args)