#!/usr/bin/env sh
set -e
pytest --html=test_report.html --self-contained-html .
