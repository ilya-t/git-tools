from __future__ import print_function

import os
import sys

from branch_filter import BranchFilter


def main(args):
    checkout_branch = BranchFilter().find_one()
    os.system('git checkout '+ checkout_branch)
    pass


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    main(args)