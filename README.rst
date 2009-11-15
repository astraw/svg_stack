svg_stack - concatenate SVG files
=================================

Overview
--------

This program concatenates (stacks) SVG graphics. It is designed to be
used from the command line or used within Python scripts. For example,
given the files red_ball.svg and blue_triangle.svg::

  svg_stack.py --direction=h --margin=100 red_ball.svg blue_triangle.svg > shapes.svg

will stack them horizontally with a 100 px margin between them. The
result will be in a file called shapes.svg.

Additionally, a Qt_ like API may be used to provide slightly more
advanced layout capabilities. See the file ``examples/qt_api_demo.py``
for examples of this type of use.

.. _Qt: http://qt.nokia.com/

Meta-data
---------

 * License: MIT (see source code of svg_stack for full license)
 * Author: Andrew D. Straw
 * Contact: strawman@astraw.com
 * Homepage: http://github.com/astraw/svg_stack
 * Issue tracker: http://github.com/astraw/svg_stack/issues

Usage
-----

::

  Usage: svg_stack FILE1 [FILE2] [...] [options]

  concatenate SVG files

  This will concatenate FILE1, FILE2, ... to a new svg file printed to
  stdout.



  Options:
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    --margin=MARGIN       size of margin (in any units, px default)
    --inkscape            attempt to work with Inkscape files
    --direction=DIRECTION
                          horizontal or vertical (or h or v)

