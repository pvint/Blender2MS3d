# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2004-2015: Paul Vint pjvint@gmail.com

"""
This script exports Milkshape text files from Blender. It supports normals,
colours, and texture coordinates per face or per vertex.
Only one mesh can be exported at a time.
"""

import bpy
import os

DEBUG = True

def getPrimaryVertexGroup(_vgroups, _v):
	g = -1
	w = 0
	## Scan through any vertex groups and return the index of the one with the highest weight (or -1 if none)
	for vertgroup in _v.groups:
		if (vertgroup.weight > w):
			w = vertgroup.weight
			g = vertgroup.group
		#fw("xx%fxx" % vertgroup.group)

	return g

def face_iter_func(mesh):
	uv_layer = mesh.uv_textures.active.data
	uv_layer_len = len(uv_layer)

	faces = mesh.faces

	for i in range(uv_layer_len):
		uv_elem = uv_layer[i]
		yield (i, uv_layer[i].uv)

def save(operator,
		 context,
		 filepath="",
		 use_modifiers=True,
		 use_normals=True,
		 use_uv_coords=True,
		 use_colors=True,
		 ):

	def rvec3d(v):
		return round(v[0], 6), round(v[1], 6), round(v[2], 6)

	def rvec2d(v):
		return round(v[0], 6), round(v[1], 6)

	scene = context.scene
	obj = context.active_object

	if not obj:
		raise Exception("Error, Select 1 active object")

	# Multiple meshes
	objects = context.selected_objects


	file = open(filepath, "w", encoding="utf8", newline="\n")
	fw = file.write
	fw("// Milkshape 3D ASCII\n\n")
	fw("Frames: 30\n")
	fw("Frame: 1\n\n")


	if scene.objects.active:
		bpy.ops.object.mode_set(mode='OBJECT')

	

	o = 0
	numArmatures = 0
	numMeshes = 0

	# count the meshes
	for obj in objects:
		if obj.type == "MESH":
			numMeshes = numMeshes + 1
	
	fw("Meshes: %d\n" % numMeshes)

	for obj in objects: 
		## Check if it's an armature
		if obj.type == "ARMATURE":
			numArmatures = numArmatures + 1
		else:
			if use_modifiers:
				mesh = obj.to_mesh(scene, True, 'PREVIEW')
			else:
				mesh = obj.data

			if not mesh:
				raise Exception("Error, could not get mesh data from active object")

			# mesh.transform(obj.matrix_world) # XXX



			has_uv = (len(mesh.uv_textures) > 0)
			has_uv_vertex = (len(mesh.sticky) > 0)

			# FIXME
			#has_uv = True

			has_vcol = len(mesh.vertex_colors) > 0

			#if (not has_uv) and (not has_uv_vertex):
			#	use_uv_coords = False
			if not has_vcol:
				use_colors = False

			if not use_uv_coords:
				has_uv = has_uv_vertex = False
			if not use_colors:
				has_vcol = False

			if has_uv:
				active_uv_layer = mesh.uv_textures.active
				if not active_uv_layer:
					use_uv_coords = False
					has_uv = False
				else:
					active_uv_layer = active_uv_layer.data

			if False:	# Testing
				for i, uv in face_iter_func(mesh):
					fw("%d %f \n" % (i, uv[0][0]))

				return True

			## Get UV list
			if has_uv:
				faceUVs = []
				for i, uv in face_iter_func(mesh):
					faceUVs.append(uv)

			if has_vcol:
				active_col_layer = mesh.vertex_colors.active
				if not active_col_layer:
					use_colors = False
					has_vcol = False
				else:
					active_col_layer = active_col_layer.data

			# in case
			color = uvcoord = uvcoord_key = normal = normal_key = None

			mesh_verts = mesh.vertices  # save a lookup
			ply_verts = []  # list of dictionaries
			# vdict = {} # (index, normal, uv) -> new index
			vdict = [{} for i in range(len(mesh_verts))]
			ply_faces = [[] for f in range(len(mesh.faces))]
			vert_count = 0

			## Vertex Group Testing
			
			vGroups = []
			vGroupsIndices = []
			if (obj.vertex_groups):
				for x in obj.vertex_groups:
					#fw("=%d %s\n" % (x.index, x.name))
					vGroups.append({x.index, x.name})
					vGroupsIndices.append(x.index)
				## Yielded:
				#0 Bone
				#1 Bone.002
				#2 Bone.001




			for i, f in enumerate(mesh.faces):

				# GOOD: fw("Verts: %d %d %d\n" % (f.vertices[0], f.vertices[1], f.vertices[2]))
				smooth = f.use_smooth
				if not smooth:
					normal = tuple(f.normal)
					normal_key = rvec3d(normal)

				if has_uv:
					uv = active_uv_layer[i]
					uv = uv.uv1, uv.uv2, uv.uv3, uv.uv4  # XXX - crufty :/
				if has_vcol:
					col = active_col_layer[i]
					col = col.color1[:], col.color2[:], col.color3[:], col.color4[:]

				f_verts = f.vertices

				pf = ply_faces[i]
				## FIXME Deprecated
				for j, vidx in enumerate(f_verts):
					v = mesh_verts[vidx]

					if smooth:
						normal = tuple(v.normal)
						normal_key = rvec3d(normal)

					if has_uv:
						uvcoord = uv[j][0], 1.0 - uv[j][1]
						uvcoord_key = rvec2d(uvcoord)
					elif has_uv_vertex:
						uvcoord = v.uvco[0], 1.0 - v.uvco[1]
						uvcoord_key = rvec2d(uvcoord)

					if has_vcol:
						color = col[j]
						color = (int(color[0] * 255.0),
								 int(color[1] * 255.0),
								 int(color[2] * 255.0),
								 )
					key = normal_key, uvcoord_key, color

					vdict_local = vdict[vidx]
					pf_vidx = vdict_local.get(key)  # Will be None initially

					if pf_vidx is None:  # same as vdict_local.has_key(key)
						pf_vidx = vdict_local[key] = vert_count
						ply_verts.append((vidx, normal, uvcoord, color))
						vert_count += 1

					pf.append(pf_vidx)

			# Mesh name, flags, material index
			fw("\"%s\" 0 %d\n" % (obj.name, o))

			#fw("%d\n" % (len(mesh.faces) * 3)) 

			#if use_colors:
			#	fw("property uchar red\n"
			#	   "property uchar green\n"
			#	   "property uchar blue\n")

			#fw("element face %d\n" % len(mesh.faces))
			#fw("property list uchar uint vertex_indices\n")
			#fw("end_header\n")

			# mesh.vertices is array of vertex coords
			# face.vertices is array of vertex indices
			# to get unique vertices in the file create an array of all vertices and
			# then find the highest index in the list of faces and use only up to 
			# that one to only have unique vertices
			maxIndex = 0
			numVerts = 0
			for f in mesh.faces:
				for v in f.vertices:
					numVerts = numVerts + 1
					if (v >= maxIndex):
						maxIndex = v

			maxIndex = maxIndex + 1
			#fw("%d\n" % (maxIndex))

			## create array of verts
			vco = []
			fverts = []

			## make a properly ordered list of vertices
			for f in mesh.faces:
				for v in mesh.vertices:
					fverts.append(v)

				
			### The following method is crap - need to duplicate verts for when they have different
			###  UV coords for different faces!
			#for i in range(0, maxIndex):
				#fw("0 %.4f %.4f %.4f " % (-fverts[i].co[0], fverts[i].co[2], -fverts[i].co[1]))
				#fw('0.0, 0.0')  # uv
				# Vertex Group
				#vg = getPrimaryVertexGroup(vGroups, fverts[i])

				#fw(" %d\n" % vg)



			## Prep for UVs
			activeUV = mesh.uv_textures[0].data
			#if has_uv:
			#	actuveUV = mesh.uv_textures

			### Dump each vert on each face
			fw("%d\n" % numVerts)
			fIdx = 0
			for f in mesh.faces:
				if (len(f.vertices) != 3):
					raise Exception("Error! All faces must be triangles. (Convert in edit mode by pressing CTRL-t)")
				
				## Loop through each vertex in the face
				vIdx = 0

				uv = activeUV[fIdx]
				fuv = uv.uv1, uv.uv2, uv.uv3

				

				for v in f.vertices:
					fw("0 %.4f %.4f %.4f " % (-fverts[v].co[0], fverts[v].co[2], -fverts[v].co[1]))

					## uv coords
					#for i, uv in face_iter_func(mesh):
					#fw("%d %f \n" % (i, uv[0][0]))

					if has_uv:
						fw("%.4f %.4f " % (faceUVs[fIdx][vIdx][0], 1.0 - faceUVs[fIdx][vIdx][1]))
						#fw("%.4f %.4f " % (fverts[v].uv[0], 1 - fverts[v].uv[1]))
					else:
						fw("0.0000 0.0000 ");

					## Vertex Group
					if not obj.vertex_groups:
						vg = -1
					else:
						vg = getPrimaryVertexGroup(vGroups, fverts[v])
					fw("%d\n" % vg)
					vIdx = vIdx + 1
				fIdx = fIdx + 1

			# Repeat the above loop to get vertex normals
			fw("%d\n" % numVerts)
			for f in mesh.faces:
				## Test if using smoothing or not
				if f.use_smooth:
					## Loop through each vertex in the face
					for v in f.vertices:
						fw("%.4f %.4f %.4f\n" % (-fverts[v].normal[0], fverts[v].normal[2], -fverts[v].normal[1]))
				else:
					for v in f.vertices:
						fw("%.4f %.4f %.4f\n" % (-f.normal[0], f.normal[2], -f.normal[1]))


			# Get Face info
			# TODO: Smoothing groups
			# A bit BFI, but vertices are in order
			fw("%d\n" % len(ply_faces))
			v = 0
			for f in mesh.faces:
				fw("1 %d %d %d" % (v + 2, v + 1, v))
				fw(" %d %d %d 1\n" % (v + 2, v + 1, v))
			
				v = v + 3
		  
			o = o + 1




	## Materials
	# Note: Limiting to one mat per mesh, and assuming every mesh has one
	world = scene.world
	if world:
		world_amb = world.ambient_color
	else:
		world_amb = Color((0.0, 0.0, 0.0))


	fw("\nMaterials: %d\n" % o)
	o = 0
	for obj in objects:
		if obj.type != "ARMATURE":
			materials = obj.data.materials[:]
			mat = materials[0]
			fw("\"Mat%d\"\n" % o)

			## ambient 
			fw('%.6f %.6f %.6f 1.000000\n' % (mat.diffuse_color * mat.ambient)[:])
			## Diffues
			fw("%.6f %.6f %.6f 1.000000\n" % (mat.diffuse_intensity * mat.diffuse_color)[:]) 
			fw("%.6f %.6f %.6f 1.000000\n" % (mat.specular_intensity * mat.specular_color)[:])  # Specular
			fw('%.6f %.6f %.6f 1.000000\n' % (mat.diffuse_color * mat.emit)[:])
			fw("%.6f\n" % mat.specular_hardness)
			fw("%.6f\n" % mat.alpha)

			if (len(obj.data.uv_textures) > 0):
				uv_layer = obj.data.uv_textures.active.data[:]
				uv_image = uv_layer[0].image
				if (uv_image):
					fw("\"%s\"\n" % uv_image.filepath)
				else:
					fw("\"\"\n")
			else:
				fw("\"\"\n")

			# TODO: Alpha texture
			fw("\"\"\n")

			o = o + 1

	fw("\n")

	#fw("Bones: %d\n" % numArmatures)
	numBones = 0
	# count the bones
	for obj in objects:
		if obj.type == "ARMATURE":
			for b in obj.pose.bones:
				numBones = numBones + 1

	fw("Bones: %d\n" % numBones)

	# export the bones
	for obj in objects:
		if obj.type == "ARMATURE":
			for b in obj.pose.bones:

				## Give the file the bone!
				## Bone Name
				fw("\"%s\"\n" % b.name)
				## Parent Name
				if (len(b.parent_recursive) > 0 ):
					fw("\"%s\"\n" % b.parent.name)
				else:
					fw("\"\"\n")

				## // joint: flags, posx, posy, posz, rotx, roty, rotz
				## Looking at examples the flag appears to always be 24 (?)
				## Not sure how to get rot - skip it for now
				fw("24 %.6f %.6f %.6f 0 0 0\n" % ( -b.head[0], b.head[2], -b.head[1]))

				## Number of position keys - using the number of frames in the anim sequence
				fw("%d\n" % (scene.frame_end - scene.frame_start))

				## FIXME Not sure how to handle time, just doing 1 sec per frame for now
				secs = 1

				## // position key: time, posx, posy, posz
				for frame in range(scene.frame_start, scene.frame_end):
					## Go to the first frame
					scene.frame_set(frame)
					fw("%.6f %.6f %.6f %.6f\n" % ( secs, -b.tail[0], b.tail[2], -b.tail[1]))
					secs = secs + 1

				### Rotation Keys
				# Just using number of frames for now with rots all 0.0
				fw("%d\n" % (scene.frame_end - scene.frame_start))
				for frame in range(scene.frame_start, scene.frame_end):
					fw("%d 0.000000 0.000000 0.000000\n" % secs)

				## End of this bone
				fw("\n")



	fw("GroupComments: 0\n")
	fw("MaterialComments: 0\n")
	fw("BoneComments: 0\n")
	fw("ModelComment: 0\n")

	file.close()
	print("writing %r done" % filepath)

	if use_modifiers:
		bpy.data.meshes.remove(mesh)

	# XXX
	"""
	if is_editmode:
		Blender.Window.EditMode(1, "", 0)
	"""

	return {'FINISHED'}
