rm -rf ./toolsenv
python3 -m venv toolsenv
source toolsenv/bin/activate
pip3 install -r builder/requirements.txt
pip3 install -r cleaner/requirements.txt
pip3 install pytest-html==1.22.0
deactivate
chmod +x builder/run_tests.sh
chmod +x reviewer/run.sh
chmod +x tests/*.sh
