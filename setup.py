from distutils.core import setup
setup(name='svg_stack',
      description='stack multiple SVG images into a single output',
      version='0.1.0', # keep in sync with svg_stack.py
      author='Andrew Straw <strawman@astraw.com>',
      url='http://github.com/astraw/svg_stack',
      py_modules=['svg_stack'],
      scripts=['svg_stack.py'],
      )
