#!/bin/sh
SCRIPT_DIR=$1
alias git-build="python3 $SCRIPT_DIR/builder/workflow_updater.py "
alias git-clean="python $SCRIPT_DIR/cleaner/main.py"
alias git-review="$SCRIPT_DIR/reviewer/run.sh"
