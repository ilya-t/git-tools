#!/usr/bin/env sh
set -e
cd builder
./run_tests.sh
cd ../cleaner
pytest --html=test_report.html --self-contained-html test_clean_merged.py
cd ../switcher
pytest --html=test_report.html --self-contained-html test_branchFilter.py
cd ..