#!/usr/bin/env sh
set -e
python3 -m unittest test_cherry_picker.py
python3 -m unittest test_workflow_updater.py
