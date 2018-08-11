from __future__ import print_function

import os
import sys
from queue import Queue

from branch_filter import BranchFilter


def mixed_input(params_queue):
    if params_queue.empty():
        return input().lower()
    item = params_queue.get()
    print(item)
    return item



def main(args):
    arg_queue = Queue()
    for arg in args:
        arg_queue.put(arg)

    checkout_branch = BranchFilter(input_provider=lambda : mixed_input(arg_queue)).find_one()
    os.system('git checkout '+ checkout_branch)
    pass


if __name__ == '__main__':
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    main(args)