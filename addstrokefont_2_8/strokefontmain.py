#
#
# Main module of Blender Stroke Font add-on.
# The stroke font xml files are assumed to be in the strokefontdata subdirectory.
#
# Supported Blender Version: 2.8 Beta
#
# Copyright (C) 2019  Shrinivas Kulkarni
#
# License: GPL (https://github.com/Shriinivas/blenderstrokefont/blob/master/LICENSE)
#
# Not yet pep8 compliant 

import os, sys, re, math
from mathutils import Vector, Matrix
from xml.dom.minidom import parse, Document
import bpy, bmesh

from . stroke_font_manager import getFontNames, FontData, CharData, DrawContext

DEF_ERR_MARGIN = 0.0001

def floatCmpWithMargin(float1, float2, margin = DEF_ERR_MARGIN):
    return abs(float1 - float2) < margin

def vectCmpWithMargin(v1, v2, margin = DEF_ERR_MARGIN):
    return all(floatCmpWithMargin(v1[i], v2[i], margin) for i in range(0, len(v1)))

def getfontNameList(scene, context):
    if(getfontNameList.fontNames != None):
        return getfontNameList.fontNames

    parentPath = os.path.dirname(__file__)
    getfontNameList.fontNames = [(n, n, n) for n in getFontNames(parentPath)]

    return getfontNameList.fontNames

#Called too many times, so cache
getfontNameList.fontNames = None

def subdivide(bm, subdivCnt, w, h):    
    wIncr = w / subdivCnt 
    hIncr = h / subdivCnt

    wStart = -w/2
    hStart = -h/2

    for i in range(1, subdivCnt):
        ret = bmesh.ops.bisect_plane(bm, geom=bm.verts[:]+bm.edges[:]+bm.faces[:], \
            plane_co=(wStart + wIncr * i, 0,0), plane_no=Vector((1,0,0)))
        ret = bmesh.ops.bisect_plane(bm, geom=bm.verts[:]+bm.edges[:]+bm.faces[:], \
            plane_co=(0, hStart + hIncr * i, 0), plane_no=Vector((0, 1,0)))
    
def createPlane(leftTop, bottomRight, collection):
    z = leftTop[2] #z is same for both
    w = bottomRight[0] - leftTop[0]
    h = leftTop[1] - bottomRight[1]
    
    bm = bmesh.new()
    v0 = bm.verts.new((-w/2, -h/2, 0))
    v1 = bm.verts.new((w/2, -h/2, 0))
    v2 = bm.verts.new((-w/2, h/2, 0))
    v3 = bm.verts.new((w/2, h/2, 0))
    
    bm.faces.new((v0, v1, v3, v2))

    subdivide(bm, subdivCnt = 50, w = w, h = h)
    
    me   = bpy.data.meshes.new('plane')
    bm.to_mesh(me)
    bm.free()

    obj   = bpy.data.objects.new('plane', me)
    collection.objects.link(obj)
    obj.location = (leftTop[0] + w / 2, bottomRight[1] + h / 2, z)
    
    return obj
          
def main(context, rectangles = None):
    params = context.window_manager.AddStrokeFontTextParams
    
    action = params.action    
    text = params.text
    filePath = bpy.path.abspath(params.filePath)

    fontName = params.fontName
    fontSize = params.fontSize

    charSpacing = params.charSpacing
    wordSpacing = params.wordSpacing
    lineSpacing = params.lineSpacing
    isFlat = params.isFlat
    rgba = params.rgba
    copyPropObj = params.copyPropertiesCurve

    if(isFlat): copyPropObj = None
    else: rgba = None

    try:
        if(params.copyPropertiesCurve != None):
            params.copyPropertiesCurve.data
    except:
        params.copyPropertiesCurve = None
    

    cloneGlyphs = params.cloneGlyphs
    confined = params.confined
    width = params.width
    height = params.height
    margin = params.margin
    hAlignment = params.hAlignment
    vAlignment = params.vAlignment
    expandDir = None if params.expandDir == 'none' else params.expandDir
    expandDist = params.expandDist
    addPlane = params.addPlane
    
    return addText(fontName, fontSize, charSpacing, wordSpacing, lineSpacing, copyPropObj, \
        rgba, text, cloneGlyphs, action, filePath, confined, width, height, \
            margin, hAlignment, vAlignment, expandDir, expandDist, rectangles, addPlane)

#Default options if called from writing animation
def addText(fontName, fontSize, charSpacing, wordSpacing, lineSpacing, copyPropObj, rgba, \
    text, cloneGlyphs, action = 'addInputText', filePath = None, confined = False, \
        width = None, height = None, margin = None, hAlignment = None, \
            vAlignment = None, expandDir = None, expandDist  = None, \
                rectangles = None, addPlane = None):        
    
    parentPath = os.path.dirname(__file__)
    
    bevelDepth = 0.01 * fontSize
    
    renderer = BlenderFontRenderer(copyPropObj, bevelDepth, cloneGlyphs, rgba)

    if(action == "addGlyphTable"):
        charSpacing = 1
        lineSpacing = 2

    context = DrawContext(parentPath, fontName, fontSize, charSpacing, wordSpacing, lineSpacing, 
        BlenderCharDataFactory(), renderer, bottomToTop = True) 
    
    if(action == "addGlyphTable"):
        context.renderGlyphTable()
    else:
        if(action == 'addInputText'):
            text = text.replace('\\n','\n').replace('\\\n','\\n')

        elif(action == "addFromFile"):
            try:
                with open(filePath, 'rU') as f: 
                    text = f.read() 
            except:
                return None

        if(text[0] == u'\ufeff'):
            text = text[1:]

        if(rectangles):
            context.renderCharsInSelBoxes(text, rectangles, margin, hAlignment, vAlignment, addPlane)
            
        elif(confined):
            x1, y1, z1 = bpy.context.scene.cursor.location
            x2, y2, z2 = x1 + width, y1 - height, z1
            rectangles = [[Vector((x1, y1, z1)), Vector((x2, y2, z2))]]
            context.renderCharsInSelBoxes(text, rectangles, margin, hAlignment, \
                vAlignment, addPlane, expandDir, expandDist)
        else:
            context.renderCharsWithoutBox(text)
        
    return renderer.collection
        
class BlenderCharData(CharData):
    def __init__(self, char, rOffset, segs, glyphName):
        self.segs = segs
        super(BlenderCharData, self).__init__(char, rOffset, glyphName)
    
    def scaleGlyph(self, scaleX, scaleY):
        self.rOffset *= scaleX
        for i, seg in enumerate(self.segs):
            pts = []
            for j in range(0, len(seg)):
                pts.append(complex(seg[j].real * scaleX, -scaleY * seg[j].imag))            
                
            self.segs[i] = CubicBezier(*pts)
        self.bbox = self.getBBox()

    def getBBox(self):
        bbox = [None] * 4
        for cb in self.segs:
            bb = getCBezierBBox(cb)
            if(bbox[0] == None or bb[0][0] < bbox[0]): bbox[0] = bb[0][0]
            if(bbox[1] == None or bb[1][0] > bbox[1]): bbox[1] = bb[1][0]
            if(bbox[2] == None or bb[1][1] > bbox[2]): bbox[2] = bb[1][1]
            if(bbox[3] == None or bb[0][1] < bbox[3]): bbox[3] = bb[0][1]
        return bbox

class BlenderCharDataFactory:
    def __init__(self):
        pass
        
    def getCharData(self, char, rOffset, pathStr, glyphName):
        segs = parse_path(pathStr)
        return BlenderCharData(char, rOffset, segs, glyphName)

class BlenderFontRenderer:
    def __init__(self, copyPropObj, bevelDepth, cloneGlyphs, rgba):
        matName = 'Flat Text Material'
        self.copyPropObj = copyPropObj
        self.collection = None
        self.currCollection = None
        self.z = bpy.context.scene.cursor.location[2]
        self.bevelDepth = bevelDepth
        self.currPlane = None
        self.bevelObj = None
        if(rgba != None):
            self.objMat = getFlatMat(matName, rgba)
        else:
            self.objMat = None
        self.cloneGlyphs = cloneGlyphs
        self.charObjDataCache = {}

    def renderChar(self, charData, x, y, naChar):
        curveData = self.charObjDataCache.get(charData.char)
        isFlat = self.objMat != None
        curve = CPath().addCurve(charData, self.copyPropObj, \
            curveData, self.cloneGlyphs, self.bevelDepth, isFlat)
        if(curveData == None):
            self.charObjDataCache[charData.char] = curve.data
            
        self.currCollection.objects.link(curve)

        curve.location[0] += x
        curve.location[1] += y
        curve.location[2] = self.z
        curve.data.bevel_object = self.bevelObj
        if(isFlat):
            curve.data.materials.append(self.objMat)

        if(self.currPlane != None):
            curve.parent = self.currPlane
            curve.matrix_parent_inverse = self.currPlane.matrix_world.inverted()
            mod = curve.modifiers.new('mod', type='SHRINKWRAP')
            mod.target = self.currPlane
            mod.offset = -0.001
            
        curve.select_set(False)
        
    def beforeRender(self):
        self.collection = bpy.data.collections.new('StrokeFontText')
        bpy.context.scene.collection.children.link(self.collection)
        if(self.objMat != None):
            self.bevelObj = createCircle(self.bevelDepth, self.collection)
        self.currCollection = self.collection
    
    def newBoxToBeRendered(self, box, addPlane):        
        self.currCollection = bpy.data.collections.new('StrokeFontTextBox')
        self.collection.children.link(self.currCollection)     
        self.z = box[0][2]
        if(addPlane):
            self.currPlane = createPlane(box[0], box[1], self.currCollection)
            # ~ bpy.context.scene.update()        
            bpy.context.evaluated_depsgraph_get().update()

    
    def moveBoxInYDir(self, moveBy):
        for o in self.currCollection.objects:
            if(o.type == 'CURVE'):
                o.location[1] += moveBy

    def centerInView(self, width, height):          
        pass

    def renderPlainText(self, text, size, x, y, objName):
        myFont = bpy.data.curves.new(type = "FONT", name = objName)
        fontOb = bpy.data.objects.new(objName, myFont)
        fontOb.data.body = text
        self.collection.objects.link(fontOb)
        fontOb.location = Vector((x, y, self.z))
        fontOb.scale = [size, size, 1]

        if(self.copyPropObj != None and \
            len(self.copyPropObj.data.materials) > 0):
            copyMatIdx = self.copyPropObj.active_material_index
            mat = self.copyPropObj.data.materials[copyMatIdx]
            fontOb.data.materials.append(mat)
            fontOb.active_material_index = 0
        
        # ~ return fontOb
        
    def getBoxLeftTopRightBottom(self, box):
        x1 = box[0][0]
        y1 = box[0][1]

        x2 = box[1][0]
        y2 = box[1][1]
        
        return min(x1, x2), max(y1, y2), max(x1, x2), min(y1, y2)
        
    def getBoxFromCoords(self, x1, y1, x2, y2):
        return [Vector((x1, y1, self.z)), Vector((x2, y2, self.z))]
        
    def getDefaultStartLocation(self):
        x, y, z = bpy.context.scene.cursor.location
        return x, y
        
#Avoid errors due to floating point conversions/comparisons
def cmplxCmpWithMargin(complex1, complex2, margin = DEF_ERR_MARGIN):
    return floatCmpWithMargin(complex1.real, complex2.real, margin) and \
        floatCmpWithMargin(complex1.imag, complex2.imag, margin)

def floatCmpWithMargin(float1, float2, margin = DEF_ERR_MARGIN):
    return abs(float1 - float2) < margin 
    
def getDisconnParts(segs):
    prevSeg = None
    disconnParts = []
    newSegs = []
    
    for i in range(0, len(segs)):
        seg = segs[i]
        if((prevSeg== None) or not cmplxCmpWithMargin(prevSeg.end, seg.start)):
            if(len(newSegs) > 0):
                disconnParts.append(Path(newSegs, isClosed = segs[-1].isClosing))
            newSegs = []
        prevSeg = seg
        newSegs.append(seg)

    if(len(segs) > 0 and len(newSegs) > 0):
        disconnParts.append(Path(newSegs, isClosed = newSegs[-1].isClosing))

    return disconnParts

def get3DVector(cmplx, z = 0):
    return Vector((cmplx.real, cmplx.imag, z))


def isBezier(bObj):
    return bObj.type == 'CURVE' and len(bObj.data.splines) > 0 \
        and bObj.data.splines[0].type == 'BEZIER'

# Note: Copied from blenderbezierutils (TODO: keep in sync or find an alternative)
def copyObjAttr(src, dest, invDestMW = Matrix(), mw = Matrix()):
    for att in dir(src):
        try:
            if(att not in ['co', 'handle_left', 'handle_right', \
                'handle_left_type', 'handle_right_type']):
                setattr(dest, att, getattr(src, att))
        except Exception as e:
            pass
    try:
        lt = src.handle_left_type
        rt = src.handle_right_type
        dest.handle_left_type = 'FREE'
        dest.handle_right_type = 'FREE'
        dest.co = invDestMW @ (mw @ src.co)
        dest.handle_left = invDestMW @ (mw @ src.handle_left)
        dest.handle_right = invDestMW @ (mw @ src.handle_right)
        dest.handle_left_type = lt
        dest.handle_right_type = rt
        pass
    except Exception as e:
        pass

def getFlatMat(matName, rgba):
    for mat in bpy.data.materials:
        if(mat.name.startswith('Flat Text Material')):
            crNode = mat.node_tree.nodes.get('ColorRamp')
            if(crNode != None):
                elem = crNode.color_ramp.elements
                if(vectCmpWithMargin(elem[0].color, rgba) and \
                    vectCmpWithMargin(elem[1].color, rgba)):
                    return mat
    mat = bpy.data.materials.new(matName)
    mat.use_nodes = True
    
    tree = mat.node_tree
    links = tree.links

    ns = [n.name for n in tree.nodes]
    for n in ns:
        tree.nodes.remove(tree.nodes[n])

    materialShader = tree.nodes.new('ShaderNodeOutputMaterial')
    bsdfShader = tree.nodes.new('ShaderNodeBsdfPrincipled')
    rgbShader = tree.nodes.new('ShaderNodeShaderToRGB')
    colorRampShader = tree.nodes.new('ShaderNodeValToRGB')
    
    colorRampShader.color_ramp.elements[0].color = rgba
    colorRampShader.color_ramp.elements[1].color = rgba

    links.new(bsdfShader.outputs['BSDF'], rgbShader.inputs['Shader'])
    links.new(rgbShader.outputs['Color'], colorRampShader.inputs['Fac'])
    links.new(colorRampShader.outputs['Color'], \
        materialShader.inputs['Surface'])

    return mat

def createCircle(radius, collection, hide = True):
    cName = '_bevelCircle'
    data = bpy.data.curves.new(cName, 'CURVE')
    data.dimensions = '3D'            
    spline = data.splines.new('BEZIER')
    spline.use_cyclic_u = True
    bpts = spline.bezier_points
    bpts.add(3)
    
    d = 2 * 0.27606262
    bpts[0].co = Vector((radius, 0, 0))
    bpts[0].handle_right = Vector((radius, radius * d, 0))
    bpts[0].handle_left = Vector((radius, -radius * d, 0))
    bpts[1].co = Vector((0, radius, 0))
    bpts[1].handle_right = Vector((-radius * d, radius, 0))
    bpts[1].handle_left = Vector((radius * d, radius, 0))
    bpts[2].co = Vector((-radius, 0, 0))
    bpts[2].handle_right = Vector((-radius, -radius * d, 0))
    bpts[2].handle_left = Vector((-radius, radius * d, 0))
    bpts[3].co = Vector((0, -radius, 0))
    bpts[3].handle_right = Vector((radius * d, -radius, 0))
    bpts[3].handle_left = Vector((-radius * d, -radius, 0))

    obj = bpy.data.objects.new(cName, data)
    collection.objects.link(obj)
    if(hide):
        obj.hide_set(True)
        obj.hide_render = True

    return obj


class CPath:

    def __init__(self):
        pass

    def getNewCurveData(self, charData, copyPropObj):
        segs = charData.segs
        parts = getDisconnParts(segs)
        
        if(copyPropObj != None and isBezier(copyPropObj)):
            newCurveData = copyPropObj.data.copy()
            newCurveData.name = charData.char
            newCurveData.splines.clear()
        else:
            newCurveData = bpy.data.curves.new(charData.char, 'CURVE')
            
        splinesData = []

        for i, part in enumerate(parts):
            splinesData.append(part.getBezierPtsInfo())

        for i, newPoints in enumerate(splinesData):

            spline = newCurveData.splines.new('BEZIER')
            spline.bezier_points.add(len(newPoints)-1)
            spline.use_cyclic_u = parts[i].isClosed
            
            for j in range(0, len(spline.bezier_points)):
                newPoint = newPoints[j]
                spline.bezier_points[j].co = newPoint[0]
                spline.bezier_points[j].handle_left = newPoint[1]
                spline.bezier_points[j].handle_right = newPoint[2]
                spline.bezier_points[j].handle_right_type = 'FREE'
                spline.bezier_points[j].handle_left_type = 'FREE'

        return newCurveData

    def addCurve(self, charData, copyPropObj, curveData, cloneGlyphs, \
        bevelDepth, isFlat):
        if(curveData == None):
            curveData = self.getNewCurveData(charData, copyPropObj)
        elif(not cloneGlyphs):
            curveData = curveData.copy()
            
        if(copyPropObj != None and isBezier(copyPropObj)):
            obj = copyPropObj.copy()
            obj.name = 't'
            obj.matrix_world = Matrix()
            obj.data = curveData
            if(curveData.shape_keys != None):
                keyblocks = reversed(curveData.shape_keys.key_blocks)
                for sk in keyblocks:
                    obj.shape_key_remove(sk)            
        elif(isFlat):
            # Note: Changes to this should also reflect in getDCObjsForSpline
            # of writinganim_2_8
            for spline in curveData.splines:
                bpts = spline.bezier_points
                if(all([bpts[0].co[i] == bpts[0].handle_right[i] \
                    for i in range(3)])):
                    continue
                bpts.add(1)
                ptCnt = len(bpts)
                for i in range(0, (ptCnt - 1)):
                    idx = ptCnt - i - 2# reversed
                    copyObjAttr(bpts[idx], bpts[idx + 1])
                bpts[0].handle_right = bpts[0].co.copy()
                bpts[1].handle_left = bpts[1].co.copy()
                curveData.twist_mode = 'MINIMUM'
        else:
            curveData.bevel_depth = bevelDepth
            curveData.bevel_resolution = 0
            curveData.twist_smooth = 0
            curveData.twist_mode = 'Z_UP'
            
        obj = bpy.data.objects.new('t', curveData)
        
        curveData.dimensions = '3D'            
        obj.location = (0, 0, 0)
        return obj

#
# The following section is a Python conversion of the javascript
# a2c function at: https://github.com/fontello/svgpath
# (Copyright (C) 2013-2015 by Vitaly Puzrin)
#
######################## a2c start #######################

TAU = math.pi * 2

# eslint-disable space-infix-ops

# Calculate an angle between two unit vectors
#
# Since we measure angle between radii of circular arcs,
# we can use simplified math (without length normalization)
#
def unit_vector_angle(ux, uy, vx, vy):
    if(ux * vy - uy * vx < 0):
        sign = -1
    else:
        sign = 1
        
    dot  = ux * vx + uy * vy

    # Add this to work with arbitrary vectors:
    # dot /= math.sqrt(ux * ux + uy * uy) * math.sqrt(vx * vx + vy * vy)

    # rounding errors, e.g. -1.0000000000000002 can screw up this
    if (dot >  1.0): 
        dot =  1.0
        
    if (dot < -1.0):
        dot = -1.0

    return sign * math.acos(dot)


# Convert from endpoint to center parameterization,
# see http:#www.w3.org/TR/SVG11/implnote.html#ArcImplementationNotes
#
# Return [cx, cy, theta1, delta_theta]
#
def get_arc_center(x1, y1, x2, y2, fa, fs, rx, ry, sin_phi, cos_phi):
    # Step 1.
    #
    # Moving an ellipse so origin will be the middlepoint between our two
    # points. After that, rotate it to line up ellipse axes with coordinate
    # axes.
    #
    x1p =  cos_phi*(x1-x2)/2 + sin_phi*(y1-y2)/2
    y1p = -sin_phi*(x1-x2)/2 + cos_phi*(y1-y2)/2

    rx_sq  =  rx * rx
    ry_sq  =  ry * ry
    x1p_sq = x1p * x1p
    y1p_sq = y1p * y1p

    # Step 2.
    #
    # Compute coordinates of the centre of this ellipse (cx', cy')
    # in the new coordinate system.
    #
    radicant = (rx_sq * ry_sq) - (rx_sq * y1p_sq) - (ry_sq * x1p_sq)

    if (radicant < 0):
        # due to rounding errors it might be e.g. -1.3877787807814457e-17
        radicant = 0

    radicant /=   (rx_sq * y1p_sq) + (ry_sq * x1p_sq)
    factor = 1
    if(fa == fs):# Migration Note: note ===
        factor = -1
    radicant = math.sqrt(radicant) * factor #(fa === fs ? -1 : 1)

    cxp = radicant *  rx/ry * y1p
    cyp = radicant * -ry/rx * x1p

    # Step 3.
    #
    # Transform back to get centre coordinates (cx, cy) in the original
    # coordinate system.
    #
    cx = cos_phi*cxp - sin_phi*cyp + (x1+x2)/2
    cy = sin_phi*cxp + cos_phi*cyp + (y1+y2)/2

    # Step 4.
    #
    # Compute angles (theta1, delta_theta).
    #
    v1x =  (x1p - cxp) / rx
    v1y =  (y1p - cyp) / ry
    v2x = (-x1p - cxp) / rx
    v2y = (-y1p - cyp) / ry

    theta1 = unit_vector_angle(1, 0, v1x, v1y)
    delta_theta = unit_vector_angle(v1x, v1y, v2x, v2y)

    if (fs == 0 and delta_theta > 0):#Migration Note: note ===
        delta_theta -= TAU
    
    if (fs == 1 and delta_theta < 0):#Migration Note: note ===
        delta_theta += TAU    

    return [ cx, cy, theta1, delta_theta ]

#
# Approximate one unit arc segment with bezier curves,
# see http:#math.stackexchange.com/questions/873224
#
def approximate_unit_arc(theta1, delta_theta):
    alpha = 4.0/3 * math.tan(delta_theta/4)

    x1 = math.cos(theta1)
    y1 = math.sin(theta1)
    x2 = math.cos(theta1 + delta_theta)
    y2 = math.sin(theta1 + delta_theta)

    return [ x1, y1, x1 - y1*alpha, y1 + x1*alpha, x2 + y2*alpha, y2 - x2*alpha, x2, y2 ]

def a2c(x1, y1, x2, y2, fa, fs, rx, ry, phi):
    sin_phi = math.sin(phi * TAU / 360)
    cos_phi = math.cos(phi * TAU / 360)

    # Make sure radii are valid
    #
    x1p =  cos_phi*(x1-x2)/2 + sin_phi*(y1-y2)/2
    y1p = -sin_phi*(x1-x2)/2 + cos_phi*(y1-y2)/2

    if (x1p == 0 and y1p == 0): # Migration Note: note ===
        # we're asked to draw line to itself
        return []

    if (rx == 0 or ry == 0): # Migration Note: note ===
        # one of the radii is zero
        return []

    # Compensate out-of-range radii
    #
    rx = abs(rx)
    ry = abs(ry)

    lmbd = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if (lmbd > 1):
        rx *= math.sqrt(lmbd)
        ry *= math.sqrt(lmbd)


    # Get center parameters (cx, cy, theta1, delta_theta)
    #
    cc = get_arc_center(x1, y1, x2, y2, fa, fs, rx, ry, sin_phi, cos_phi)

    result = []
    theta1 = cc[2]
    delta_theta = cc[3]

    # Split an arc to multiple segments, so each segment
    # will be less than 90
    #
    segments = int(max(math.ceil(abs(delta_theta) / (TAU / 4)), 1))
    delta_theta /= segments

    for i in range(0, segments):
        result.append(approximate_unit_arc(theta1, delta_theta))

        theta1 += delta_theta
        
    # We have a bezier approximation of a unit circle,
    # now need to transform back to the original ellipse
    #
    return getMappedList(result, rx, ry, sin_phi, cos_phi, cc)

def getMappedList(result, rx, ry, sin_phi, cos_phi, cc):
    mappedList = []
    for elem in result:
        curve = []
        for i in range(0, len(elem), 2):
            x = elem[i + 0]
            y = elem[i + 1]

            # scale
            x *= rx
            y *= ry

            # rotate
            xp = cos_phi*x - sin_phi*y
            yp = sin_phi*x + cos_phi*y

            # translate
            elem[i + 0] = xp + cc[0]
            elem[i + 1] = yp + cc[1]        
            curve.append(complex(elem[i + 0], elem[i + 1]))
        mappedList.append(curve)
    return mappedList

######################### a2c end ########################

    

#
# The following section is an extract
# from svgpathtools (https://github.com/mathandy/svgpathtools)
# (Copyright (c) 2015 Andrew Allan Port, Copyright (c) 2013-2014 Lennart Regebro)
#
#################### svgpathtools start ###################


COMMANDS = set('MmZzLlHhVvCcSsQqTtAa')
UPPERCASE = set('MZLHVCSQTA')

COMMAND_RE = re.compile("([MmZzLlHhVvCcSsQqTtAa])")
FLOAT_RE = re.compile("[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")

def _tokenize_path(pathdef):
    for x in COMMAND_RE.split(pathdef):
        if x in COMMANDS:
            yield x
        for token in FLOAT_RE.findall(x):
            yield token

# Added for stroke font text
def getCBForQBPts(start, ctrl, end):
    cp0 = start
    cp3 = end

    cp1 = start + 2/3 * (ctrl - start)
    cp2 = end + 2/3 * (ctrl - end)
    
    return CubicBezier(cp0, cp1, cp2, cp3)
    
# Added for stroke font text
def getCBForArcPts(start, radius, rotation, large_arc, sweep, end):
    x1, y1 = start.real, start.imag
    x2, y2 = end.real, end.imag
    fa = large_arc
    fs = sweep
    rx, ry = radius.real, radius.imag
    phi = rotation
    curvesPts = a2c(x1, y1, x2, y2, fa, fs, rx, ry, phi)
    newPartSegs = []
    for curvePts in curvesPts:
        newPartSegs.append(CubicBezier(curvePts[0], curvePts[1], 
            curvePts[2], curvePts[3]))
    return newSegs
    

def parse_path(pathdef, current_pos=0j):

    elements = list(_tokenize_path(pathdef))

    elements.reverse()

    segments = []
    start_pos = None
    command = None

    while elements:

        if elements[-1] in COMMANDS:
            last_command = command
            command = elements.pop()
            absolute = command in UPPERCASE
            command = command.upper()
        else:
            if command is None:
                raise ValueError("Unallowed implicit command in %s, position %s" % (
                    pathdef, len(pathdef.split()) - len(elements)))

        if command == 'M':
            x = elements.pop()
            y = elements.pop()
            pos = float(x) + float(y) * 1j
            if absolute:
                current_pos = pos
            else:
                current_pos += pos

            start_pos = current_pos
            command = 'L'

        elif command == 'Z':
            if not (cmplxCmpWithMargin(current_pos, start_pos)):
                segments.append(CubicBezier(current_pos, current_pos, start_pos, start_pos))
            segments[-1].isClosing = True
            current_pos = start_pos
            start_pos = None
            command = None

        elif command == 'L':
            x = elements.pop()
            y = elements.pop()
            pos = float(x) + float(y) * 1j
            if not absolute:
                pos += current_pos
            segments.append(CubicBezier(current_pos, current_pos, pos, pos))
            current_pos = pos

        elif command == 'H':
            x = elements.pop()
            pos = float(x) + current_pos.imag * 1j
            if not absolute:
                pos += current_pos.real
            segments.append(CubicBezier(current_pos, current_pos, pos, pos))
            current_pos = pos

        elif command == 'V':
            y = elements.pop()
            pos = current_pos.real + float(y) * 1j
            if not absolute:
                pos += current_pos.imag * 1j
            segments.append(CubicBezier(current_pos, current_pos, pos, pos))
            current_pos = pos

        elif command == 'C':
            control1 = float(elements.pop()) + float(elements.pop()) * 1j
            control2 = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control1 += current_pos
                control2 += current_pos
                end += current_pos

            segments.append(CubicBezier(current_pos, control1, control2, end))
            current_pos = end

        elif command == 'S':
            if last_command not in 'CS':
                control1 = current_pos
            else:
                control1 = current_pos + current_pos - segments[-1].control2

            control2 = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control2 += current_pos
                end += current_pos

            segments.append(CubicBezier(current_pos, control1, control2, end))
            current_pos = end

        elif command == 'Q':
            control = float(elements.pop()) + float(elements.pop()) * 1j
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                control += current_pos
                end += current_pos

            segments.append(getCBForQBPts(current_pos, control, end))
            current_pos = end

        elif command == 'T':
            if last_command not in 'QT':
                control = current_pos
            else:
                control = current_pos + current_pos - segments[-1].control

            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments.append(getCBForQBPts(current_pos, control, end))
            current_pos = end

        elif command == 'A':
            radius = float(elements.pop()) + float(elements.pop()) * 1j
            rotation = float(elements.pop())
            arc = float(elements.pop())
            sweep = float(elements.pop())
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments += getCBForArcPts(current_pos, radius, rotation, arc, sweep, end)
            current_pos = end

    return segments

class CubicBezier(object):
    def __init__(self, start, control1, control2, end):
        self.start = start
        self.control1 = control1
        self.control2 = control2
        self.end = end
        self.isClosing = False

    def __eq__(self, other):
        if not isinstance(other, CubicBezier):
            return NotImplemented
        return self.start == other.start and self.end == other.end \
            and self.control1 == other.control1 \
            and self.control2 == other.control2

    def __ne__(self, other):
        if not isinstance(other, CubicBezier):
            return NotImplemented
        return not self == other

    def bpoints(self):
        return self.start, self.control1, self.control2, self.end

    def __getitem__(self, item):
        return self.bpoints()[item]

    def __len__(self):
        return 4

class Path:
    def __init__(self, segments, isClosed = False):
        self.segments = segments
        self.isClosed = isClosed
        
    def getBezierPtsInfo(self):
        prevSeg = None
        bezierPtsInfo = []

        for j, seg in enumerate(self.segments):
            
            pt = get3DVector(seg.start)
            handleRight = get3DVector(seg.control1)
            
            if(j == 0):
                if(self.isClosed):
                    handleLeft = get3DVector(self.segments[-1].control2)
                else:
                    handleLeft = pt
            else:
                handleLeft = get3DVector(prevSeg.control2)
                
            bezierPtsInfo.append([pt, handleLeft, handleRight])
            prevSeg = seg
    
        if(self.isClosed == True):
            bezierPtsInfo[-1][2] = get3DVector(seg.control1)
        else:
            bezierPtsInfo.append([get3DVector(prevSeg.end), \
                get3DVector(prevSeg.control2), get3DVector(prevSeg.end)])
                
        return bezierPtsInfo

#see https://stackoverflow.com/questions/24809978/calculating-the-bounding-box-of-cubic-bezier-curve
def getCBezierBBox(cbezier):
    def evalBez(AA, BB, CC, DD, t):
        return AA * (1 - t) * (1 - t) * (1 - t) + \
                3 * BB * t * (1 - t) * (1 - t) + \
                    3 * CC * t * t * (1 - t) + \
                        DD * t * t * t
    A = [cbezier.start.real, cbezier.start.imag]
    B = [cbezier.control1.real, cbezier.control1.imag]
    C = [cbezier.control2.real, cbezier.control2.imag]
    D = [cbezier.end.real, cbezier.end.imag]
    dim = 2
    
    MINXY = [min([A[i], D[i]]) for i in range(0, dim)]
    MAXXY = [max([A[i], D[i]]) for i in range(0, dim)]
    bbox = [MINXY, MAXXY]

    a = [3 * D[i] - 9 * C[i] + 9 * B[i] - 3 * A[i] for i in range(0, dim)]
    b = [6 * A[i] - 12 * B[i] + 6 * C[i] for i in range(0, dim)]
    c = [3 * (B[i] - A[i]) for i in range(0, dim)]

    solnsxyz = []
    for i in range(0, dim):
        solns = []
        if(a[i] == 0):
            if(b[i] == 0):
                solns.append(0)#Independent of t so lets take the starting pt
            else:
                solns.append(c[i] / b[i])
        else:
            rootFact = b[i] * b[i] - 4 * a[i] * c[i]
            if(rootFact >=0 ):
                #Two solutions with + and - sqrt
                solns.append((-b[i] + math.sqrt(rootFact)) / (2 * a[i]))
                solns.append((-b[i] - math.sqrt(rootFact)) / (2 * a[i]))
        solnsxyz.append(solns)

    for i, soln in enumerate(solnsxyz):
        for j, t in enumerate(soln):
            if(t < 1 and t > 0):
                co = evalBez(A[i], B[i], C[i], D[i], t)
                if(co < bbox[0][i]):
                    bbox[0][i] = co
                if(co > bbox[1][i]):
                    bbox[1][i] = co

    return bbox

##################### svgpathtools end ####################
