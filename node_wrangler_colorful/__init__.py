'''
Author: error: git config user.name && git config user.email & please set dead value or install git
Date: 2026-03-18 02:23:48
LastEditors: error: git config user.name && git config user.email & please set dead value or install git
LastEditTime: 2026-03-18 04:33:26
FilePath: \Translate\colorful_node_wrangler\__init__.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
# SPDX-FileCopyrightText: 2013-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Node Wrangler Colorful",
    # This is now displayed as the maintainer, so show the foundation.
    # "author": "Bartek Skorupa, Greg Zaal, Sebastian Koenig, Christian Brinkmann, Florian Meyer", # Original Authors
    "author": "Blender Foundation、Blender超级技术交流社✨、NACEN✨",
    "version": (4, 0, 2),
    "blender": (5, 0, 0),
    "location": "Node Editor Toolbar or Shift-W",
    "description": "Various tools to enhance and speed up node-based workflow",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/node/node_wrangler.html",
    "support": 'OFFICIAL',
    "category": "Node",
}

import bpy
from bpy.props import (
    IntProperty,
    StringProperty,
)

from . import operators
from . import preferences
from . import interface
from .utils.draw import draw_callback_highlight_connections

_draw_handle = None

def redraw_timer():
    # Use bpy.data to avoid context issues in timers
    for wm in bpy.data.window_managers:
        for window in wm.windows:
            for area in window.screen.areas:
                if area.type == 'NODE_EDITOR':
                    area.tag_redraw()
    return 0.02

def register():
    # props
    bpy.types.Scene.NWBusyDrawing = StringProperty(
        name="Busy Drawing!",
        default="",
        description="用于存储第一个鼠标位置的内部属性")
    bpy.types.Scene.NWLazySource = StringProperty(
        name="Lazy Source!",
        default="x",
        description="用于存储快速连接操作中第一个节点的内部属性")
    bpy.types.Scene.NWLazyTarget = StringProperty(
        name="Lazy Target!",
        default="x",
        description="用于存储快速连接操作中最后一个节点的内部属性")
    bpy.types.Scene.NWSourceSocket = IntProperty(
        name="Source Socket!",
        default=0,
        description="用于存储快速连接操作中源接口的内部属性")

    operators.register()
    interface.register()
    preferences.register()

    # Register draw handler for connection highlighting
    global _draw_handle
    _draw_handle = bpy.types.SpaceNodeEditor.draw_handler_add(
        draw_callback_highlight_connections, (), 'WINDOW', 'POST_PIXEL')
    
    # if not bpy.app.timers.is_registered(redraw_timer):
    #     bpy.app.timers.register(redraw_timer)


def unregister():
    global _draw_handle
    if _draw_handle:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
        
    # if bpy.app.timers.is_registered(redraw_timer):
    #     bpy.app.timers.unregister(redraw_timer)

    preferences.unregister()
    interface.unregister()
    operators.unregister()

    # props
    del bpy.types.Scene.NWBusyDrawing

    del bpy.types.Scene.NWLazySource
    del bpy.types.Scene.NWLazyTarget
    del bpy.types.Scene.NWSourceSocket
