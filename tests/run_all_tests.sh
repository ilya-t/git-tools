#!/usr/bin/env sh
set -e
cd builder
./run_tests.sh
cd ../cleaner
python3 -m unittest test_clean_merged.py
cd ../switcher
python3 -m unittest test_branchFilter.py
cd ..