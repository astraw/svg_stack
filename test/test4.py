#!/usr/bin/env python
from __future__ import print_function

import subprocess

# "stack" a single Inkscape file
subprocess.check_call(
    '../svg_stack.py inkscape-pattern.svg > inkscape-pattern-copy.svg',
    shell=True)

# Inkscape files don't pass xmllint -- don't test

print('You should manually verify that inkscape-pattern.svg looks exactly the same as inkscape-pattern-copy.svg')

# subprocess.check_call(
#     'rasterizer  inkscape-pattern-copy.svg',
#     shell=True)
