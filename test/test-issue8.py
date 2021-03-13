#!/usr/bin/env python
from __future__ import print_function

import subprocess

subprocess.check_call(
    '../svg_stack.py --direction=h --margin=100 issue8.svg > issue8-copy.svg',
    shell=True)
