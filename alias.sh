#!/bin/sh
SCRIPT_DIR=$1
alias git-checkout="python3 $SCRIPT_DIR/switcher/main.py "
alias git-build="python3 $SCRIPT_DIR/builder/workflow_updater.py "
alias git-clean="python3 $SCRIPT_DIR/cleaner/clean_merged.py"
alias git-review="$SCRIPT_DIR/reviewer/run.sh"
