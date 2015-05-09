#!/bin/bash
dir=$(dirname $(readlink -f $0))
source $dir/.virtualenv/bin/activate && $dir/run.py
