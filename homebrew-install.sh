#!/bin/bash
# Add numpy includes for cython compilation , required for MacOS homebrew
export CFLAGS="-I /usr/local/lib/python3.8/site-packages/numpy/core/include $CFLAGS"
python3 setup.py install
