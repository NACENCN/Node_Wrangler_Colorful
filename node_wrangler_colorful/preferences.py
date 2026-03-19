# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.props import EnumProperty, BoolProperty, StringProperty, FloatProperty
from bpy.app.translations import contexts as i18n_contexts

try:
    from bpy.app.translations import pgettext_n as n_
except ImportError:
    def n_(*args):
        return args[0] if args else ""

try:
    from bpy.app.translations import pgettext_iface as iface_
except ImportError:
    def iface_(msg):
        return msg

from . import operators
from . import interface

from .utils.constants import nice_hotkey_name
from .utils.i18n import T


# Principled prefs
class NWPrincipledPreferences(bpy.types.PropertyGroup):
    base_color: StringProperty(
        name=T('基础色'),
        default='diffuse diff albedo base col color basecolor',
        description='基础色贴图的命名组件')
    metallic: StringProperty(
        name=T('金属度'),
        default='metallic metalness metal mtl',
        description='金属度贴图的命名组件')
    specular: StringProperty(
        name=T('高光'),
        default='specularity specular spec spc',
        description='高光贴图的命名组件')
    normal: StringProperty(
        name=T('法向'),
        default='normal nor nrm nrml norm',
        description='法向贴图的命名组件')
    bump: StringProperty(
        name=T('凹凸'),
        default='bump bmp',
        description='凹凸贴图的命名组件')
    rough: StringProperty(
        name=T('糙度'),
        default='roughness rough rgh',
        description='糙度贴图的命名组件')
    gloss: StringProperty(
        name=T('光泽'),
        default='gloss glossy glossiness',
        description='光泽贴图的命名组件')
    displacement: StringProperty(
        name=T('置换'),
        default='displacement displace disp dsp height heightmap',
        description='置换贴图的命名组件')
    transmission: StringProperty(
        name=T('透射'),
        default='transmission transparency',
        description='透射贴图的命名组件')
    emission: StringProperty(
        name=T('自发光'),
        default='emission emissive emit',
        description='自发光贴图的命名组件')
    alpha: StringProperty(
        name=T('Alpha'),
        default='alpha opacity',
        description='Alpha 贴图的命名组件')
    ambient_occlusion: StringProperty(
        name=T('环境光遮蔽'),
        default='ao ambient occlusion',
        description='AO 贴图的命名组件')


def update_merge_hide_zh(self, context):
    if self.merge_hide != self.merge_hide_zh: self.merge_hide = self.merge_hide_zh
    if self.merge_hide_en != self.merge_hide_zh: self.merge_hide_en = self.merge_hide_zh

def update_merge_hide_en(self, context):
    if self.merge_hide != self.merge_hide_en: self.merge_hide = self.merge_hide_en
    if self.merge_hide_zh != self.merge_hide_en: self.merge_hide_zh = self.merge_hide_en

def update_merge_pos_zh(self, context):
    if self.merge_position != self.merge_position_zh: self.merge_position = self.merge_position_zh
    if self.merge_position_en != self.merge_position_zh: self.merge_position_en = self.merge_position_zh

def update_merge_pos_en(self, context):
    if self.merge_position != self.merge_position_en: self.merge_position = self.merge_position_en
    if self.merge_position_zh != self.merge_position_en: self.merge_position_zh = self.merge_position_en

def update_render_quality_zh(self, context):
    if self.render_quality != self.render_quality_zh: self.render_quality = self.render_quality_zh
    if self.render_quality_en != self.render_quality_zh: self.render_quality_en = self.render_quality_zh

def update_render_quality_en(self, context):
    if self.render_quality != self.render_quality_en: self.render_quality = self.render_quality_en
    if self.render_quality_zh != self.render_quality_en: self.render_quality_zh = self.render_quality_en

def update_visual_theme_zh(self, context):
    if self.visual_theme != self.visual_theme_zh: self.visual_theme = self.visual_theme_zh
    if self.visual_theme_en != self.visual_theme_zh: self.visual_theme_en = self.visual_theme_zh

def update_visual_theme_en(self, context):
    if self.visual_theme != self.visual_theme_en: self.visual_theme = self.visual_theme_en
    if self.visual_theme_zh != self.visual_theme_en: self.visual_theme_zh = self.visual_theme_en

# Addon prefs
class NWNodeWrangler(bpy.types.AddonPreferences):
    bl_idname = __package__

    language: EnumProperty(
        name="Language / 语言",
        items=(
            ("ZH", "简体中文", "使用简体中文界面"),
            ("EN", "English", "Use English interface")
        ),
        default='ZH',
        description="选择插件界面的语言"
    )

    visual_theme: EnumProperty(
        items=(
            ("0", "0", ""),
            ("1", "1", ""),
            ("2", "2", ""),
            ("3", "3", ""),
            ("4", "4", ""),
            ("5", "5", "")
        ),
        default='0'
    )
    visual_theme_zh: EnumProperty(
        name="流光主题",
        items=(
            ("0", "经典彩虹", "保留完整的色彩光谱与脉冲"),
            ("1", "赛博霓虹", "青色与品红的高频数据流"),
            ("2", "魔法流金", "缓慢涌动的温暖岩浆"),
            ("3", "幽能矩阵", "深邃的黑客帝国代码流"),
            ("4", "极地冰晶", "清凉柔和的浅蓝水流"),
            ("5", "少女粉", "萌萌哒心动粉色流光")
        ),
        default='0',
        update=update_visual_theme_zh
    )
    visual_theme_en: EnumProperty(
        name="Visual Theme",
        items=(
            ("0", "Classic Rainbow", "Full color spectrum with flowing pulses"),
            ("1", "Cyberpunk Neon", "Cyan and magenta high-frequency data streams"),
            ("2", "Magical Gold", "Slowly surging warm magma"),
            ("3", "Matrix Stream", "Deep Matrix-style code stream"),
            ("4", "Frost Ice", "Cool and soft light blue water flow"),
            ("5", "Cute Pink", "Heart-throbbing cute pink glow")
        ),
        default='0',
        update=update_visual_theme_en
    )

    render_quality: EnumProperty(
        items=(
            ("QUALITY", "Quality", ""),
            ("PERFORMANCE", "Performance", "")
        ),
        default='QUALITY'
    )
    render_quality_zh: EnumProperty(
        name="渲染质量",
        items=(
            ("QUALITY", "质量模式", "渲染所有选中节点，可能卡顿"),
            ("PERFORMANCE", "性能模式", "超过5个节点仅渲染活动节点")
        ),
        default='QUALITY',
        update=update_render_quality_zh
    )
    render_quality_en: EnumProperty(
        name="Render Quality",
        items=(
            ("QUALITY", "Quality Mode", "Render all selected nodes, might lag"),
            ("PERFORMANCE", "Performance Mode", "Only render active node if >5 selected")
        ),
        default='QUALITY',
        update=update_render_quality_en
    )

    merge_hide: EnumProperty(
        items=(
            ("ALWAYS", "Always", ""),
            ("NON_SHADER", "Non-Shader", ""),
            ("NEVER", "Never", "")
        ),
        default='NON_SHADER'
    )
    merge_hide_zh: EnumProperty(
        name="隐藏混合节点",
        items=(
            ("ALWAYS", "总是", "总是折叠新的混合节点"),
            ("NON_SHADER", "非着色器", "除着色器外均折叠"),
            ("NEVER", "从不", "从不折叠新的混合节点")
        ),
        default='NON_SHADER',
        update=update_merge_hide_zh
    )
    merge_hide_en: EnumProperty(
        name="Hide Merge Nodes",
        items=(
            ("ALWAYS", "Always", "Always collapse the new merge nodes"),
            ("NON_SHADER", "Non-Shader", "Collapse in all cases except for shaders"),
            ("NEVER", "Never", "Never collapse the new merge nodes")
        ),
        default='NON_SHADER',
        update=update_merge_hide_en
    )

    merge_position: EnumProperty(
        items=(
            ("CENTER", "Center", ""),
            ("BOTTOM", "Bottom", "")
        ),
        default='CENTER'
    )
    merge_position_zh: EnumProperty(
        name="混合节点位置",
        items=(
            ("CENTER", "中心", "将混合节点放置在两个节点之间"),
            ("BOTTOM", "底部", "将混合节点放置在最低节点的高度")
        ),
        default='CENTER',
        update=update_merge_pos_zh
    )
    merge_position_en: EnumProperty(
        name="Merge Node Position",
        items=(
            ("CENTER", "Center", "Place merge nodes between the two nodes"),
            ("BOTTOM", "Bottom", "Place merge nodes at the lowest node")
        ),
        default='CENTER',
        update=update_merge_pos_en
    )

    show_connected_rainbow: BoolProperty(
        name=T("显示相连节点彩虹线"),
        default=True,
        description="显示选中节点相连的彩虹线效果"
    )
    connected_rainbow_thickness: FloatProperty(
        name=T("彩虹线增粗"),
        default=1.0,
        min=1.0,
        max=4.0,
        description="在当前线宽基础上按倍率增粗"
    )

    show_hotkey_list: BoolProperty(
        name=T("显示热键列表"),
        default=False,
        description="展开此框以列出此插件所有功能的热键"
    )
    hotkey_list_filter: StringProperty(
        name="        按名称过滤",
        default="",
        description="仅显示名称中包含此文本的热键",
        options={'TEXTEDIT_UPDATE'}
    )
    show_principled_lists: BoolProperty(
        name=T("显示 Principled 命名标签"),
        default=False,
        description="展开此框以列出 Principled 纹理设置的所有命名标签"
    )
    principled_tags: bpy.props.PointerProperty(type=NWPrincipledPreferences)

    def draw(self, context):
        layout = self.layout

        # 语言切换置顶
        row = layout.row()
        row.prop(self, "language", expand=True)
        layout.separator()

        node_wrangler_addon = context.preferences.addons.get("node_wrangler")
        if node_wrangler_addon:
            box = layout.box()
            box.alert = True
            col = box.column(align=True)
            col.label(text=T("检测到已启用原版 Node Wrangler（node_wrangler）"), icon="ERROR")
            col.label(text=T("请先在插件列表禁用原版，否则本插件会冲突/无法正常使用"), icon="BLANK1")

        col = layout.column()
        if self.language == 'EN':
            col.prop(self, "visual_theme_en", text=T("流光主题"))
            col.prop(self, "render_quality_en", text=T("渲染质量"))
            col.prop(self, "merge_position_en", text=T("混合节点位置"))
            col.prop(self, "merge_hide_en", text=T("隐藏混合节点"))
        else:
            col.prop(self, "visual_theme_zh", text=T("流光主题"))
            col.prop(self, "render_quality_zh", text=T("渲染质量"))
            col.prop(self, "merge_position_zh", text=T("混合节点位置"))
            col.prop(self, "merge_hide_zh", text=T("隐藏混合节点"))
        col.prop(self, "show_connected_rainbow", text=T("显示相连节点彩虹线"))
        sub = col.column()
        sub.enabled = self.show_connected_rainbow
        sub.prop(self, "connected_rainbow_thickness", text=T("彩虹线增粗"))

        box = layout.box()
        col = box.column(align=True)
        col.prop(
            self,
            "show_principled_lists",
            text=T('显示 Principled 命名标签'),
            toggle=True)
        if self.show_principled_lists:
            tags = self.principled_tags

            col.prop(tags, "base_color", text=T("基础色"))
            col.prop(tags, "metallic", text=T("金属度"))
            col.prop(tags, "specular", text=T("高光"))
            col.prop(tags, "rough", text=T("糙度"))
            col.prop(tags, "gloss", text=T("光泽"))
            col.prop(tags, "normal", text=T("法向"))
            col.prop(tags, "bump", text=T("凹凸"))
            col.prop(tags, "displacement", text=T("置换"))
            col.prop(tags, "transmission", text=T("透射"))
            col.prop(tags, "emission", text=T("自发光"))
            col.prop(tags, "alpha", text=T("Alpha"))
            col.prop(tags, "ambient_occlusion", text=T("环境光遮蔽"))

        box = layout.box()
        col = box.column(align=True)
        hotkey_button_name = T("隐藏热键列表") if self.show_hotkey_list else T("显示热键列表")
        col.prop(self, "show_hotkey_list", text=hotkey_button_name, translate=False, toggle=True)
        if self.show_hotkey_list:
            col.prop(self, "hotkey_list_filter", text=T("        按名称过滤"), icon="VIEWZOOM")
            col.separator()
            for hotkey in kmi_defs:
                if hotkey[7]:
                    hotkey_name = T(hotkey[7])

                    if (self.hotkey_list_filter.lower() in hotkey_name.lower()
                            or self.hotkey_list_filter.lower() in iface_(hotkey_name).lower()):
                        row = col.row(align=True)
                        row.label(text=hotkey_name)
                        keystr = iface_(nice_hotkey_name(hotkey[1]), i18n_contexts.ui_events_keymaps)
                        if hotkey[4]:
                            keystr = iface_("Shift", i18n_contexts.ui_events_keymaps) + " " + keystr
                        if hotkey[5]:
                            keystr = iface_("Alt", i18n_contexts.ui_events_keymaps) + " " + keystr
                        if hotkey[3]:
                            keystr = iface_("Ctrl", i18n_contexts.ui_events_keymaps) + " " + keystr
                        row.label(text=keystr, translate=False)


#
#  REGISTER/UNREGISTER CLASSES AND KEYMAP ITEMS
#
addon_keymaps = []
# kmi_defs entry: (identifier, key, action, CTRL, SHIFT, ALT, props, nice name)
# props entry: (property name, property value)
kmi_defs = (
    # MERGE NODES
    # NWMergeNodes with Ctrl (AUTO).
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_0', 'PRESS', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), T("合并节点 (自动)")),
    (operators.NWMergeNodes.bl_idname, 'ZERO', 'PRESS', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'AUTO'),), T("合并节点 (自动)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), T("合并节点 (相加)")),
    (operators.NWMergeNodes.bl_idname, 'EQUAL', 'PRESS', True, False, False,
        (('mode', 'ADD'), ('merge_type', 'AUTO'),), T("合并节点 (相加)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), T("合并节点 (相乘)")),
    (operators.NWMergeNodes.bl_idname, 'EIGHT', 'PRESS', True, False, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'AUTO'),), T("合并节点 (相乘)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), T("合并节点 (相减)")),
    (operators.NWMergeNodes.bl_idname, 'MINUS', 'PRESS', True, False, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'AUTO'),), T("合并节点 (相减)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), T("合并节点 (相除)")),
    (operators.NWMergeNodes.bl_idname, 'SLASH', 'PRESS', True, False, False,
        (('mode', 'DIVIDE'), ('merge_type', 'AUTO'),), T("合并节点 (相除)")),
    (operators.NWMergeNodes.bl_idname, 'COMMA', 'PRESS', True, False, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), T("合并节点 (小于)")),
    (operators.NWMergeNodes.bl_idname, 'PERIOD', 'PRESS', True, False, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), T("合并节点 (大于)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PERIOD', 'PRESS', True, False, False,
        (('mode', 'MIX'), ('merge_type', 'ZCOMBINE'),), T("合并节点 (Z-Combine)")),
    # NWMergeNodes with Ctrl Alt (MIX or ALPHAOVER)
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_0', 'PRESS', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'ALPHAOVER'),), T("合并节点 (Alpha Over)")),
    (operators.NWMergeNodes.bl_idname, 'ZERO', 'PRESS', True, False, True,
        (('mode', 'MIX'), ('merge_type', 'ALPHAOVER'),), T("合并节点 (Alpha Over)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相加)")),
    (operators.NWMergeNodes.bl_idname, 'EQUAL', 'PRESS', True, False, True,
        (('mode', 'ADD'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相加)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相乘)")),
    (operators.NWMergeNodes.bl_idname, 'EIGHT', 'PRESS', True, False, True,
        (('mode', 'MULTIPLY'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相乘)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相减)")),
    (operators.NWMergeNodes.bl_idname, 'MINUS', 'PRESS', True, False, True,
        (('mode', 'SUBTRACT'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相减)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相除)")),
    (operators.NWMergeNodes.bl_idname, 'SLASH', 'PRESS', True, False, True,
        (('mode', 'DIVIDE'), ('merge_type', 'MIX'),), T("合并节点 (颜色, 相除)")),
    # NWMergeNodes with Ctrl Shift (MATH)
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相加)")),
    (operators.NWMergeNodes.bl_idname, 'EQUAL', 'PRESS', True, True, False,
        (('mode', 'ADD'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相加)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相乘)")),
    (operators.NWMergeNodes.bl_idname, 'EIGHT', 'PRESS', True, True, False,
        (('mode', 'MULTIPLY'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相乘)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相减)")),
    (operators.NWMergeNodes.bl_idname, 'MINUS', 'PRESS', True, True, False,
        (('mode', 'SUBTRACT'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相减)")),
    (operators.NWMergeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相除)")),
    (operators.NWMergeNodes.bl_idname, 'SLASH', 'PRESS', True, True, False,
        (('mode', 'DIVIDE'), ('merge_type', 'MATH'),), T("合并节点 (数学, 相除)")),
    (operators.NWMergeNodes.bl_idname, 'COMMA', 'PRESS', True, True, False,
        (('mode', 'LESS_THAN'), ('merge_type', 'MATH'),), T("合并节点 (数学, 小于)")),
    (operators.NWMergeNodes.bl_idname, 'PERIOD', 'PRESS', True, True, False,
        (('mode', 'GREATER_THAN'), ('merge_type', 'MATH'),), T("合并节点 (数学, 大于)")),
    # BATCH CHANGE NODES
    # NWBatchChangeNodes with Alt
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_0', 'PRESS', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), T("批量更改混合类型 (混合)")),
    (operators.NWBatchChangeNodes.bl_idname, 'ZERO', 'PRESS', False, False, True,
        (('blend_type', 'MIX'), ('operation', 'CURRENT'),), T("批量更改混合类型 (混合)")),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_PLUS', 'PRESS', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), T("批量更改混合类型 (相加)")),
    (operators.NWBatchChangeNodes.bl_idname, 'EQUAL', 'PRESS', False, False, True,
        (('blend_type', 'ADD'), ('operation', 'ADD'),), T("批量更改混合类型 (相加)")),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_ASTERIX', 'PRESS', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), T("批量更改混合类型 (相乘)")),
    (operators.NWBatchChangeNodes.bl_idname, 'EIGHT', 'PRESS', False, False, True,
        (('blend_type', 'MULTIPLY'), ('operation', 'MULTIPLY'),), T("批量更改混合类型 (相乘)")),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_MINUS', 'PRESS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), T("批量更改混合类型 (相减)")),
    (operators.NWBatchChangeNodes.bl_idname, 'MINUS', 'PRESS', False, False, True,
        (('blend_type', 'SUBTRACT'), ('operation', 'SUBTRACT'),), T("批量更改混合类型 (相减)")),
    (operators.NWBatchChangeNodes.bl_idname, 'NUMPAD_SLASH', 'PRESS', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), T("批量更改混合类型 (相除)")),
    (operators.NWBatchChangeNodes.bl_idname, 'SLASH', 'PRESS', False, False, True,
        (('blend_type', 'DIVIDE'), ('operation', 'DIVIDE'),), T("批量更改混合类型 (相除)")),
    (operators.NWBatchChangeNodes.bl_idname, 'COMMA', 'PRESS', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'LESS_THAN'),), T("批量更改混合类型 (当前)")),
    (operators.NWBatchChangeNodes.bl_idname, 'PERIOD', 'PRESS', False, False, True,
        (('blend_type', 'CURRENT'), ('operation', 'GREATER_THAN'),), T("批量更改混合类型 (当前)")),
    (operators.NWBatchChangeNodes.bl_idname, 'DOWN_ARROW', 'PRESS', False, False, True,
        (('blend_type', 'NEXT'), ('operation', 'NEXT'),), T("批量更改混合类型 (下一个)")),
    (operators.NWBatchChangeNodes.bl_idname, 'UP_ARROW', 'PRESS', False, False, True,
        (('blend_type', 'PREV'), ('operation', 'PREV'),), T("批量更改混合类型 (上一个)")),
    # LINK ACTIVE TO SELECTED
    # Don't use names, don't replace links (K)
    (operators.NWLinkActiveToSelected.bl_idname, 'K', 'PRESS', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', False),), T("链接活动项到选中项 (不替换链接)")),
    # Don't use names, replace links (Shift K)
    (operators.NWLinkActiveToSelected.bl_idname, 'K', 'PRESS', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', False),), T("链接活动项到选中项 (替换链接)")),
    # Use node name, don't replace links (')
    (operators.NWLinkActiveToSelected.bl_idname, 'QUOTE', 'PRESS', False, False, False,
        (('replace', False), ('use_node_name', True), ('use_outputs_names', False),), T("链接活动项到选中项 (不替换链接, 节点名称)")),
    # Use node name, replace links (Shift ')
    (operators.NWLinkActiveToSelected.bl_idname, 'QUOTE', 'PRESS', False, True, False,
        (('replace', True), ('use_node_name', True), ('use_outputs_names', False),), T("链接活动项到选中项 (替换链接, 节点名称)")),
    # Don't use names, don't replace links (;)
    (operators.NWLinkActiveToSelected.bl_idname, 'SEMI_COLON', 'PRESS', False, False, False,
        (('replace', False), ('use_node_name', False), ('use_outputs_names', True),), T("链接活动项到选中项 (不替换链接, 输出名称)")),
    # Don't use names, replace links (')
    (operators.NWLinkActiveToSelected.bl_idname, 'SEMI_COLON', 'PRESS', False, True, False,
        (('replace', True), ('use_node_name', False), ('use_outputs_names', True),), T("链接活动项到选中项 (替换链接, 输出名称)")),
    # CHANGE MIX FACTOR
    (operators.NWChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS', False,
     False, True, (('option', -0.1),), T("减少混合系数 0.1")),
    (operators.NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS', False,
     False, True, (('option', 0.1),), T("增加混合系数 0.1")),
    (operators.NWChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS', False,
     True, True, (('option', -0.01),), T("减少混合系数 0.01")),
    (operators.NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS', False,
     True, True, (('option', 0.01),), T("增加混合系数 0.01")),
    (operators.NWChangeMixFactor.bl_idname, 'LEFT_ARROW', 'PRESS',
     True, True, True, (('option', 0.0),), T("设置混合系数为 0.0")),
    (operators.NWChangeMixFactor.bl_idname, 'RIGHT_ARROW', 'PRESS',
     True, True, True, (('option', 1.0),), T("设置混合系数为 1.0")),
    (operators.NWChangeMixFactor.bl_idname, 'NUMPAD_0', 'PRESS',
     True, True, True, (('option', 0.0),), T("设置混合系数为 0.0")),
    (operators.NWChangeMixFactor.bl_idname, 'ZERO', 'PRESS', True, True, True, (('option', 0.0),), T("设置混合系数为 0.0")),
    (operators.NWChangeMixFactor.bl_idname, 'NUMPAD_1', 'PRESS', True, True, True, (('option', 1.0),), T("设置混合系数为 1.0")),
    (operators.NWChangeMixFactor.bl_idname, 'ONE', 'PRESS', True, True, True, (('option', 1.0),), T("设置混合系数为 1.0")),
    # CLEAR LABEL (Alt L)
    (operators.NWClearLabel.bl_idname, 'L', 'PRESS', False, False, True, (('option', False),), T("清除节点标签")),
    # MODIFY LABEL (Alt Shift L)
    (operators.NWModifyLabels.bl_idname, 'L', 'PRESS', False, True, True, None, T("修改节点标签")),
    # Copy Label from active to selected
    (operators.NWCopyLabel.bl_idname, 'V', 'PRESS', False, True, False,
     (('option', 'FROM_ACTIVE'),), T("从活动项复制标签到选中项")),
    # DETACH OUTPUTS (Alt Shift D)
    (operators.NWDetachOutputs.bl_idname, 'D', 'PRESS', False, True, True, None, T("断开输出")),
    # LINK TO OUTPUT NODE (O)
    (operators.NWLinkToOutputNode.bl_idname, 'O', 'PRESS', False, False, False, None, T("链接到输出节点")),
    # SELECT PARENT/CHILDREN
    # Select Children
    (operators.NWSelectParentChildren.bl_idname, 'RIGHT_BRACKET', 'PRESS',
     False, False, False, (('option', 'CHILD'),), T("选择子级")),
    # Select Parent
    (operators.NWSelectParentChildren.bl_idname, 'LEFT_BRACKET', 'PRESS',
     False, False, False, (('option', 'PARENT'),), T("选择父级")),
    # Add Texture Setup
    (operators.NWAddTextureSetup.bl_idname, 'T', 'PRESS', True, False, False, None, T("添加纹理设置")),
    # Add Principled BSDF Texture Setup
    (operators.NWAddPrincipledSetup.bl_idname, 'T', 'PRESS', True, True, False, None, T("添加 Principled 纹理设置")),
    # Reset backdrop
    (operators.NWResetBG.bl_idname, 'Z', 'PRESS', False, False, False, None, T("重置背景图像缩放")),
    # Delete unused
    (operators.NWDeleteUnused.bl_idname, 'X', 'PRESS', False, False, True, None, T("删除未使用的节点")),
    # Frame Selected
    ('node.join', 'P', 'PRESS', False, True, False, None, T("框选选中节点")),
    # Swap Links
    (operators.NWSwapLinks.bl_idname, 'S', 'PRESS', False, False, True, None, T("交换链接")),
    # Reload Images
    (operators.NWReloadImages.bl_idname, 'R', 'PRESS', False, False, True, None, T("重新加载图像")),
    # Lazy Mix
    (operators.NWLazyMix.bl_idname, 'RIGHTMOUSE', 'PRESS', True, True, False, None, T("快速混合")),
    # Lazy Connect
    (operators.NWLazyConnect.bl_idname, 'RIGHTMOUSE', 'PRESS', False, False, True, (('with_menu', False),), T("快速连接")),
    # Lazy Connect with Menu
    (operators.NWLazyConnect.bl_idname, 'RIGHTMOUSE', 'PRESS', False,
     True, True, (('with_menu', True),), T("快速连接 (带接口菜单)")),
    # Align Nodes
    (operators.NWAlignNodes.bl_idname, 'EQUAL', 'PRESS', False, True,
     False, None, T("整齐对齐选中节点")),
    # Reset Nodes (Back Space)
    (operators.NWResetNodes.bl_idname, 'BACK_SPACE', 'PRESS', False, False,
     False, None, T("重置节点 (保持连接)")),
    # MENUS
    ('wm.call_menu', 'W', 'PRESS', False, True, False, (('name', interface.NodeWranglerMenu.bl_idname),), T("Node Wrangler 菜单")),
    ('wm.call_menu', 'SLASH', 'PRESS', False, False, False,
     (('name', interface.NWAddReroutesMenu.bl_idname),), T("添加路由点菜单")),
    ('wm.call_menu', 'NUMPAD_SLASH', 'PRESS', False, False, False,
     (('name', interface.NWAddReroutesMenu.bl_idname),), T("添加路由点菜单")),
    ('wm.call_menu', 'BACK_SLASH', 'PRESS', False, False, False,
     (('name', interface.NWLinkActiveToSelectedMenu.bl_idname),), T("链接活动项到选中项 (菜单)")),
    ('wm.call_menu', 'C', 'PRESS', False, True, False,
     (('name', interface.NWCopyToSelectedMenu.bl_idname),), T("复制到选中项 (菜单)")),
)

classes = (
    NWPrincipledPreferences, NWNodeWrangler
)


def register():
    from bpy.utils import register_class, unregister_class
    for cls in classes:
        try:
            register_class(cls)
        except ValueError:
            unregister_class(cls)
            register_class(cls)

    # keymaps
    addon_keymaps.clear()
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
        for (identifier, key, action, CTRL, SHIFT, ALT, props, nicename) in kmi_defs:
            kmi = km.keymap_items.new(identifier, key, action, ctrl=CTRL, shift=SHIFT, alt=ALT)
            if props:
                for prop, value in props:
                    setattr(kmi.properties, prop, value)
            addon_keymaps.append((km, kmi))


def unregister():

    # keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
