pip3 install pytest-html==1.22.0

chmod +x builder/run_tests.sh
pip install -r builder/requirements.txt 

pip3 install -r cleaner/requirements.txt 
chmod +x reviewer/run.sh

chmod +x tests/*.sh
