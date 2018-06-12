#!/bin/sh

start_dir="$PWD"
script_dir=`dirname $BASH_SOURCE`

cd $script_dir
python ./main.py $1
cd $start_dir
