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

# <pep8-80 compliant>

bl_info = {
    "name": "Milkshape 3d format",
    "author": "Paul Vint",
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "File > Import-Export",
    "description": "Export MS3d Format",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Import-Export/MS3D",
    "tracker_url": "",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

import os
import bpy
from bpy.props import CollectionProperty, StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


class ExportMS3D(bpy.types.Operator, ExportHelper):
    '''Export a single object as MS3d, ''' 
    bl_idname = "export_ms3d.ms3d"
    bl_label = "Export MS3D"

    filename_ext = ".txt"
    filter_glob = StringProperty(default="*.txt", options={'HIDDEN'})

    use_modifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply Modifiers to the exported mesh",
            default=True,
            )
    use_normals = BoolProperty(
            name="Normals",
            description="Export Normals for smooth and hard shaded faces",
            default=True,
            )
    use_uv_coords = BoolProperty(
            name="UVs",
            description="Export the active UV layer",
            default=True,
            )
    use_colors = BoolProperty(
            name="Vertex Colors",
            description="Exort the active vertex color layer",
            default=True)

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        filepath = self.filepath
        filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
        from . import export_ms3d
        keywords = self.as_keywords(ignore=("check_existing", "filter_glob"))
        return export_ms3d.save(self, context, **keywords)

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "use_modifiers")
        row.prop(self, "use_normals")
        row = layout.row()
        row.prop(self, "use_uv_coords")
        row.prop(self, "use_colors")



def menu_func_export(self, context):
    self.layout.operator(ExportMS3D.bl_idname, text="MS3D (.txt)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
