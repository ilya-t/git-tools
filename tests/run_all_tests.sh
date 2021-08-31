#!/usr/bin/env sh
set -e

mkdir -p ./reports/
cd ../builder
../toolsenv/bin/pytest --html=../tests/reports/builder_report.html --self-contained-html ./test_*.py
cd ../cleaner
../toolsenv/bin/pytest --html=../tests/reports/cleaner_report.html --self-contained-html ./test_*.py
cd ../switcher
../toolsenv/bin/pytest --html=../tests/reports/switcher_report.html --self-contained-html ./test_*.py
cd ..

echo "See test reports: "
echo "  ./reports/builder_report.html"
echo "  ./reports/cleaner_report.html"
echo "  ./reports/switcher_report.html"
