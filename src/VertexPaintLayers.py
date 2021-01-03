# <pep8 compliant>

bl_info = {
	"name": "Vertex Paint Layers",
	"description": "Paint vertex colors with a photoshop-style layering stack.",
	"author": "Brendan Keesing",
	"version": (1, 0),
	"blender": (2, 8, 0),
	"location": "Vertex Paint | View3D > Vertex Paint Layer",
	"support": "COMMUNITY",
	"category": "Paint"
}

import bpy
import json

###
### BLEND MODES
###

def BlendModeNormal(a, b):
	return b

def BlendModeMultiply(a, b):
	return a * b

def BlendModeDarken(a, b):
	return min(a, b)

def BlendModeColorBurn(a, b):
	if b == 0:
		return 0
	else:
		return 1 - (1 - a) / b

def BlendModeLinearBurn(a, b):
	return a + b - 1

def BlendModeLighten(a, b):
	return max(a, b)

def BlendModeScreen(a, b):
	return 1 - (1 - a) * (1 - b)

def BlendModeColorDodge(a, b):
	if b == 1:
		return 0
	else:
		return a / (1 - b)

def BlendModeLinearDodge(a, b):
	return a + b

def BlendModeOverlay(a, b):
	if a > 0.5:
		return 1 - (1 - 2 * (a - 0.5)) * (1 - b)
	else:
		return 2 * a * b

def BlendModeSubtract(a, b):
	return a - b

def BlendModeDifference(a, b):
	return abs(a - b)

def BlendModeExclusion(a, b):
	return 0.5 - 2 * (a - 0.5) * (b - 0.5)

blendModes = [
	BlendModeNormal,
	BlendModeMultiply,
	BlendModeDarken,
	BlendModeColorBurn,
	BlendModeLinearBurn,
	BlendModeLighten,
	BlendModeScreen,
	BlendModeColorDodge,
	BlendModeLinearDodge,
	BlendModeOverlay,
	BlendModeSubtract,
	BlendModeDifference,
	BlendModeExclusion
]
blendModeEnum = [
	("NML", "Normal", ""),
	("MUL", "Multiply", ""),
	("DRK", "Darken", ""),
	("CBR", "Color Burn", ""),
	("LBR", "Linear Burn", ""),
	("LTN", "Lighten", ""),
	("SCR", "Screen", ""),
	("CDO", "Color Dodge", ""),
	("LDO", "Linear Dodge", ""),
	("OVR", "Overlay", ""),
	("SUB", "Subtract", ""),
	("DIF", "Difference", ""),
	("EXC", "Exclusion", "")
]

###
### DRAWING
###

def Lerp(a, b, t):
	return (b - a) * t + a

def BlendLayers(mesh, layer1, layer2, destination, blendmodeidx, amount):
	mixfunc = blendModes[blendmodeidx]
	for poly in mesh.polygons:
		for loopindex in poly.loop_indices:
			colorA = layer1.data[loopindex].color
			colorB = layer2.data[loopindex].color
			
			blendamount = amount * colorB[3]
			destination.data[loopindex].color = [
				Lerp(colorA[0], mixfunc(colorA[0], colorB[0]), blendamount),
				Lerp(colorA[1], mixfunc(colorA[1], colorB[1]), blendamount),
				Lerp(colorA[2], mixfunc(colorA[2], colorB[2]), blendamount),
				max(colorA[3], colorB[3])
			]

def FillLayer(mesh, destination, color):
	for poly in mesh.polygons:
		for loopindex in poly.loop_indices:
			destination.data[loopindex].color = color

def CopyLayer(mesh, source, destination):
	for poly in mesh.polygons:
		for loopindex in poly.loop_indices:
			destination.data[loopindex].color = source.data[loopindex].color

###
### API
###

_lastMesh = None
_lastDict = None

def VPL_GetSelectedMesh():
	return bpy.context.object.data

def VPL_GetSelectedVertexColorGroup():
	return VPL_GetSelectedMesh().vertex_colors.active

def VPL_SelectVertexColorGroup(group):
	vc = VPL_GetSelectedMesh().vertex_colors
	vc.active_index = vc.find(group.name)

def VPL_FindVertexColorGroup(id):
	for colorlayer in VPL_GetSelectedMesh().vertex_colors:
		if colorlayer.name == id:
			return colorlayer
	return None

def VPL_GetDict():
	global _lastMesh
	global _lastDict
	
	mesh = VPL_GetSelectedMesh()
	if mesh == None:
		return None
	if mesh == _lastMesh:
		return _lastDict
	_lastMesh = mesh
	_lastDict = mesh.get("_VPL")
	if isinstance(_lastDict, str):
		_lastDict = json.loads(_lastDict)
	return _lastDict

def VPL_SetDict(dict):
	global _lastMesh
	global _lastDict
	
	if dict == None:
		return
	
	mesh = VPL_GetSelectedMesh()
	if mesh == None:
		return
	_lastMesh = mesh
	_lastDict = dict
	mesh["_VPL"] = json.dumps(_lastDict)

def VPL_SaveDict():
	VPL_SetDict(VPL_GetDict())

def VPL_IsSetup():
	return VPL_GetDict() != None

def VPL_Reset():
	VPL_SetDict({ "outputID": "_output", "selectedID": "", "isPaintMode": True, "layers": [] })
	
	# make sure output layer exists
	dict = VPL_GetDict()
	if VPL_FindVertexColorGroup(dict["outputID"]) == None:
		lastselected = VPL_GetSelectedVertexColorGroup()
		bpy.ops.mesh.vertex_color_add()
		VPL_GetSelectedVertexColorGroup().name = dict["outputID"]
		VPL_SelectVertexColorGroup(lastselected)

def VPL_CreateFromSelectedColorLayer():
	newlayer = {
		"layerID": VPL_GetSelectedMesh().vertex_colors.active.name,
		"blendMode": 0,
		"blendAmount": 1,
		"isVisible": True
	}
	list = VPL_GetDict()["layers"].append(newlayer)
	VPL_SelectLayer(newlayer)
	return newlayer

def VPL_CreateLayer():
	bpy.ops.mesh.vertex_color_add()
	FillLayer(VPL_GetSelectedMesh(), VPL_GetSelectedVertexColorGroup(), [1, 1, 1, 1])
	return VPL_CreateFromSelectedColorLayer()

def VPL_DeleteLayer(layer):
	group = VPL_FindVertexColorGroup(VPL_GetLayerID(layer))
	lastselected = None
	if group != VPL_GetSelectedVertexColorGroup():
		lastselected = group
	VPL_SelectVertexColorGroup(group)
	bpy.ops.mesh.vertex_color_remove()
	VPL_GetAllLayers().remove(layer)
	if lastselected != None:
		VPL_SelectVertexColorGroup(lastselected)
	elif VPL_GetLayerCount() == 0:
		VPL_GetDict()["selectedID"] = ""
		VPL_SaveDict()
	else:
		VPL_SelectLayer(VPL_GetAllLayers()[0])

def VPL_GetOutputLayer():
	return VPL_FindVertexColorGroup(VPL_GetDict()["outputID"])

def VPL_GetAllLayers():
	return VPL_GetDict()["layers"]

def VPL_FindLayer(layerid):
	dict = VPL_GetDict()
	for layer in VPL_GetAllLayers():
		if VPL_GetLayerID(layer) == layerid:
			return layer
	return None

def VPL_GetSelectedLayer():
	layer = VPL_FindLayer(VPL_GetDict()["selectedID"])
	if layer == None and VPL_GetLayerCount() > 0:
		layer = VPL_GetAllLayers()[0]
		VPL_GetDict()["selectedID"] = VPL_GetLayerID(layer)
	return layer
	
def VPL_SelectLayer(layer):
	VPL_GetDict()["selectedID"] = VPL_GetLayerID(layer)
	VPL_SaveDict()
	
	# select vertex color group
	if VPL_IsPaintMode():
		VPL_SelectVertexColorGroup(VPL_FindVertexColorGroup(VPL_GetLayerID(layer)))
	
	VPL_DrawOutput()

def VPL_IsLayerSetup(colorgroup):
	return VPL_FindLayer(colorgroup.name) == None and colorgroup.name != VPL_GetDict()["outputID"]

def VPL_GetIndexOfLayer(layer):
	return VPL_GetAllLayers().index(layer)

def VPL_GetLayerCount():
	return len(VPL_GetAllLayers())

def VPL_MoveLayer(layer, newindex):
	layers = VPL_GetAllLayers()
	layers.insert(newindex, layers.pop(VPL_GetIndexOfLayer(layer)))
	VPL_SaveDict()
	VPL_DrawOutput()

def VPL_IsOutputLayerSelected():
	return VPL_GetSelectedVertexColorGroup().name == VPL_GetDict()["outputID"]

def VPL_IsPaintMode():
	return VPL_GetDict()["isPaintMode"]

def VPL_SetPaintMode(enable):
	VPL_GetDict()["isPaintMode"] = enable
	VPL_SaveDict()
	
	if enable:
		VPL_SelectVertexColorGroup(VPL_FindVertexColorGroup(VPL_GetLayerID(VPL_GetSelectedLayer())))
	else:
		VPL_SelectVertexColorGroup(VPL_GetOutputLayer())
	VPL_DrawOutput()

def VPL_GetLayerID(layer):
	return layer["layerID"]

def VPL_SetLayerID(layer, newid):
	isselected = VPL_GetSelectedLayer() == layer
	group = VPL_FindVertexColorGroup(VPL_GetLayerID(layer))
	if group != None:
		group.name = newid
	layer["layerID"] = newid
	if isselected:
		VPL_GetDict()["selectedID"] = newid
	VPL_SaveDict()
	VPL_DrawOutput()

def VPL_GetBlendMode(layer):
	return layer["blendMode"]

def VPL_SetBlendMode(layer, mode):
	layer["blendMode"] = mode
	VPL_SaveDict()
	VPL_DrawOutput()

def VPL_GetBlendAmount(layer):
	return layer["blendAmount"]

def VPL_SetBlendAmount(layer, amount):
	layer["blendAmount"] = amount
	VPL_SaveDict()
	VPL_DrawOutput()

def VPL_IsLayerVisible(layer):
	return layer["isVisible"]

def VPL_SetLayerVisible(layer, visible):
	layer["isVisible"] = visible
	VPL_SaveDict()
	VPL_DrawOutput()

def VPL_DrawOutput():
	if VPL_IsPaintMode():
		return
	
	dict = VPL_GetDict()
	mesh = VPL_GetSelectedMesh()
	outputgroup = VPL_FindVertexColorGroup(dict["outputID"])
	hasdonefirstlayer = False
	for layer in reversed(VPL_GetAllLayers()):
		if not VPL_IsLayerVisible(layer):
			continue
		
		layergroup = VPL_FindVertexColorGroup(VPL_GetLayerID(layer))
		if layergroup == None:
			continue # this means there is a problem, but shouldn't be fatal
		
		if not hasdonefirstlayer:
			hasdonefirstlayer = True
			CopyLayer(mesh, layergroup, outputgroup)
		else:
			BlendLayers(mesh, outputgroup, layergroup, outputgroup, VPL_GetBlendMode(layer), VPL_GetBlendAmount(layer))
			lastgroup = outputgroup
	
	# if nothing was set, set it all to black
	if not hasdonefirstlayer:
		FillLayer(mesh, outputgroup, [0, 0, 0, 0])

###
### CALLBACKS
###

def CallbackIsPaintMode(self):
	return VPL_IsPaintMode()

def CallbackSetPaintMode(self, enable):
	VPL_SetPaintMode(enable)

def CallbackGetLayerID(self):
	return VPL_GetLayerID(VPL_GetSelectedLayer())
	
def CallbackSetLayerID(self, value):
	VPL_SetLayerID(VPL_GetSelectedLayer(), value)

def CallbackGetBlendMode(self):
	return VPL_GetBlendMode(VPL_GetSelectedLayer())
	
def CallbackSetBlendMode(self, value):
	VPL_SetBlendMode(VPL_GetSelectedLayer(), value)

def CallbackGetBlendAmount(self):
	return VPL_GetBlendAmount(VPL_GetSelectedLayer())

def CallbackSetBlendAmount(self, value):
	VPL_SetBlendAmount(VPL_GetSelectedLayer(), value)

###
### OPERATORS
###

class VertexPaintLayerSetupOperator(bpy.types.Operator):
	bl_idname = "mesh.vpl_setup_layer"
	bl_label = "Setup Layer"
	
	def execute(self, context):
		if not VPL_IsSetup():
			VPL_Reset()
		VPL_CreateFromSelectedColorLayer()
		return {'FINISHED'}

class VertexPaintLayerSetLayer(bpy.types.Operator):
	bl_idname = "mesh.vpl_set_layer"
	bl_label = "Set Vertex Layer"
	
	layerID = bpy.props.StringProperty()
	
	def execute(self, context):
		VPL_SelectLayer(VPL_FindLayer(self.layerID))
		return {'FINISHED'}

class VertexPaintLayerSetVisibile(bpy.types.Operator):
	bl_idname = "mesh.vpl_set_visible"
	bl_label = "Set Visible"
	
	layerID = bpy.props.StringProperty()
	visible = bpy.props.BoolProperty()
	
	def execute(self, context):
		VPL_SetLayerVisible(VPL_FindLayer(self.layerID), self.visible)
		return {'FINISHED'}

class VertexPaintLayerMoveLayer(bpy.types.Operator):
	bl_idname = "mesh.vpl_move_layer"
	bl_label = "Set Vertex Layer"
	
	layerID = bpy.props.StringProperty()
	newIndex = bpy.props.IntProperty()
	
	def execute(self, context):
		VPL_MoveLayer(VPL_FindLayer(self.layerID), self.newIndex)
		return {'FINISHED'}

class VertexPaintLayerCreateLayer(bpy.types.Operator):
	bl_idname = "mesh.vpl_create_layer"
	bl_label = "Add Vertex Layer"
	
	def execute(self, context):
		VPL_CreateLayer()
		return {'FINISHED'}

class VertexPaintLayerDeleteLayer(bpy.types.Operator):
	bl_idname = "mesh.vpl_delete_layer"
	bl_label = "Delete Vertex Layer"
	
	layerID = bpy.props.StringProperty()
	
	def execute(self, context):
		VPL_DeleteLayer(VPL_FindLayer(self.layerID))
		return {'FINISHED'}

###
### PANELS
###

class VertexPaintLayerPanel(bpy.types.Panel):
	bl_idname = "VertexPaintLayer"
	bl_label = "Vertex Paint Layer"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_context = "vertexpaint"
	bl_category = "View"
	
	bpy.types.Object.paintMode = bpy.props.BoolProperty(get=CallbackIsPaintMode, set=CallbackSetPaintMode)
	bpy.types.Object.blendMode = bpy.props.EnumProperty(items=blendModeEnum, get=CallbackGetBlendMode, set=CallbackSetBlendMode)
	bpy.types.Object.blendAmount = bpy.props.FloatProperty(default=1, min=0, max=1, soft_min=0, soft_max=1, get=CallbackGetBlendAmount, set=CallbackSetBlendAmount)
	bpy.types.Object.layerID = bpy.props.StringProperty(get=CallbackGetLayerID, set=CallbackSetLayerID)
	
	def draw(self, context):
		layout=self.layout
		
		# setup options
		if not VPL_IsSetup() or VPL_IsLayerSetup(VPL_GetSelectedVertexColorGroup()):
			layout.operator("mesh.vpl_setup_layer")
			return
		
		# top options
		togglelabel = "PAINT MODE"
		if VPL_IsPaintMode():
			togglelabel = "PAINT MODE"
		else:
			togglelabel = "VIEW MODE"
		
		layout.prop(context.object, "paintMode", text=togglelabel, toggle=True)
		
		column = layout.column()
		column.active = VPL_GetLayerCount() > 0 and VPL_GetIndexOfLayer(VPL_GetSelectedLayer()) != VPL_GetLayerCount() - 1
		column.prop(context.object, "blendMode", text="Mode")
		column.prop(context.object, "blendAmount", text="Amount", slider=True)
		
		# list
		row = layout.row()
		
		# layer list
		box = row.box()
		for layer in VPL_GetAllLayers():
			layerrow = box.row()
			
			iconid = "CHECKBOX_HLT" if VPL_GetSelectedLayer() == layer else "CHECKBOX_DEHLT"
			opie = layerrow.operator("mesh.vpl_set_layer", icon=iconid, text=VPL_GetLayerID(layer))
			opie.layerID = VPL_GetLayerID(layer)
			
			isvisible = VPL_IsLayerVisible(layer)
			iconid = "HIDE_OFF" if isvisible else "HIDE_ON"
			opie = layerrow.operator("mesh.vpl_set_visible", icon=iconid, text="")
			opie.layerID = VPL_GetLayerID(layer)
			opie.visible = not isvisible
		
		# list side options
		column = row.column()
		
		opie = column.operator("mesh.vpl_create_layer", icon="ADD", text="")
		
		holder = column.row()
		holder.active = VPL_GetSelectedLayer() != None
		opie = holder.operator("mesh.vpl_delete_layer", icon="REMOVE", text="")
		if holder.active:
			opie.layerID = VPL_GetLayerID(VPL_GetSelectedLayer())
		
		holder = column.row()
		holder.active = VPL_GetLayerCount() > 0 and VPL_GetIndexOfLayer(VPL_GetSelectedLayer()) > 0
		opie = holder.operator("mesh.vpl_move_layer", icon="TRIA_UP", text="")
		if holder.active:
			opie.layerID = VPL_GetLayerID(VPL_GetSelectedLayer())
			opie.newIndex = VPL_GetIndexOfLayer(VPL_GetSelectedLayer()) - 1
		
		holder = column.row()
		holder.active = VPL_GetLayerCount() > 0 and VPL_GetIndexOfLayer(VPL_GetSelectedLayer()) < VPL_GetLayerCount() - 1
		opie = holder.operator("mesh.vpl_move_layer", icon="TRIA_DOWN", text="")
		if holder.active:
			opie.layerID = VPL_GetLayerID(VPL_GetSelectedLayer())
			opie.newIndex = VPL_GetIndexOfLayer(VPL_GetSelectedLayer()) + 1
		
		# selected layer options
		if VPL_GetSelectedLayer() != None:
			layout.prop(context.object, "layerID", text="Name")
			
			if VPL_FindVertexColorGroup(VPL_GetSelectedLayer()["layerID"]) == None:
				layout.label(text="MISSING VERTEX COLOR GROUP WITH THIS NAME!", icon="ERROR")

###
### REGISTER
###

classes = (
	# operators
	VertexPaintLayerSetupOperator,
	VertexPaintLayerSetLayer,
	VertexPaintLayerSetVisibile,
	VertexPaintLayerMoveLayer,
	VertexPaintLayerCreateLayer,
	VertexPaintLayerDeleteLayer,
	
	# panels
	VertexPaintLayerPanel
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
	register()
