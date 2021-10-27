#!/usr/bin/env sh
set -e

mkdir -p ./reports/
set +e
rm -rf ./repo-cache
cd ../builder
../toolsenv/bin/pytest --html=../tests/reports/tests_report.html --self-contained-html ./test_*.py
BUILDER_RET_CODE=$?
cd ..

echo "See test reports: "

RETCODE=0

if [ "$BUILDER_RET_CODE" != "0" ]; then
    echo "  ./reports/tests_report.html (FAILED)"
    RETCODE=1
else
    echo "  ./reports/tests_report.html"
fi

exit $RETCODE
