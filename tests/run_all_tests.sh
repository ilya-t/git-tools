#!/usr/bin/env sh
set -e

mkdir -p ./reports/
set +e
cd ../builder
../toolsenv/bin/pytest --html=../tests/reports/builder_report.html --self-contained-html ./test_*.py
BUILDER_RET_CODE=$?
cd ../cleaner
../toolsenv/bin/pytest --html=../tests/reports/cleaner_report.html --self-contained-html ./test_*.py
CLEANER_RET_CODE=$?
cd ../switcher
../toolsenv/bin/pytest --html=../tests/reports/switcher_report.html --self-contained-html ./test_*.py
SWITCHER_RET_CODE=$?
cd ..

echo "See test reports: "

RETCODE=0

if [ "$BUILDER_RET_CODE" != "0" ]; then
    echo "  ./reports/builder_report.html (FAILED)"
    RETCODE=1
else
    echo "  ./reports/builder_report.html"
fi

if [ "$CLEANER_RET_CODE" != "0" ]; then
    echo "  ./reports/cleaner_report.html (FAILED)"
    RETCODE=1
else
    echo "  ./reports/cleaner_report.html"
fi

if [ "$SWITCHER_RET_CODE" != "0" ]; then
    echo "  ./reports/switcher_report.html (FAILED)"
    RETCODE=1
else
    echo "  ./reports/switcher_report.html"
fi

exit $RETCODE
