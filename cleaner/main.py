from __future__ import print_function

import pprint

import git
import os
import sys

import colorama
from colorama import Fore

import config


LOG_FILE = file(name=os.path.dirname(__file__)+'/delete.log', mode='a')

def find_dot_git(path):
    candidate = os.path.abspath(path)

    if (os.path.exists(candidate+'/.git')):
        return candidate
    else:
        return find_dot_git(os.path.dirname(candidate))

REPO_PATH = find_dot_git('.')

def git_branch_minus_D(_repository_path, _branch, _log_file):
    repo = git.Repo(_repository_path)
    sha = repo.git.rev_parse(_branch)
    msg = "Delete: " + _branch + " ( " + sha + " ) "
    print(Fore.RED + msg + Fore.RESET)
    print(msg, file=_log_file)
    repo.git.branch(_branch, '-D')
    pass


def last_commit(_commit_hash):
    repo = git.Repo(REPO_PATH)
    return repo.git.log('--oneline', '-1', _commit_hash)


def print_branches(_filter, _red):
    repo = git.Repo(REPO_PATH)

    i = 1
    for head in repo.branches:
        if _filter.__contains__(head.name):
            message = '{}. {}: {}'.format(i, head.name, last_commit(head.object))
            if (_red):
                print(Fore.RED + message + Fore.RESET)
            else:
                print(Fore.GREEN + message + Fore.RESET)
            i = i + 1

    pass

def diff(_branches, _strategy = config.Config()):
    for excluded in _strategy.exclude_branches:
        try:
            _branches.remove(excluded[0])
        except:
            pass
    pass

    print('Keep Branches:')
    for excluded in _strategy.exclude_branches:
        print(Fore.GREEN + excluded[0]+' - '+excluded[1])

    print ('')
    print(Fore.RESET + 'Unused Branches:')
    for _branch in _branches:
        print(Fore.RED + _branch)

    return len(_branches)
pass


def query_yes_no(question, default='yes'):
    '''Ask a yes/no question via raw_input() and return their answer.

    'question' is a string that is presented to the user.
    'default' is the presumed answer if the user just hits <Enter>.
        It must be 'yes' (the default), 'no' or None (meaning
        an answer is required of the user).

    The 'answer' return value is one of 'yes' or 'no'.
    '''
    valid = {'yes': 'yes', 'y': 'yes', 'ye': 'yes',
             'no': 'no', 'n': 'no'}
    if default == None:
        prompt = ' [y/n] '
    elif default == 'yes':
        prompt = ' [Y/n] '
    elif default == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " \
                             "(or 'y' or 'n').\n")
pass


def get_all_branches():
    repo = git.Repo(REPO_PATH)

    branch_names = []

    for head in repo.branches:
        branch_names.append(head.name)

    return branch_names


def get_active_branch():
    repo = git.Repo(REPO_PATH)
    return repo.active_branch.name


def find_branches_by_filter(_user_filter):
    repo = git.Repo(REPO_PATH)
    branch_names = []

    for head in repo.branches:
        if (head.name.__contains__(_user_filter)):
            branch_names.append(head.name)
            continue
        if (last_commit(head.object).__contains__(_user_filter)):
            branch_names.append(head.name)
            continue


    return branch_names


def start_filter_flow(_branches_for_deletion, _keep_branches):
    for kept_branch in _keep_branches:
        if (_branches_for_deletion.__contains__(kept_branch)):
            _branches_for_deletion.remove(kept_branch)
    print('Marked for Deletion:')
    print_branches(_branches_for_deletion, True)
    print('Kept branches:')
    print_branches(_keep_branches, False)
    print('')
    print('Type part of branch name or commit hash or log message to keep it or empty line to delete:')
    user_filter = raw_input().lower()

    if (user_filter != ''):
        for branch in find_branches_by_filter(user_filter):
            if (not _keep_branches.__contains__(branch)):
                _keep_branches.append(branch)
        start_filter_flow(_branches_for_deletion, _keep_branches)
    pass


def main(args):
    colorama.init()

    branches_for_deletion = get_all_branches()
    keep_branches = ['master']

    if (not keep_branches.__contains__(get_active_branch())):
        keep_branches.append(get_active_branch())

    start_filter_flow(branches_for_deletion, keep_branches)
    for branch in branches_for_deletion:
        git_branch_minus_D(REPO_PATH, branch, LOG_FILE)

    pass


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    main(args)