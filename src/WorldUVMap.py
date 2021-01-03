import bpy
from math import *

class WorldUVMap(bpy.types.Operator):
	bl_idname = "mesh.world_uv_map"
	bl_label = "World UV Map"
	
	unitsPerMeter = bpy.props.FloatProperty(default=1, min=0, max=1000, soft_min=0, soft_max=1000)
	
	def execute(self, context):
		print("#######################")
		
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
		bpy.ops.object.mode_set(mode='OBJECT')
		
		mesh = bpy.context.selected_objects[0].data
		uvdata = mesh.uv_layers.active.data
		
		# Required "UV Magic" addon to be enabled in preferences
		#if callable(bpy.ops.uv.muv_world_scale_uv_apply_manual):
		#	bpy.ops.object.mode_set(mode='EDIT')
		#	bpy.ops.uv.muv_world_scale_uv_apply_manual(tgt_density=1, origin='LEFT_BOTTOM', tgt_texture_size=(1, 2))
		#	return {'FINISHED'}
		
		# calculate average edge length
		totalworlddist = 0
		totaluvdist = 0
		totalcount = 0
		for poly in mesh.polygons:
			for i in range(len(poly.loop_indices) - 1):
				# world dist
				pos1 = mesh.vertices[mesh.loops[i + 0].vertex_index].co
				pos2 = mesh.vertices[mesh.loops[i + 1].vertex_index].co
				offset = [pos2[0] - pos1[0], pos2[1] - pos1[1], pos2[2] - pos1[2]]
				worlddist = sqrt(offset[0]**2 + offset[1]**2 + offset[2]**2)
				
				# uv dist
				uv1 = uvdata[poly.loop_indices[i + 0]].uv
				uv2 = uvdata[poly.loop_indices[i + 1]].uv
				offset = [uv2[0] - uv1[0], uv2[1] - uv1[1]]
				uvdist = sqrt(offset[0]**2 + offset[1]**2)
				
				# total
				totalworlddist = totalworlddist + worlddist
				totaluvdist = totaluvdist + uvdist
				totalcount = totalcount + 1
		
		if totalcount == 0:
			return {'FINISHED'}
		
		worldaveragedist = totalworlddist / totalcount
		uvaveragedist = totaluvdist / totalcount
		scale = worldaveragedist / uvaveragedist
		print(scale)
		print("########## " + str(worldaveragedist))
		
		# scale uvs
		for uv in mesh.uv_layers.active.data:
			uv.uv[0] = uv.uv[0] * scale
			uv.uv[1] = uv.uv[1] * scale
		
		bpy.ops.object.mode_set(mode='EDIT')
		
		return {'FINISHED'}

bpy.utils.register_class(WorldUVMap)
