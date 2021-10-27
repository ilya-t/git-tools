#!/bin/sh
SCRIPT_DIR=$1
PYTHON3=$SCRIPT_DIR/toolsenv/bin/python3
alias git-checkout="$PYTHON3 $SCRIPT_DIR/builder/run_switcher.py "
alias git-build="$PYTHON3 $SCRIPT_DIR/builder/workflow_updater.py "
alias git-clean="$PYTHON3 $SCRIPT_DIR/builder/run_cleaner.py"
alias git-review="$SCRIPT_DIR/reviewer/run.sh"
