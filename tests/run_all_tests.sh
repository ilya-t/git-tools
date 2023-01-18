#!/usr/bin/env sh
set -e

mkdir -p ./reports/
set +e
rm -rf ./repo-cache
cd ../src
../toolsenv/bin/pytest --html=../tests/reports/tests_report.html --self-contained-html ./test_*.py
BUILDER_RET_CODE=$?
cd ..

echo "See test reports: "

RETCODE=0

if [ "$BUILDER_RET_CODE" != "0" ]; then
    echo "GOT FAILED TESTS:"
    RETCODE=1
else
    echo "All tests passed:"
fi

echo "  ./reports/tests_report.html"

exit $RETCODE
