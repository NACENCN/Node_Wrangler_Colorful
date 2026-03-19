# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel, Menu
from bpy.props import StringProperty
from bpy.app.translations import contexts as i18n_contexts

from . import operators

from .utils.constants import blend_types, geo_combine_operations, operations
from .utils.nodes import get_nodes_links, NWBaseMenu


from .utils.i18n import T


def socket_to_icon(socket):
    socket_type = socket.type

    if socket_type == "CUSTOM":
        return "RADIOBUT_OFF"

    if socket_type == "VALUE":
        socket_type = "FLOAT"

    return "NODE_SOCKET_" + socket_type


def drawlayout(context, layout, mode='non-panel'):
    tree_type = context.space_data.tree_type

    col = layout.column(align=True)
    col.menu(NWMergeNodesMenu.bl_idname, text=T("合并选中节点"))
    col.separator()

    if tree_type == 'ShaderNodeTree':
        col = layout.column(align=True)
        col.operator(operators.NWAddTextureSetup.bl_idname, text=T("添加纹理设置"), icon='NODE_SEL')
        col.operator(operators.NWAddPrincipledSetup.bl_idname, text=T("添加原理化设置"), icon='NODE_SEL')
        col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWDetachOutputs.bl_idname, text=T("分离输出"), icon='UNLINKED')
    col.operator(operators.NWSwapLinks.bl_idname, text=T("交换链接"))
    col.menu(NWAddReroutesMenu.bl_idname, text=T("添加路由点"), icon='LAYER_USED')
    col.separator()

    col = layout.column(align=True)
    col.menu(NWLinkActiveToSelectedMenu.bl_idname, text=T("链接活动项到选中项"), icon='LINKED')
    if tree_type != 'GeometryNodeTree':
        col.operator(operators.NWLinkToOutputNode.bl_idname, text=T("连接到输出"), icon='DRIVER')
    col.separator()

    col = layout.column(align=True)
    if mode == 'panel':
        row = col.row(align=True)
        row.operator(operators.NWClearLabel.bl_idname, text=T("清除标签")).option = True
        row.operator(operators.NWModifyLabels.bl_idname, text=T("修改标签"))
    else:
        col.operator(operators.NWClearLabel.bl_idname, text=T("清除标签")).option = True
        col.operator(operators.NWModifyLabels.bl_idname, text=T("修改标签"))
    col.menu(NWBatchChangeNodesMenu.bl_idname, text=T("批量修改"), text_ctxt=i18n_contexts.operator_default)
    col.separator()
    col.menu(NWCopyToSelectedMenu.bl_idname, text=T("复制到选中项"))
    col.separator()

    col = layout.column(align=True)
    if tree_type == 'CompositorNodeTree':
        col.operator(operators.NWResetBG.bl_idname, text=T("重置背景图像缩放"), icon='ZOOM_PREVIOUS')
    if tree_type != 'GeometryNodeTree':
        col.operator(operators.NWReloadImages.bl_idname, text=T("重新加载图像"), icon='FILE_REFRESH')
    col.separator()

    col = layout.column(align=True)
    col.operator('node.join', text=T("Join Nodes"), icon='STICKY_UVS_LOC')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWAlignNodes.bl_idname, text=T("对齐节点"), icon='CENTER_ONLY')
    col.separator()

    col = layout.column(align=True)
    col.operator(operators.NWDeleteUnused.bl_idname, text=T("删除未使用的节点"), icon='CANCEL')


class NodeWranglerPanel(Panel, NWBaseMenu):
    bl_idname = "NODE_PT_nw_node_wrangler"
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Node Wrangler Colorful"
    bl_region_type = "UI"
    bl_category = "Node Wrangler"

    prepend: StringProperty(
        name='prepend',
    )
    append: StringProperty()
    remove: StringProperty()

    def draw(self, context):
        self.layout.label(text=T("(快速访问: Shift+W)"))
        drawlayout(context, self.layout, mode='panel')


#
#  M E N U S
#
class NodeWranglerMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_node_wrangler_menu"
    bl_label = "Node Wrangler Colorful"

    def draw(self, context):
        self.layout.operator_context = 'INVOKE_DEFAULT'
        drawlayout(context, self.layout)


class NWMergeNodesMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_merge_nodes_menu"
    bl_label = T("合并选中节点")

    def draw(self, context):
        type = context.space_data.tree_type
        layout = self.layout
        if type == 'ShaderNodeTree':
            layout.menu(NWMergeShadersMenu.bl_idname, text=T("使用着色器"))
        if type == 'GeometryNodeTree':
            layout.menu(NWMergeGeometryMenu.bl_idname, text=T("使用几何节点"))
            layout.menu(NWMergeMathMenu.bl_idname, text=T("使用数学节点"))
        else:
            layout.menu(NWMergeMixMenu.bl_idname, text=T("使用混合节点"))
            layout.menu(NWMergeMathMenu.bl_idname, text=T("使用数学节点"))
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=T("使用 Z-Combine 节点"))
            props.mode = 'MIX'
            props.merge_type = 'ZCOMBINE'
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=T("使用 Alpha Over 节点"))
            props.mode = 'MIX'
            props.merge_type = 'ALPHAOVER'


class NWMergeGeometryMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_merge_geometry_menu"
    bl_label = T("使用几何节点合并选中节点")

    def draw(self, context):
        layout = self.layout
        # The boolean node + Join Geometry node
        for type, name, description in geo_combine_operations:
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=T(name), text_ctxt=i18n_contexts.id_nodetree)
            props.mode = type
            props.merge_type = 'GEOMETRY'


class NWMergeShadersMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_merge_shaders_menu"
    bl_label = T("使用着色器合并选中节点")

    def draw(self, context):
        layout = self.layout
        for type in ('MIX', 'ADD'):
            name = f'{type.capitalize()} Shader'
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=T(name), text_ctxt=i18n_contexts.default)
            props.mode = type
            props.merge_type = 'SHADER'


class NWMergeMixMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_merge_mix_menu"
    bl_label = T("使用混合合并选中节点")

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=T(name), text_ctxt=i18n_contexts.id_nodetree)
            props.mode = type
            props.merge_type = 'MIX'


class NWConnectionListOutputs(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_connection_list_out"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        nodes, links = get_nodes_links(context)

        layout.label(text=T("从接口"), icon='RADIOBUT_OFF')
        layout.separator()

        n1 = nodes[context.scene.NWLazySource]
        for index, output in enumerate(n1.outputs):
            # Only show sockets that are exposed.
            if output.enabled:
                layout.operator(
                    operators.NWCallInputsMenu.bl_idname,
                    text=output.name,
                    text_ctxt=i18n_contexts.default,
                    icon=socket_to_icon(output),
                ).from_socket = index


class NWConnectionListInputs(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_connection_list_in"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        nodes, links = get_nodes_links(context)

        layout.label(text=T("到接口"), icon='FORWARD')
        layout.separator()

        n2 = nodes[context.scene.NWLazyTarget]

        for index, input in enumerate(n2.inputs):
            # Only show sockets that are exposed.
            # This prevents, for example, the scale value socket
            # of the vector math node being added to the list when
            # the mode is not 'SCALE'.
            if input.enabled:
                op = layout.operator(
                    operators.NWMakeLink.bl_idname, text=input.name,
                    text_ctxt=i18n_contexts.default,
                    icon=socket_to_icon(input),
                )
                op.from_socket = context.scene.NWSourceSocket
                op.to_socket = index


class NWMergeMathMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_merge_math_menu"
    bl_label = T("使用数学合并选中节点")

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(operators.NWMergeNodes.bl_idname, text=T(name), text_ctxt=i18n_contexts.id_nodetree)
            props.mode = type
            props.merge_type = 'MATH'


class NWBatchChangeNodesMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_batch_change_nodes_menu"
    bl_label = T("批量修改选中节点")

    def draw(self, context):
        layout = self.layout
        layout.menu(NWBatchChangeBlendTypeMenu.bl_idname, text=T("批量修改混合类型"))
        layout.menu(NWBatchChangeOperationMenu.bl_idname, text=T("批量修改数学运算"))


class NWBatchChangeBlendTypeMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_batch_change_blend_type_menu"
    bl_label = T("批量修改混合类型")

    def draw(self, context):
        layout = self.layout
        for type, name, description in blend_types:
            props = layout.operator(
                operators.NWBatchChangeNodes.bl_idname,
                text=T(name),
                text_ctxt=i18n_contexts.id_nodetree,
            )
            props.blend_type = type
            props.operation = 'CURRENT'


class NWBatchChangeOperationMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_batch_change_operation_menu"
    bl_label = T("批量修改数学运算")

    def draw(self, context):
        layout = self.layout
        for type, name, description in operations:
            props = layout.operator(operators.NWBatchChangeNodes.bl_idname, text=T(name), text_ctxt=i18n_contexts.id_nodetree)
            props.blend_type = 'CURRENT'
            props.operation = type


class NWCopyToSelectedMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_copy_node_properties_menu"
    bl_label = T("复制到选中项")

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.NWCopySettings.bl_idname, text=T("从活动项复制设置"))
        layout.menu(NWCopyLabelMenu.bl_idname, text=T("复制标签"))


class NWCopyLabelMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_copy_label_menu"
    bl_label = T("复制标签")

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.NWCopyLabel.bl_idname, text=T("从活动节点标签")).option = 'FROM_ACTIVE'
        layout.operator(operators.NWCopyLabel.bl_idname, text=T("从链接节点标签")).option = 'FROM_NODE'
        layout.operator(operators.NWCopyLabel.bl_idname, text=T("从链接输出名称")).option = 'FROM_SOCKET'


class NWAddReroutesMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_add_reroutes_menu"
    bl_label = "添加路由点"
    bl_description = "为选中节点的输出添加路由节点"

    @classmethod
    def poll(cls, context):
        cls.bl_label = T("添加路由点")
        return super().poll(context)

    def draw(self, context):
        layout = self.layout
        layout.operator(operators.NWAddReroutes.bl_idname, text=T("到所有输出")).option = 'ALL'
        layout.operator(operators.NWAddReroutes.bl_idname, text=T("到松散输出")).option = 'LOOSE'
        layout.operator(operators.NWAddReroutes.bl_idname, text=T("到链接输出")).option = 'LINKED'


class NWLinkActiveToSelectedMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_link_active_to_selected_menu"
    bl_label = "链接活动项到选中项"

    @classmethod
    def poll(cls, context):
        cls.bl_label = T("链接活动项到选中项")
        return super().poll(context)

    def draw(self, context):
        layout = self.layout
        layout.menu(NWLinkStandardMenu.bl_idname, text=T("到所有选中项"))
        layout.menu(NWLinkUseNodeNameMenu.bl_idname, text=T("使用节点名称/标签"))
        layout.menu(NWLinkUseOutputsNamesMenu.bl_idname, text=T("使用输出名称"))


class NWLinkStandardMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_link_standard_menu"
    bl_label = T("到所有选中项")

    def draw(self, context):
        layout = self.layout
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text=T("不替换链接"))
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = False
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text=T("替换链接"))
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = False


class NWLinkUseNodeNameMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_link_use_node_name_menu"
    bl_label = T("使用节点名称/标签")

    def draw(self, context):
        layout = self.layout
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text=T("不替换链接"))
        props.replace = False
        props.use_node_name = True
        props.use_outputs_names = False
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text=T("替换链接"))
        props.replace = True
        props.use_node_name = True
        props.use_outputs_names = False


class NWLinkUseOutputsNamesMenu(Menu, NWBaseMenu):
    bl_idname = "NODE_MT_nw_link_use_outputs_names_menu"
    bl_label = T("使用输出名称")

    def draw(self, context):
        layout = self.layout
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text=T("不替换链接"))
        props.replace = False
        props.use_node_name = False
        props.use_outputs_names = True
        props = layout.operator(operators.NWLinkActiveToSelected.bl_idname, text=T("替换链接"))
        props.replace = True
        props.use_node_name = False
        props.use_outputs_names = True


class NWAttributeMenu(bpy.types.Menu):
    bl_idname = "NODE_MT_nw_node_attribute_menu"
    bl_label = T("属性")

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return (space.type == 'NODE_EDITOR'
                and space.node_tree is not None
                and space.node_tree.library is None
                and space.tree_type == 'ShaderNodeTree'
                and space.shader_type == 'OBJECT')

    def draw(self, context):
        l = self.layout
        nodes, links = get_nodes_links(context)
        mat = context.object.active_material

        objs = []
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                if slot.material == mat:
                    objs.append(obj)
        attrs = []
        for obj in objs:
            if obj.data.attributes:
                for attr in obj.data.attributes:
                    if not attr.is_internal:
                        attrs.append(attr.name)
        attrs = list(set(attrs))  # get a unique list

        if attrs:
            for attr in attrs:
                l.operator(
                    operators.NWAddAttrNode.bl_idname,
                    text=attr,
                    translate=False,
                ).attr_name = attr
        else:
            l.label(text=T("此材质的对象上没有属性"))


#
#  APPENDAGES TO EXISTING UI
#


def select_parent_children_buttons(self, context):
    layout = self.layout
    layout.operator(operators.NWSelectParentChildren.bl_idname,
                    text=T("选择帧成员 (子级)")).option = 'CHILD'
    layout.operator(operators.NWSelectParentChildren.bl_idname, text=T("选择父级帧")).option = 'PARENT'


def attr_nodes_menu_func(self, context):
    col = self.layout.column(align=True)
    col.menu("NODE_MT_nw_node_attribute_menu", text=T("属性"))
    col.separator()


def multipleimages_menu_func(self, context):
    col = self.layout.column(align=True)
    col.operator("node.add_image", text=T("多张图像"))
    col.operator(operators.NWAddSequence.bl_idname, text=T("图像序列"))
    col.separator()


def bgreset_menu_func(self, context):
    self.layout.operator(operators.NWResetBG.bl_idname)


def save_viewer_menu_func(self, context):
    space = context.space_data
    if (space.type == 'NODE_EDITOR'
            and space.tree_type == 'CompositorNodeTree'
            and getattr(space, 'node_tree_sub_type', 'SCENE') == 'SCENE'
            and space.node_tree is not None
            and space.node_tree.library is None
            and space.edit_tree.nodes.active
            and space.edit_tree.nodes.active.type == "VIEWER"):
        self.layout.operator(operators.NWSaveViewer.bl_idname, icon='FILE_IMAGE')


def reset_nodes_button(self, context):
    node_active = context.active_node
    node_selected = context.selected_nodes

    # Check if active node is in the selection, ignore some node types
    if (len(node_selected) != 1
            or node_active is None
            or not node_active.select
            or node_active.type in {"REROUTE", "GROUP"}):
        return

    row = self.layout.row()

    if node_active.type == "FRAME":
        row.operator(operators.NWResetNodes.bl_idname, text=T("重置帧内节点"), icon="FILE_REFRESH")
    else:
        row.operator(operators.NWResetNodes.bl_idname, text=T("重置节点"), icon="FILE_REFRESH")

    self.layout.separator()


classes = (
    NodeWranglerPanel,
    NodeWranglerMenu,
    NWMergeNodesMenu,
    NWMergeGeometryMenu,
    NWMergeShadersMenu,
    NWMergeMixMenu,
    NWConnectionListOutputs,
    NWConnectionListInputs,
    NWMergeMathMenu,
    NWBatchChangeNodesMenu,
    NWBatchChangeBlendTypeMenu,
    NWBatchChangeOperationMenu,
    NWCopyToSelectedMenu,
    NWCopyLabelMenu,
    NWAddReroutesMenu,
    NWLinkActiveToSelectedMenu,
    NWLinkStandardMenu,
    NWLinkUseNodeNameMenu,
    NWLinkUseOutputsNamesMenu,
    NWAttributeMenu,
)


def register():
    from bpy.utils import register_class, unregister_class
    for cls in classes:
        try:
            register_class(cls)
        except ValueError:
            unregister_class(cls)
            register_class(cls)

    # menu items
    bpy.types.NODE_MT_select.append(select_parent_children_buttons)
    bpy.types.NODE_MT_category_shader_input.prepend(attr_nodes_menu_func)
    bpy.types.NODE_PT_backdrop.append(bgreset_menu_func)
    bpy.types.NODE_PT_active_node_generic.append(save_viewer_menu_func)
    bpy.types.NODE_MT_category_shader_texture.prepend(multipleimages_menu_func)
    bpy.types.NODE_MT_category_compositor_input.prepend(multipleimages_menu_func)
    bpy.types.NODE_PT_active_node_generic.prepend(reset_nodes_button)
    bpy.types.NODE_MT_node.prepend(reset_nodes_button)


def unregister():
    # menu items
    bpy.types.NODE_MT_select.remove(select_parent_children_buttons)
    bpy.types.NODE_MT_category_shader_input.remove(attr_nodes_menu_func)
    bpy.types.NODE_PT_backdrop.remove(bgreset_menu_func)
    bpy.types.NODE_PT_active_node_generic.remove(save_viewer_menu_func)
    bpy.types.NODE_MT_category_shader_texture.remove(multipleimages_menu_func)
    bpy.types.NODE_MT_category_compositor_input.remove(multipleimages_menu_func)
    bpy.types.NODE_PT_active_node_generic.remove(reset_nodes_button)
    bpy.types.NODE_MT_node.remove(reset_nodes_button)

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
