chmod +x builder/run_tests.sh
chmod +x builder/tests/*.sh
pip install -r builder/requirements.txt 

pip install -r cleaner/requirements.txt 
chmod +x cleaner/run.sh

chmod +x reviewer/run.sh
