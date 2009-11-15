#!/usr/bin/env python

import svg_stack as ss

doc = ss.Document()

layout1 = ss.HBoxLayout()
layout1.addSVG('red_ball.svg')
layout1.addSVG('blue_triangle.svg')

layout2 = ss.VBoxLayout()

layout2.addSVG('red_ball.svg')
layout2.addSVG('red_ball.svg')
layout2.addSVG('red_ball.svg')
layout1.addLayout(layout2)

doc.setLayout(layout1)

doc.save('qt_api_test.svg')
