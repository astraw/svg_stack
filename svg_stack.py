#!/usr/bin/env python

## Copyright (c) 2009 Andrew D. Straw

## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:

## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
## THE SOFTWARE.

from lxml import etree # Ubuntu Karmic package: python-lxml
import sys
from optparse import OptionParser

VERSION = '0.0.1' # keep in sync with setup.py

UNITS = ['pt','px','in']
PT2IN = 1.0/72.0
IN2PT = 72.0
PT2PX = 1.25
PX2PT = 1.0/1.25

def get_unit_attr(value):
    # coordinate handling from http://www.w3.org/TR/SVG11/coords.html#Units
    units = None # default (user)
    for unit_name in UNITS:
        if value.endswith(unit_name):
            units = unit_name
            value = value[:-len(unit_name)]
            break
    val_float = float(value) # this will fail if units str not parsed
    return val_float, units

def convert_to_pixels( val, units):
    if units == 'px' or units is None:
        val_px = val
    elif units == 'pt':
        val_px = val*PT2PX
    elif units == 'in':
        val_px = val*IN2PT*PT2PX
    else:
        raise ValueError('unsupport unit conversion to pixels: %s'%units)
    return val_px

def fix_ids( elem, prefix, level=0 ):
    ns = '{http://www.w3.org/2000/svg}'

    if elem.tag.startswith(ns):

        tag = elem.tag[len(ns):]

        if 'id' in elem.attrib:
            elem.attrib['id'] = prefix + elem.attrib['id']

        # fix references (See http://www.w3.org/TR/SVGTiny12/linking.html#IRIReference )

        for attrib in elem.attrib.keys():
            value = elem.attrib.get(attrib,None)

            if value is not None:

                if attrib.startswith('{http://www.w3.org/1999/xlink}'):
                    relIRI = False
                else:
                    relIRI = True

                if (not relIRI) and value.startswith('#'): # local IRI, change
                    iri = value[1:]
                    value = '#' + prefix + iri
                    elem.attrib[attrib] = value
                elif relIRI and value.startswith('url(#') and value.endswith(')'): # local IRI, change
                    iri = value[5:-1]
                    value = 'url(#' + prefix + iri + ')'
                    elem.attrib[attrib] = value

        # Do same for children

    for child in elem:
        fix_ids(child,prefix,level=level+1)
    return elem

header_str = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Created with svg_stack (http://github.com/astraw/svg_stack) -->
"""

# ------------------------------------------------------------------
class Document(object):
    def __init__(self):
        self._layout = None
    def setLayout(self,layout):
        self._layout = layout
    def save(self,fileobj,**kwargs):
        if self._layout is None:
            raise ValueError('No layout, cannot save.')
        accum = LayoutAccumulator(**kwargs)
        self._layout.render(accum)
        if isinstance(fileobj,file):
            fd = fileobj
            close = False
        else:
            fd = open(fileobj,mode='w')
            close = True
        buf = accum.tostring(pretty_print=True)

        fd.write(header_str)
        fd.write( buf )
        if close:
            fd.close()

class SVGFile(object):
    def __init__(self,fname):
        self._fname = fname
        self._root = etree.parse(fname).getroot()
        if self._root.tag != '{http://www.w3.org/2000/svg}svg':
            raise ValueError('expected file to have root element <svg:svg>')

        height, height_units = get_unit_attr(self._root.get('height'))
        width, width_units = get_unit_attr(self._root.get('width'))
        self._width_px = convert_to_pixels( width, width_units)
        self._height_px = convert_to_pixels( height, height_units)
        self._orig_width_px = self._width_px
        self._orig_height_px = self._height_px
        self._coord = None # unassigned

    def get_root(self):
        return self._root

    def get_size(self,min_size=None):
        return Size(self._width_px,self._height_px)

    def _set_size(self,size):
        self._width_px = size.width
        self._height_px = size.height

    def _set_coord(self,coord):
        self._coord = coord

class LayoutAccumulator(object):
    def __init__(self,inkscape=False):
        self._inkscape = inkscape
        self._svgfiles = []

    def add_svg(self,svgfile):
        assert isinstance(svgfile,SVGFile)
        if svgfile in self._svgfiles:
            raise ValueError('cannot accumulate SVGFile instance twice')
        self._svgfiles.append( svgfile )

    def tostring(self, **kwargs):
        root = self._make_finalized_root()
        return etree.tostring(root,**kwargs)

    def _set_size(self,size):
        self._size = size

    def _make_finalized_root(self):
        # get all required namespaces and prefixes
        NSMAP = {None : 'http://www.w3.org/2000/svg' }
        for svgfile in self._svgfiles:
            origelem = svgfile.get_root()
            for key,value in origelem.nsmap.iteritems():
                if key in NSMAP:
                    assert value == NSMAP[key]
                    # Already in namespace dictionary
                    continue
                elif key == 'svg':
                    assert value == NSMAP[None]
                    # svg is the default namespace - don't insert again.
                    continue
                NSMAP[key] = value

        root = etree.Element('{http://www.w3.org/2000/svg}svg',
                             nsmap=NSMAP)

        if self._inkscape:
            root_defs = etree.SubElement(root,'{http://www.w3.org/2000/svg}defs')

        root.attrib['version']='1.1'
        for fname_num, svgfile in enumerate(self._svgfiles):
            origelem = svgfile.get_root()

            fix_id_prefix = 'id%d:'%fname_num
            elem = etree.SubElement(root,'{http://www.w3.org/2000/svg}g')
            elem.attrib['id'] = 'id%d'%fname_num

            elem_sz = svgfile.get_size()
            width_px = elem_sz.width
            height_px = elem_sz.height

            # copy svg contents into new group
            for child in origelem:
                if self._inkscape:
                    if child.tag == '{http://www.w3.org/2000/svg}defs':
                        # copy into root_defs, not into sub-group
                        for subchild in child:
                            fix_ids( subchild, fix_id_prefix )
                            root_defs.append( subchild )
                        continue
                    elif child.tag == '{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}:namedview':
                        # don't copy
                        continue
                    elif child.tag == '{http://www.w3.org/2000/svg}metadata':
                        # don't copy
                        continue
                elem.append(child)

            fix_ids( elem, fix_id_prefix )

            translate_x = svgfile._coord[0]
            translate_y = svgfile._coord[1]
            if svgfile._orig_width_px != width_px:
                raise NotImplementedError('rescaling width not implemented')
            if svgfile._orig_height_px != height_px:
                raise NotImplementedError('rescaling height not implemented')
            orig_viewBox = origelem.get('viewBox')
            if orig_viewBox is not None:
                # split by comma or whitespace
                vb_tup = orig_viewBox.split(',')
                vb_tup = [c.strip() for c in vb_tup]
                if len(vb_tup)==1:
                    # not separated by commas
                    vb_tup = orig_viewBox.split()
                assert len(vb_tup)==4
                vb_tup = [float(v) for v in vb_tup]
                vbminx, vbminy, vbwidth, vbheight = vb_tup
                sx = width_px / vbwidth
                sy = height_px / vbheight
                tx = translate_x - vbminx
                ty = translate_y - vbminy
                elem.attrib['transform'] = 'matrix(%s,0,0,%s,%s,%s)'%(
                    sx,sy,tx,ty)
            else:
                elem.attrib['transform'] = 'translate(%s,%s)'%(
                    translate_x, translate_y)
            root.append( elem )

        root.attrib["width"] = repr(self._size.width)
        root.attrib["height"] = repr(self._size.height)

        return root

# ------------------------------------------------------------------
class Size(object):
    def __init__(self, width=0, height=0):
        self.width=width
        self.height=height

# directions for BoxLayout
LeftToRight = 'LeftToRight'
RightToLeft = 'RightToLeft'
TopToBottom = 'TopToBottom'
BottomToTop = 'BottomToTop'

# alignment values
AlignLeft = 0x01
AlignRight = 0x02
AlignHCenter = 0x04

AlignTop = 0x020
AlignBottom = 0x040
AlignVCenter = 0x080

AlignCenter = AlignHCenter | AlignVCenter

class Layout(object):
    def __init__(self, parent=None):
        if parent is not None:
            raise NotImplementedError('')

class BoxLayout(Layout):
    def __init__(self, direction, parent=None):
        super(BoxLayout,self).__init__(parent=parent)
        self._direction = direction
        self._items = []
        self._contents_margins = 0 # around edge of box
        self._spacing = 0 # between items in box
        self._coord = (0,0) # default
        self._size = None # uncalculated

    def _set_coord(self,coord):
        self._coord = coord

    def render(self,accum, min_size=None, level=0):
        size = self.get_size(min_size=min_size)
        if level==0:
            # set document size if top level
            accum._set_size(size)
        for (item,stretch,alignment) in self._items:
            if isinstance( item, SVGFile ):
                accum.add_svg(item)
            elif isinstance( item, BoxLayout ):
                item.render( accum, min_size=item._size, level=level+1 )
            else:
                raise NotImplementedError(
                    "don't know how to accumulate item %s"%item)

    def get_size(self, min_size=None):
        cum_dim = 0 # size along layout direction
        max_orth_dim = 0 # size along other direction

        if min_size is None:
            min_size = Size(0,0)

        # Step 1: calculate required size along self._direction
        if self._direction in [LeftToRight, RightToLeft]:
            max_orth_dim = min_size.height
            dim_min_size = Size(width=0,
                                height=max_orth_dim)
        else:
            max_orth_dim = min_size.width
            dim_min_size = Size(width=max_orth_dim,
                                height=0)

        cum_dim += self._contents_margins # first margin
        item_normcoords = []
        item_sizes = []
        for item_number,(item,stretch,alignment) in enumerate(self._items):
            item_size = item.get_size(min_size=dim_min_size)
            item_sizes.append( item_size )
            item_normcoords.append( (cum_dim, self._contents_margins) )

            if self._direction in [LeftToRight, RightToLeft]:
                cum_dim += item_size.width
                max_orth_dim = max(max_orth_dim,item_size.height)
            else:
                cum_dim += item_size.height
                max_orth_dim = max(max_orth_dim,item_size.width)

            if (item_number+1) < len(self._items):
                cum_dim += self._spacing # space between elements
        cum_dim += self._contents_margins # last margin
        max_orth_dim += 2*self._contents_margins # margins

        # Step 2: which is bigger - required size or minimum size
        expansion = False
        if (self._direction in [LeftToRight, RightToLeft]):
            if min_size.width > cum_dim:
                expansion=True
        else:
            if min_size.height > cum_dim:
                expansion=True

        # Step 3: calculate coordinates of each item

        if expansion:
            # required size less than minimum size
            item_normcoords = None # invalid
            # need to incorporate stretch data here
            raise NotImplementedError('expanding box not yet done')
        # else required size is larger than minimum size

        if self._direction in [LeftToRight, RightToLeft]:
            size = Size(cum_dim, max_orth_dim)
        else:
            size = Size(max_orth_dim, cum_dim)

        coords = []
        for ic in item_normcoords:
            if self._direction == LeftToRight:
                coords.append( (ic[0],ic[1]) )
            elif self._direction == TopToBottom:
                coords.append( (ic[1],ic[0]) )
            else:
                raise NotImplementedError(
                    'direction %s not implemented'%self._direction)
        del item_normcoords

        # Step 4: set coordinates of each item
        for i in range(len(self._items)):
            coord = coords[i]
            (item, stretch, alignment) = self._items[i]
            box_pos = (self._coord[0]+coord[0], self._coord[1]+coord[1])
            item_size = item_sizes[i]
            if self._direction in [LeftToRight, RightToLeft]:
                # expand vertically
                box_size = Size(item_size.width, max_orth_dim)
            else:
                # expand horizontally
                box_size = Size(max_orth_dim, item_size.height)
            item_pos, item_size = self._calc_box( box_pos, box_size, item_size,
                                                  alignment )
            item._set_coord( item_pos )
            item._set_size( item_size )
            tmp = item.get_size()

        self._size = size
        return size

    def _calc_box(self, in_pos, in_sz, item_sz, alignment):
        if (AlignLeft & alignment):
            left = in_pos[0]
            width = item_sz.width
        elif (AlignRight & alignment):
            left = in_pos[0]+in_sz.width-item_sz.width
            width = item_sz.width
        elif (AlignHCenter & alignment):
            left = in_pos[0]+0.5*(in_sz.width-item_sz.width)
            width = item_sz.width
        else:
            # expand
            left = in_pos[0]
            width = in_sz.width

        if (AlignTop & alignment):
            top = in_pos[1]
            height = item_sz.height
        elif (AlignBottom & alignment):
            top = in_pos[1]+in_sz.height-item_sz.height
            height = item_sz.height
        elif (AlignVCenter & alignment):
            top = in_pos[1]+0.5*(in_sz.height-item_sz.height)
            height = item_sz.height
        else:
            # expand
            top = in_pos[1]
            height = in_sz.height

        pos = (left,top)
        size = Size(width,height)
        return pos,size

    def _set_size(self, size):
        self._size = size

    def setSpacing(self,spacing):
        self._spacing = spacing

    def addSVG(self, svg_file, stretch=0, alignment=0):
        if not isinstance(svg_file,SVGFile):
            svg_file = SVGFile(svg_file)
        self._items.append((svg_file,stretch,alignment))

    def addLayout(self, layout, stretch=0):
        assert isinstance(layout,Layout)
        alignment=0 # expand
        self._items.append((layout,stretch,alignment))

class HBoxLayout(BoxLayout):
    def __init__(self, parent=None):
        super(HBoxLayout,self).__init__(LeftToRight,parent=parent)

class VBoxLayout(BoxLayout):
    def __init__(self, parent=None):
        super(VBoxLayout,self).__init__(TopToBottom,parent=parent)

# ------------------------------------------------------------------

def main():
    usage = '''%prog FILE1 [FILE2] [...] [options]

concatenate SVG files

This will concatenate FILE1, FILE2, ... to a new svg file printed to
stdout.

'''

    parser = OptionParser(usage, version=VERSION)
    parser.add_option("--margin",type='str',
                      help='size of margin (in any units, px default)',
                      default=None)
    parser.add_option("--inkscape",action='store_true',default=False,
                      help='attempt to work with Inkscape files')
    parser.add_option("--direction",type='str',
                      default='vertical',
                      help='horizontal or vertical (or h or v)')
    (options, args) = parser.parse_args()
    fnames = args

    if options.direction.lower().startswith('v'):
        direction = 'vertical'
    elif options.direction.lower().startswith('h'):
        direction = 'horizontal'
    else:
        raise ValueError('unknown direction %s'%options.direction)

    if options.margin is not None:
        margin_px = convert_to_pixels(*get_unit_attr(options.margin))
    else:
        margin_px = 0

    if 0:
        fd = open('tmp.svg',mode='w')
    else:
        fd = sys.stdout

    doc = Document()
    if direction == 'vertical':
        layout = VBoxLayout()
    elif direction == 'horizontal':
        layout = HBoxLayout()

    for fname in fnames:
        layout.addSVG(fname,alignment=AlignCenter)

    layout.setSpacing(margin_px)
    doc.setLayout(layout)
    doc.save( fd, inkscape=options.inkscape )

if __name__=='__main__':
    main()
