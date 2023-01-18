#!/bin/sh
SCRIPT_DIR=$1
PYTHON3=$SCRIPT_DIR/toolsenv/bin/python3
alias git-checkout="$PYTHON3 $SCRIPT_DIR/src/run_switcher.py "
alias git-build="$PYTHON3 $SCRIPT_DIR/src/workflow_updater.py "
alias git-j="$PYTHON3 $SCRIPT_DIR/src/workflow_jumper.py"
alias git-clean="$PYTHON3 $SCRIPT_DIR/src/run_cleaner.py"
alias git-review="$SCRIPT_DIR/reviewer/run.sh"

