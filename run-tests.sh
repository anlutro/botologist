#!/bin/sh

if [ "$1" = "-v" ] || [ "$1" = "--venv" ]; then
	dir=$(dirname $(readlink -f $0))
	source $dir/.virtualenv/bin/activate
fi

python -m unittest discover -s tests/ -p '*_test.py'
