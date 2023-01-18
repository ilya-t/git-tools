rm -rf ./toolsenv
python3 -m venv toolsenv
source toolsenv/bin/activate
pip3 install -r src/requirements.txt
pip3 install pytest-html==3.2.0
deactivate
