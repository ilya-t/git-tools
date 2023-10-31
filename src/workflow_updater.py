#!/usr/bin/env python3
import argparse
import datetime
import os
import subprocess
import yaml
import cherry_picker
from typing import Callable

CWD = os.path.abspath('')
BASEMENT = 'basement_branch'
BRANCH_CONTENTS = 'branch_contents'
OUTPUT = 'output_branch'
LOG_FILE = os.path.abspath(os.path.dirname(__file__)) + '/assembly.log'

BR_CONTENT_COMMIT = cherry_picker.CONTENT_COMMIT
BR_CONTENT_MSG = cherry_picker.CONTENT_MESSAGE

CONFIG_BRANCH_CONTENT_COMMIT = 'commit'
CONFIG_BRANCH_CONTENT_MESSAGE = 'message'


def load_yaml(yaml_config:str) -> dict:
    with open(yaml_config, 'r') as config_file:
        try:
            return yaml.load(config_file, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            raise Exception(exc)


class WorkflowBuilder:
    def __init__(self,
                 yaml_config: str,
                 cwd: str,
                 input_provider: Callable[[], str] = lambda: input().lower(),
                 force_update: bool = False,
                 dry_run: bool = False,
                 quiet: bool = False,
                 log_file = LOG_FILE) -> None:
        super().__init__()
        self.yaml_config = yaml_config
        self.input_provider = input_provider
        self.force_update = force_update
        self.dry_run = dry_run
        self.quiet = quiet
        self.cwd = cwd
        self.log_file = log_file
        self.config = self.parse_yaml(load_yaml(yaml_config))

    def start_flow(self):
        if self.has_uncommited_changes():
            if not self.try_commit_changes():
                print('Please commit or stash changes before building!')
                return
        self.log('\n==== Updating branches at: {} ===='.format(self.cwd))
        affected = []

        flow_start = datetime.datetime.now()

        for item in self.config:
            target_branch: str = item[OUTPUT]
            basement_branch: str = item[BASEMENT]
            contents: [object] = item[BRANCH_CONTENTS]
            picker = cherry_picker.Picker(target_branch=target_branch, basement_branch=basement_branch,
                                          branch_contents=contents, cwd=self.cwd, log_file=self.log_file,
                                          input_provider=self.input_provider, verbose_ouput=not self.quiet, dry_run=self.dry_run,
                                          assume_assembled_properly=self.quiet, fallback_branch=basement_branch)

            if not self.force_update and picker.up_to_date():
                print('Branch "' + picker.target_branch + '" already up-to-date with basement "' +
                      picker.basement_branch + '"')
                continue

            result = picker.run()

            if result:
                affected.append(target_branch)
            else:
                print('Building cancelled!')
                return
        flow_end = datetime.datetime.now()
        flow_seconds = (flow_end - flow_start).total_seconds()
        seconds = str(round(flow_seconds, 1))
        print('Overall build took: ' + seconds + 's')
        self.log('\nAffected branches: ' + ','.join(affected))

        if len(affected) > 0:
            print('All Done! How about to push changes?')

            for branch in affected:
                print('    git push origin ' + branch + ':' + branch + ' --force')

        print('')

    def has_uncommited_changes(self) -> bool:
        output = subprocess.check_output('git status --short --untracked-files=no', cwd=self.cwd, universal_newlines=True, shell=True)
        return output.replace('\n', '') != ''

    def parse_yaml(self, config: dict) -> [dict]:
        parsed_config = []
        for node in config:
            if not isinstance(node, dict):
                raise Exception("Wrong root node format!")

            if len(node.keys()) == 1: # short form
                basement_branch: str = list(node.keys())[0]
                basement_config: [] = list(node.values())[0]
            else:
                basement_branch: str = node['basement']
                basement_config = node['branches']
                repo = node.get('repo', None)

                if repo not in self.cwd:
                    continue

            parsed_config.extend(self.extract_rebuild_configs(
                raw_config=basement_config,
                basement=basement_branch)
            )
        return parsed_config

    def extract_rebuild_configs(self, raw_config, basement) -> [dict]:
        """Return the absolute version of a path."""
        results = []
        for config_node in raw_config:
            branch_contents = []
            if isinstance(config_node, str):  # short form without list to commit
                if '~' in config_node:
                    branch_to_rebuild = config_node[:config_node.index('~')]
                    branch_contents.append({
                        BR_CONTENT_COMMIT: config_node,
                        BR_CONTENT_MSG: None
                    })
                else:
                    raise Exception('Expecting format "branchName~0" instead got "', config_node, '"')
            elif isinstance(config_node, dict):
                branch_contents = []
                branch_to_rebuild = list(config_node.keys())[0]
                raw_contents = config_node[branch_to_rebuild]
                if not raw_contents:
                    raw_contents = []
                for raw_content in raw_contents:
                    if isinstance(raw_content, str):  # short of branch content: 'some_branch~1`
                        branch_contents.append({
                            BR_CONTENT_COMMIT: raw_content,
                            BR_CONTENT_MSG: None
                        })
                    elif isinstance(raw_content, dict):  # long form
                        message = raw_content.get(CONFIG_BRANCH_CONTENT_MESSAGE, None)
                        commit = raw_content.get(CONFIG_BRANCH_CONTENT_COMMIT, None)

                        if not message and not commit:
                            raise Exception('Wrong rebuild config! Specify either "message" or "commit"!', raw_content, '"')
                        branch_contents.append({
                            BR_CONTENT_COMMIT: commit,
                            BR_CONTENT_MSG: message
                        })
            else:
                raise Exception('Unknown rebuild branch format"', config_node, '"')

            for i, c in enumerate(reversed(branch_contents)):
                commit : str = c.get(BR_CONTENT_COMMIT, None)
                if not commit: # only message specified, trying to resolve commit automatically
                    commit = '~' + str(i)
                c[BR_CONTENT_COMMIT] = self.as_long_form(commit_ref=commit, branch=branch_to_rebuild)

            results.append({
                OUTPUT: branch_to_rebuild,
                BASEMENT: basement,
                BRANCH_CONTENTS: branch_contents
            })
            basement = branch_to_rebuild

        return results

    def as_long_form(self, commit_ref: str, branch: str):
        if commit_ref[0] == '~':
            return branch + commit_ref
        else:
            return commit_ref

    def log(self, msg: str):
        with open(file=LOG_FILE, mode='a') as log_file:
            print(msg, file=log_file)

    def start(self):
        current_branch = self.capture_current_branch()
        self.start_flow()
        print('Returning back...')
        os.system('git checkout ' + current_branch)


    def capture_current_branch(self) -> str:
        cmd = 'git rev-parse --abbrev-ref HEAD'
        output = subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)
        return str(output.splitlines()[0])

    def try_commit_changes(self) -> bool:
        current_branch = self.capture_current_branch()
        current_branch_configs = list(filter(lambda e: e[OUTPUT] == current_branch, self.config))

        if len(current_branch_configs) != 1:
            return False

        branch_config = current_branch_configs[0]

        if len(branch_config[BRANCH_CONTENTS]) == 0:
            return False

        head_content_desc = branch_config[BRANCH_CONTENTS][-1]

        if head_content_desc.get(BR_CONTENT_MSG,'') == '':
            return False

        can_commit_to_head = head_content_desc[BR_CONTENT_COMMIT] == current_branch+'~0'
        if not can_commit_to_head:
            return False

        def get_commit_hash(commit_link: str) -> str:
            cmd = 'git rev-parse ' + commit_link
            output = subprocess.check_output(cmd, cwd=self.cwd, universal_newlines=True, shell=True)
            return str(output.splitlines()[0])

        head_commit_hash = get_commit_hash(head_content_desc[BR_CONTENT_COMMIT])
        basement_commit_hash = get_commit_hash(branch_config[BASEMENT])

        should_amend = head_commit_hash != basement_commit_hash

        print('Got uncommitted changes:')
        os.system('cd ' + self.cwd + ' && git status')

        if should_amend:
            question = 'Amend all of them to head commit with message "'+head_content_desc[BR_CONTENT_MSG]+'"?'
        else:
            question = 'Commit all of them to head commit with message "'+head_content_desc[BR_CONTENT_MSG]+'"?'

        if cherry_picker.query_yes_no(question, self.input_provider, default='yes') != 'yes':
            return False

        amend = ''
        if should_amend:
            amend = '--amend'
        print(self.run_cmd('git commit '+amend+' --all --message="' + head_content_desc[BR_CONTENT_MSG] + '"'))
        return True


    def run_cmd(self, command) -> str:
        with subprocess.Popen(command,
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True,
                              cwd=self.cwd) as p:
            retcode = p.wait()
            if retcode != 0:
                raise Exception('failed to execute command:' + command + "\nOutput:\n" +
                          '\n'.join(p.stdout.readlines()) + '\n' +
                          '\n'.join(p.stderr.readlines()))
            return ''.join(p.stdout.readlines())


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

    WorkflowBuilder(
        yaml_config=args.config_file,
        cwd=CWD,
        force_update=args.force,
        dry_run=args.dry_run,
        quiet=args.quiet
    ).start()
pass
