#!/bin/sh

start_dir="$PWD"
script_dir=`dirname $BASH_SOURCE`

cd $script_dir
python3 ./main.py
cd $start_dir
