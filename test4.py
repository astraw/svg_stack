#!/usr/bin/env python

import subprocess

# stack two Inkscape generated files
subprocess.check_call(
    'svg_stack --direction=h --inkscape inkscape-pattern.svg > inkscape-pattern-copy.svg',
    shell=True)

# Inkscape files don't pass xmllint -- don't test

print 'You should manually verify that inkscape-pattern.svg looks exactly the same as inkscape-pattern-copy.svg'

subprocess.check_call(
    'rasterizer  inkscape-pattern-copy.svg',
    shell=True)
