# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from collections import namedtuple
from .i18n import T


#################
# rl_outputs:
# list of outputs of Input Render Layer
# with attributes determining if pass is used,
# and MultiLayer EXR outputs names and corresponding render engines
#
# rl_outputs entry = (render_pass, rl_output_name, exr_output_name, in_eevee, in_cycles)
RL_entry = namedtuple('RL_Entry', ['render_pass', 'output_name', 'exr_output_name', 'in_eevee', 'in_cycles'])
rl_outputs = (
    RL_entry('use_pass_ambient_occlusion', T('环境光遮蔽'), 'Ambient Occlusion', True, True),
    RL_entry('use_pass_combined', T('图像'), 'Combined', True, True),
    RL_entry('use_pass_diffuse_color', T('漫射颜色'), 'Diffuse Color', False, True),
    RL_entry('use_pass_diffuse_direct', T('漫射直接光'), 'Diffuse Direct', False, True),
    RL_entry('use_pass_diffuse_indirect', T('漫射间接光'), 'Diffuse Indirect', False, True),
    RL_entry('use_pass_emit', T('自发光'), 'Emission', False, True),
    RL_entry('use_pass_environment', T('环境'), 'Environment', False, False),
    RL_entry('use_pass_glossy_color', T('光泽颜色'), 'Glossy Color', False, True),
    RL_entry('use_pass_glossy_direct', T('光泽直接光'), 'Glossy Direct', False, True),
    RL_entry('use_pass_glossy_indirect', T('光泽间接光'), 'Glossy Indirect', False, True),
    RL_entry('use_pass_indirect', T('间接光'), 'Indirect', False, False),
    RL_entry('use_pass_material_index', T('材质索引'), 'Material Index', False, True),
    RL_entry('use_pass_mist', T('雾场'), 'Mist', True, True),
    RL_entry('use_pass_normal', T('法向'), 'Normal', True, True),
    RL_entry('use_pass_object_index', T('对象索引'), 'Object Index', False, True),
    RL_entry('use_pass_shadow', T('阴影'), 'Shadow', False, True),
    RL_entry('use_pass_subsurface_color', T('次表面颜色'), 'Subsurface Color', True, True),
    RL_entry('use_pass_subsurface_direct', T('次表面直接光'), 'Subsurface Direct', True, True),
    RL_entry('use_pass_subsurface_indirect', T('次表面间接光'), 'Subsurface Indirect', False, True),
    RL_entry('use_pass_transmission_color', T('透射颜色'), 'Transmission Color', False, True),
    RL_entry('use_pass_transmission_direct', T('透射直接光'), 'Transmission Direct', False, True),
    RL_entry('use_pass_transmission_indirect', T('透射间接光'), 'Transmission Indirect', False, True),
    RL_entry('use_pass_uv', 'UV', 'UV', True, True),
    RL_entry('use_pass_vector', T('速度'), 'Vector', False, True),
    RL_entry('use_pass_z', 'Z', 'Depth', True, True),
)

# list of blend types of "Mix" nodes in a form that can be used as 'items' for EnumProperty.
# used list, not tuple for easy merging with other lists.
blend_types = [
    ('MIX', T('混合'), T('混合模式')),
    ('ADD', T('相加'), T('相加模式')),
    ('MULTIPLY', T('相乘'), T('相乘模式')),
    ('SUBTRACT', T('相减'), T('相减模式')),
    ('SCREEN', T('屏幕'), T('屏幕模式')),
    ('DIVIDE', T('相除'), T('相除模式')),
    ('DIFFERENCE', T('差值'), T('差值模式')),
    ('DARKEN', T('变暗'), T('变暗模式')),
    ('LIGHTEN', T('变亮'), T('变亮模式')),
    ('OVERLAY', T('叠加'), T('叠加模式')),
    ('DODGE', T('颜色减淡'), T('颜色减淡模式')),
    ('BURN', T('颜色加深'), T('颜色加深模式')),
    ('HUE', T('色相'), T('色相模式')),
    ('SATURATION', T('饱和度'), T('饱和度模式')),
    ('VALUE', T('明度'), T('明度模式')),
    ('COLOR', T('颜色'), T('颜色模式')),
    ('SOFT_LIGHT', T('柔光'), T('柔光模式')),
    ('LINEAR_LIGHT', T('线性光'), T('线性光模式')),
]

# list of operations of "Math" nodes in a form that can be used as 'items' for EnumProperty.
# used list, not tuple for easy merging with other lists.
operations = [
    ('ADD', T('相加'), T('相加模式')),
    ('SUBTRACT', T('相减'), T('相减模式')),
    ('MULTIPLY', T('相乘'), T('相乘模式')),
    ('DIVIDE', T('相除'), T('相除模式')),
    ('MULTIPLY_ADD', T('乘加运算'), T('乘加运算模式')),
    ('SINE', T('正弦'), T('正弦模式')),
    ('COSINE', T('余弦'), T('余弦模式')),
    ('TANGENT', T('正切'), T('正切模式')),
    ('ARCSINE', T('反正弦'), T('反正弦模式')),
    ('ARCCOSINE', T('反余弦'), T('反余弦模式')),
    ('ARCTANGENT', T('反正切'), T('反正切模式')),
    ('ARCTAN2', T('反正切2'), T('反正切2模式')),
    ('SINH', T('双曲正弦'), T('双曲正弦模式')),
    ('COSH', T('双曲余弦'), T('双曲余弦模式')),
    ('TANH', T('双曲正切'), T('双曲正切模式')),
    ('POWER', T('幂运算'), T('幂运算模式')),
    ('LOGARITHM', T('对数'), T('对数模式')),
    ('SQRT', T('平方根'), T('平方根模式')),
    ('INVERSE_SQRT', T('平方根倒数'), T('平方根倒数模式')),
    ('EXPONENT', T('指数'), T('指数模式')),
    ('MINIMUM', T('最小值'), T('最小值模式')),
    ('MAXIMUM', T('最大值'), T('最大值模式')),
    ('LESS_THAN', T('小于'), T('小于模式')),
    ('GREATER_THAN', T('大于'), T('大于模式')),
    ('SIGN', T('符号'), T('符号模式')),
    ('COMPARE', T('比较'), T('比较模式')),
    ('SMOOTH_MIN', T('平滑最小值'), T('平滑最小值模式')),
    ('SMOOTH_MAX', T('平滑最大值'), T('平滑最大值模式')),
    ('FRACT', T('小数部分'), T('小数部分模式')),
    ('MODULO', T('取模'), T('取模模式')),
    ('SNAP', T('吸附'), T('吸附模式')),
    ('WRAP', T('包裹'), T('包裹模式')),
    ('PINGPONG', T('往复'), T('往复模式')),
    ('ABSOLUTE', T('绝对值'), T('绝对值模式')),
    ('ROUND', T('四舍五入'), T('四舍五入模式')),
    ('FLOOR', T('向下取整'), T('向下取整模式')),
    ('CEIL', T('向上取整'), T('向上取整模式')),
    ('TRUNCATE', T('截断'), T('截断模式')),
    ('RADIANS', T('转为弧度'), T('转为弧度模式')),
    ('DEGREES', T('转为角度'), T('转为角度模式')),
]

# Operations used by the geometry boolean node and join geometry node
geo_combine_operations = [
    ('JOIN', T('合并几何'), T('合并几何模式')),
    ('INTERSECT', T('交集'), T('交集模式')),
    ('UNION', T('并集'), T('并集模式')),
    ('DIFFERENCE', T('差集'), T('差集模式')),
]

# in NWBatchChangeNodes additional types/operations. Can be used as 'items' for EnumProperty.
# used list, not tuple for easy merging with other lists.
navs = [
    ('CURRENT', T('当前'), T('保持当前状态')),
    ('NEXT', T('下一个'), T('下一个混合类型/运算')),
    ('PREV', T('上一个'), T('上一个混合类型/运算')),
]

draw_color_sets = {
    "red_white": (
        (1.0, 1.0, 1.0, 0.7),
        (1.0, 0.0, 0.0, 0.7),
        (0.8, 0.2, 0.2, 1.0)
    ),
    "green": (
        (0.0, 0.0, 0.0, 1.0),
        (0.38, 0.77, 0.38, 1.0),
        (0.38, 0.77, 0.38, 1.0)
    ),
    "yellow": (
        (0.0, 0.0, 0.0, 1.0),
        (0.77, 0.77, 0.16, 1.0),
        (0.77, 0.77, 0.16, 1.0)
    ),
    "purple": (
        (0.0, 0.0, 0.0, 1.0),
        (0.38, 0.38, 0.77, 1.0),
        (0.38, 0.38, 0.77, 1.0)
    ),
    "grey": (
        (0.0, 0.0, 0.0, 1.0),
        (0.63, 0.63, 0.63, 1.0),
        (0.63, 0.63, 0.63, 1.0)
    ),
    "black": (
        (1.0, 1.0, 1.0, 0.7),
        (0.0, 0.0, 0.0, 0.7),
        (0.2, 0.2, 0.2, 1.0)
    )
}


def get_texture_node_types():
    return [
        "ShaderNodeTexBrick",
        "ShaderNodeTexChecker",
        "ShaderNodeTexEnvironment",
        "ShaderNodeTexGabor",
        "ShaderNodeTexGradient",
        "ShaderNodeTexIES",
        "ShaderNodeTexImage",
        "ShaderNodeTexMagic",
        "ShaderNodeTexMusgrave",
        "ShaderNodeTexNoise",
        "ShaderNodeTexSky",
        "ShaderNodeTexVoronoi",
        "ShaderNodeTexWave",
        "ShaderNodeTexWhiteNoise"
    ]


def nice_hotkey_name(punc):
    # convert the ugly string name into the actual character
    from bpy.types import KeyMapItem
    nice_name = {
        enum_item.identifier:
        enum_item.name
        for enum_item in KeyMapItem.bl_rna.properties['type'].enum_items
    }
    try:
        return nice_name[punc]
    except KeyError:
        return punc.replace("_", " ").title()
