# SPDX-FileCopyrightText: 2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import gpu
import time
import colorsys
from ctypes import Structure, POINTER, c_void_p, c_char, c_short, c_float, cast
from mathutils import Vector as Vec2
from gpu_extras.batch import batch_for_shader
from math import cos, sin, pi, sqrt, exp, hypot, isfinite

from .nodes import get_nodes_links, prefs_line_width, abs_node_location, dpi_fac, is_visible_socket

# --- GLSL Shaders ---

_SHADER_CACHE = {}
_RAINBOW_GAP_LIMIT = 64
_AREAS_TO_REDRAW = set()

def get_shader(name):
    if name in _SHADER_CACHE:
        return _SHADER_CACHE[name]
    
    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant('MAT4', 'ModelViewProjectionMatrix')
    
    if name == 'RAINBOW':
        iface = gpu.types.GPUStageInterfaceInfo("node_wrangler_rainbow_iface")
        iface.smooth('VEC2', 'v_uv')
        info.vertex_in(0, 'VEC2', 'pos')
        info.vertex_in(1, 'VEC2', 'uv')
        info.vertex_out(iface)
        info.push_constant('FLOAT', 'u_time')
        info.push_constant('FLOAT', 'u_alpha')
        info.push_constant('FLOAT', 'u_theme')
        info.fragment_out(0, 'VEC4', 'fragColor')
        
        info.vertex_source('''
            void main() {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
                v_uv = uv;
            }
        ''')
        
        info.fragment_source('''
            vec3 hsv2rgb(vec3 c) {
                vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
                vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
                return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
            }
            
            void main() {
                float v_progress = v_uv.x;
                float v_side = v_uv.y;
                
                float t = u_time * 0.5;
                float flow_phase = t * 3.0 - v_progress * 4.0;
                float hue = fract(flow_phase / 6.28318530718);
                
                float saturation = 0.9;
                float value = 0.95;
                
                float pulse_t = u_time * 1.0;
                float pulse_center = fract(pulse_t);
                float raw_dist = fract(pulse_center - v_progress);
                float pulse = 0.0;
                
                if (raw_dist > 0.5) {
                     float front_dist = 1.0 - raw_dist;
                     pulse = exp(-(front_dist * front_dist) / (2.0 * 0.01 * 0.01));
                } else {
                     pulse = exp(-(raw_dist * raw_dist) / (2.0 * 0.2 * 0.2));
                }
                
                float boost = 1.0 + 3.0 * pulse;
                float sat_damp = 1.0 - 0.95 * pulse;
                
                int theme = int(u_theme + 0.5);
                
                if (theme == 1) { // Cyberpunk
                    hue = mix(0.5, 0.83, smoothstep(-1.0, 1.0, sin(flow_phase * 1.5)));
                    saturation = 0.9;
                    value = 1.0;
                    boost = 1.0 + 4.0 * pulse;
                } else if (theme == 2) { // Gold
                    hue = mix(0.0, 0.15, smoothstep(-1.0, 1.0, sin(flow_phase * 0.5)));
                    saturation = 1.0;
                    value = 0.9;
                    boost = 1.0 + 2.0 * pulse;
                } else if (theme == 3) { // Matrix
                    hue = 0.33;
                    saturation = 1.0;
                    value = 0.2 + 0.8 * pulse;
                    boost = 1.0 + 5.0 * pulse;
                    sat_damp = 1.0;
                } else if (theme == 4) { // Ice
                    hue = mix(0.55, 0.65, smoothstep(-1.0, 1.0, sin(flow_phase * 0.8)));
                    saturation = mix(0.4, 0.8, pulse);
                    value = 0.9;
                    boost = 1.0 + 1.0 * pulse;
                    sat_damp = 1.0;
                } else if (theme == 5) { // Cute Pink
                    hue = mix(0.88, 0.98, smoothstep(-1.0, 1.0, sin(flow_phase * 1.2)));
                    saturation = mix(0.8, 0.95, pulse);
                    value = 1.0;
                    boost = 1.0 + 1.5 * pulse;
                    sat_damp = 1.0;
                }
                
                vec3 rgb = hsv2rgb(vec3(hue, saturation * sat_damp, min(1.0, value * boost)));
                
                // Anti-aliasing using V coordinate
                float dist = abs(v_side);
                float alpha_edge = 1.0 - smoothstep(0.85, 1.0, dist);
                
                fragColor = vec4(rgb, u_alpha * alpha_edge);
            }
        ''')
        
    elif name == 'SMOOTH_COLOR':
        iface = gpu.types.GPUStageInterfaceInfo("node_wrangler_smooth_color_iface")
        iface.smooth('VEC2', 'v_uv')
        info.vertex_in(0, 'VEC2', 'pos')
        info.vertex_in(1, 'VEC2', 'uv')
        info.vertex_out(iface)
        info.push_constant('VEC4', 'color')
        info.fragment_out(0, 'VEC4', 'fragColor')
        
        info.vertex_source('''
            void main() {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
                v_uv = uv;
            }
        ''')
        
        info.fragment_source('''
            void main() {
                float dist = abs(v_uv.y);
                float alpha_edge = 1.0 - smoothstep(0.85, 1.0, dist);
                fragColor = vec4(color.rgb, color.a * alpha_edge);
            }
        ''')

    elif name == 'SDF_CIRCLE':
        iface = gpu.types.GPUStageInterfaceInfo("node_wrangler_sdf_circle_iface")
        iface.smooth('VEC2', 'v_uv')
        info.vertex_in(0, 'VEC2', 'pos')
        info.vertex_in(1, 'VEC2', 'uv')
        info.vertex_out(iface)
        info.push_constant('VEC4', 'color')
        info.fragment_out(0, 'VEC4', 'fragColor')
        
        info.vertex_source('''
            void main() {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
                v_uv = uv;
            }
        ''')
        
        info.fragment_source('''
            void main() {
                float dist = length(v_uv);
                float delta = 1.5 * fwidth(dist);
                float alpha = 1.0 - smoothstep(1.0 - delta, 1.0, dist);
                fragColor = vec4(color.rgb, color.a * alpha);
            }
        ''')
        
    elif name == 'SDF_ROUND_BOX':
        iface = gpu.types.GPUStageInterfaceInfo("node_wrangler_sdf_round_box_iface")
        iface.smooth('VEC2', 'v_uv')
        info.vertex_in(0, 'VEC2', 'pos')
        info.vertex_in(1, 'VEC2', 'uv')
        info.vertex_out(iface)
        info.push_constant('VEC4', 'color')
        info.push_constant('VEC2', 'rect_half_size')
        info.push_constant('FLOAT', 'radius')
        info.fragment_out(0, 'VEC4', 'fragColor')
        
        info.vertex_source('''
            void main() {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
                v_uv = uv;
            }
        ''')
        
        info.fragment_source('''
            float sdRoundBox(vec2 p, vec2 b, float r) {
                vec2 q = abs(p) - b + r;
                return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
            }
            
            void main() {
                float dist = sdRoundBox(v_uv, rect_half_size, radius);
                float delta = 1.5 * fwidth(dist);
                float alpha = 1.0 - smoothstep(-delta, 0.0, dist);
                fragColor = vec4(color.rgb, color.a * alpha);
            }
        ''')
    
    elif name == 'SDF_ROUND_BOX_OUTLINE':
        iface = gpu.types.GPUStageInterfaceInfo("node_wrangler_sdf_round_box_outline_iface")
        iface.smooth('VEC2', 'v_uv')
        info.vertex_in(0, 'VEC2', 'pos')
        info.vertex_in(1, 'VEC2', 'uv')
        info.vertex_out(iface)
        info.push_constant('VEC4', 'color')
        info.push_constant('VEC2', 'rect_half_size')
        info.push_constant('FLOAT', 'radius')
        info.push_constant('FLOAT', 'stroke_width')
        info.fragment_out(0, 'VEC4', 'fragColor')
        
        info.vertex_source('''
            void main() {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
                v_uv = uv;
            }
        ''')
        
        info.fragment_source('''
            float sdRoundBox(vec2 p, vec2 b, float r) {
                vec2 q = abs(p) - b + r;
                return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
            }
            
            void main() {
                float dist = sdRoundBox(v_uv, rect_half_size, radius);
                float delta = 1.5 * fwidth(dist);
                float d = abs(dist);
                float alpha = 1.0 - smoothstep(stroke_width, stroke_width + delta, d);
                fragColor = vec4(color.rgb, color.a * alpha);
            }
        ''')

    elif name == 'RAINBOW_BOX_OUTLINE':
        iface = gpu.types.GPUStageInterfaceInfo("node_wrangler_rainbow_box_outline_iface")
        iface.smooth('VEC2', 'v_uv')
        info.vertex_in(0, 'VEC2', 'pos')
        info.vertex_in(1, 'VEC2', 'uv')
        info.vertex_out(iface)
        info.push_constant('FLOAT', 'u_time')
        info.push_constant('FLOAT', 'u_alpha')
        info.push_constant('FLOAT', 'u_theme')
        info.push_constant('VEC2', 'rect_half_size')
        info.push_constant('FLOAT', 'radius')
        info.push_constant('FLOAT', 'stroke_width')
        GAP_LIMIT = _RAINBOW_GAP_LIMIT
        info.typedef_source(f'''
            struct NodeWranglerRainbowOutlineUBO {{
                vec4 gaps[{GAP_LIMIT}];
                vec4 meta;
            }};
        ''')
        info.uniform_buf(0, 'NodeWranglerRainbowOutlineUBO', 'u_params')
        info.fragment_out(0, 'VEC4', 'fragColor')
        
        info.vertex_source('''
            void main() {
                gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
                v_uv = uv;
            }
        ''')
        
        info.fragment_source(f'''
            float sdRoundBox(vec2 p, vec2 b, float r) {{
                vec2 q = abs(p) - b + r;
                return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
            }}
            
            void main() {{
                float uv_len = length(v_uv);
                vec2 dir = uv_len > 1e-6 ? (v_uv / uv_len) : vec2(1.0, 0.0);
                float cos_a = dir.x;
                float sin_a = dir.y;

                float flow_t = u_time * 1.05;
                int theme = int(u_theme + 0.5);
                vec3 rgb;
                
                if (theme == 1) {{ // Cyberpunk
                    float mix_val = 0.5 + 0.5 * (cos_a * cos(flow_t*2.0) - sin_a * sin(flow_t*2.0));
                    rgb = mix(vec3(0.0, 1.0, 1.0), vec3(1.0, 0.0, 1.0), mix_val);
                }} else if (theme == 2) {{ // Gold
                    float mix_val = 0.5 + 0.5 * (cos_a * cos(flow_t*0.5) - sin_a * sin(flow_t*0.5));
                    rgb = mix(vec3(1.0, 0.2, 0.0), vec3(1.0, 0.8, 0.0), mix_val);
                }} else if (theme == 3) {{ // Matrix
                    rgb = vec3(0.0, 0.8, 0.2);
                }} else if (theme == 4) {{ // Ice
                    float mix_val = 0.5 + 0.5 * (cos_a * cos(flow_t*0.5) - sin_a * sin(flow_t*0.5));
                    rgb = mix(vec3(0.3, 0.7, 1.0), vec3(0.8, 0.9, 1.0), mix_val);
                }} else if (theme == 5) {{ // Cute Pink
                    float mix_val = 0.5 + 0.5 * (cos_a * cos(flow_t*1.2) - sin_a * sin(flow_t*1.2));
                    rgb = mix(vec3(1.0, 0.3, 0.6), vec3(1.0, 0.7, 0.9), mix_val);
                }} else {{ // Classic
                    vec3 phase = flow_t + vec3(0.0, 2.09439510239, 4.18879020479);
                    vec3 cos_p = cos(phase);
                    vec3 sin_p = sin(phase);
                    vec3 wave = cos_a * cos_p - sin_a * sin_p;
                    rgb = 0.5 + 0.5 * wave;
                }}

                float pulse_ang = fract(u_time * 0.7) * 6.28318530718;
                vec2 pulse_dir = vec2(cos(pulse_ang), sin(pulse_ang));
                float dp = clamp(dot(dir, pulse_dir), -1.0, 1.0);
                float pulse_dist = acos(dp);
                float pulse = exp(-(pulse_dist * pulse_dist) / (2.0 * 0.4 * 0.4));

                if (theme == 3) {{ // Matrix specific pulse
                    rgb = mix(rgb * 0.3, vec3(0.5, 1.0, 0.5), pulse);
                    rgb = min(vec3(1.0), rgb * (1.0 + 3.0 * pulse));
                }} else {{
                    rgb = mix(rgb, vec3(1.0), 0.85 * pulse);
                    rgb = min(vec3(1.0), rgb * (1.0 + 1.8 * pulse));
                }}
                
                // SDF Logic for Alpha
                float sdf_dist = sdRoundBox(v_uv, rect_half_size, radius);
                float delta = 1.5 * fwidth(sdf_dist);
                float d = abs(sdf_dist);
                float alpha_shape = 1.0 - smoothstep(stroke_width, stroke_width + delta, d);
                
                // Gap logic
                int gap_count = int(u_params.meta.y + 0.5);
                if (gap_count > 0) {{
                    float min_gap_dist = 1e5;
                    for (int i = 0; i < {GAP_LIMIT}; i++) {{
                        if (i >= gap_count) {{
                            break;
                        }}
                        min_gap_dist = min(min_gap_dist, length(v_uv - u_params.gaps[i].xy));
                    }}
                    float gap_r = u_params.meta.x;
                    float gap_mask = smoothstep(gap_r, gap_r + delta, min_gap_dist);
                    alpha_shape *= gap_mask;
                }}

                fragColor = vec4(rgb, u_alpha * alpha_shape);
            }}
        ''')
    
    else:
        return None

    try:
        shader = gpu.shader.create_from_info(info)
    except Exception as e:
        print(f"Node Wrangler Shader Error ({name}): {e}")
        return None
        
    _SHADER_CACHE[name] = shader
    return shader

# --- Native Link Curve Calculation ---

OFFSET_RUNTIME = 456 if bpy.app.version >= (5, 1, 0) else 520

class BNodeSocketRuntime(Structure):
    _fields_ = [
        ("declaration", c_void_p),
        ("changed_flag", c_void_p),
        ("total_inputs", c_short),
        ("pad", c_char * 6),
        ("location", c_float * 2),
    ]

class BNodeSocket(Structure):
    _fields_ = [
        ("pad", c_char * OFFSET_RUNTIME),
        ("runtime", POINTER(BNodeSocketRuntime)),
    ]

SEG_MIN = 5
SEG_MAX = 80
_BEZIER_TABLE = {}
_UNIT_CIRCLE_VERTS = [(cos(i * 2 * pi / 12), sin(i * 2 * pi / 12)) for i in range(13)]

def get_curving_factor():
    """
    Get the curvature factor from preferences.
    """
    try:
        curving = bpy.context.preferences.themes[0].node_editor.noodle_curving
        return curving / 10.0
    except Exception:
        return 0.0

def get_adaptive_handle_offset(x1, y1, x2, y2, curv_factor):
    """
    Calculate handle offset using slope-based clamping.
    curv_factor: Normalized curvature (0.0 - 1.0)
    """
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    if dx == 0:
        slope = float('inf')
    else:
        slope = dy / dx
    
    # Raw curving (0-10) for clamp calculation
    raw_curving = curv_factor * 10.0
    
    clamp_factor = min(1.0, slope * (4.5 - 0.25 * raw_curving))
    return (curv_factor * 10.0) * 0.1 * dx * clamp_factor

def _view2d_zoom_factor(v2d):
    try:
        x0, y0 = v2d.region_to_view(0.0, 0.0)
        x1, y1 = v2d.region_to_view(1.0, 0.0)
        dx = abs(x1 - x0)
        if dx <= 1e-8:
            return 1.0
        z = 1.0 / dx
        return max(0.35, min(6.0, z))
    except Exception:
        return 1.0

def init_bezier_table():
    if _BEZIER_TABLE:
        return
    for seg in range(SEG_MIN, SEG_MAX + 1):
        coeffs = []
        for i in range(seg + 1):
            t = i / seg
            inv_t = 1.0 - t
            a = inv_t ** 3
            b = 3 * (inv_t ** 2) * t
            c = 3 * inv_t * (t ** 2)
            d = t ** 3
            coeffs.append((a, b, c, d))
        _BEZIER_TABLE[seg] = coeffs

init_bezier_table()

def _native_socket_y_offset():
    return 0.5 * dpi_fac()

def get_native_link_points(link, v2d, curv):
    """
    Calculate Bezier points for a link using Blender's native logic and memory access.
    Returns a list of (x, y) tuples in region coordinates.
    """
    fs, ts = link.from_socket, link.to_socket
    try:
        # Check enabled state
        # Note: from_socket/to_socket in Python API are BNodeSocket wrappers.
        # We need to access the underlying C struct.
        if not (fs.enabled and ts.enabled):
            return None
        
        sf = BNodeSocket.from_address(fs.as_pointer())
        st = BNodeSocket.from_address(ts.as_pointer())
        
        # Check if runtime is valid (not null)
        if not (sf.runtime and st.runtime):
            return None
            
        rf, rt = sf.runtime.contents, st.runtime.contents
        x1, y1 = rf.location[0], rf.location[1]
        x2, y2 = rt.location[0], rt.location[1]
    except Exception:
        return None

    y_off = _native_socket_y_offset()
    y1 += y_off
    y2 += y_off

    h = get_adaptive_handle_offset(x1, y1, x2, y2, curv)
    
    p0 = (x1, y1)
    p1 = (x1 + h, y1)
    p2 = (x2 - h, y2)
    p3 = (x2, y2)
    
    v2r = v2d.view_to_region
    # We need to convert control points to region space to calculate segment count based on screen length
    # But wait, the user's snippet converts result points to region.
    # It also converts p0 and p3 to region to calculate 'approx'.
    
    r0 = v2r(*p0, clip=False)
    r3 = v2r(*p3, clip=False)
    
    approx = abs(r3[0] - r0[0]) + abs(r3[1] - r0[1])
    seg = max(SEG_MIN, min(SEG_MAX, int(approx * 0.055)))
    
    coeff = _BEZIER_TABLE.get(seg)
    if not coeff:
        # Fallback if table missing or out of bounds (shouldn't happen with correct range)
        seg = SEG_MAX
        coeff = _BEZIER_TABLE[SEG_MAX]
        
    pts = []
    for (a, b, c, d) in coeff:
        x = a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0]
        y = a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]
        pts.append(v2r(x, y, clip=False))
        
    return pts

def _get_line_strip_geometry(vertices, width):
    """
    Generate triangle strip vertices for a polyline.
    Returns (pos_list, uv_list)
    """
    if len(vertices) < 2:
        return [], []
    
    pos_data = []
    uv_data = []
    
    half_w = width * 0.5
    count = len(vertices)
    
    # Pre-convert to Vector for easier math if they aren't already
    verts = [Vec2(v) for v in vertices]
    
    for i in range(count):
        curr_p = verts[i]
        
        # Calculate tangent
        if i == 0:
            tangent = (verts[1] - curr_p).normalized()
        elif i == count - 1:
            tangent = (curr_p - verts[i-1]).normalized()
        else:
            t1 = (curr_p - verts[i-1]).normalized()
            t2 = (verts[i+1] - curr_p).normalized()
            tangent = (t1 + t2).normalized()
            
        # Normal (rotate 90 degrees)
        normal = Vec2((-tangent.y, tangent.x))
        
        p0 = curr_p + normal * half_w
        p1 = curr_p - normal * half_w
        
        pos_data.append((p0.x, p0.y))
        pos_data.append((p1.x, p1.y))
        
        # U = progress along line (0 to 1)
        # V = side (-1 to 1)
        u = i / (count - 1)
        uv_data.append((u, 1.0))  # Top
        uv_data.append((u, -1.0)) # Bottom
        
    return pos_data, uv_data


def draw_batch_lines(all_lines_data, shader_name, width, color=None, time_sec=0.0, alpha_mod=1.0, theme_id=0):
    """
    Batch draw multiple lines using TRI_STRIP with degenerate triangles for connection.
    all_lines_data: list of vertex lists
    """
    if not all_lines_data:
        return

    shader = get_shader(shader_name)
    if not shader:
        return

    all_pos = []
    all_uv = []
    
    # Generate geometry for each line and stitch them
    for vertices in all_lines_data:
        if not vertices or len(vertices) < 2:
            continue
            
        pos, uv = _get_line_strip_geometry(vertices, width)
        if not pos:
            continue
            
        if all_pos:
            # Degenerate triangles to jump between strips
            # Repeat last vertex of previous strip
            all_pos.append(all_pos[-1])
            all_uv.append(all_uv[-1])
            
            # Repeat first vertex of new strip
            all_pos.append(pos[0])
            all_uv.append(uv[0])
            
        all_pos.extend(pos)
        all_uv.extend(uv)
        
    if not all_pos:
        return

    # Create batch
    if shader_name == 'RAINBOW':
        batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": all_pos, "uv": all_uv})
    elif shader_name == 'SMOOTH_COLOR':
        batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": all_pos, "uv": all_uv})
    else:
        return

    shader.bind()
    
    if shader_name == 'RAINBOW':
        shader.uniform_float("u_time", time_sec % 1000.0)
        shader.uniform_float("u_alpha", alpha_mod)
        shader.uniform_float("u_theme", float(theme_id))
    elif shader_name == 'SMOOTH_COLOR':
        shader.uniform_float("color", color)
        
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_batch_circles(centers, radius, color):
    """
    Batch draw multiple circles using TRIS (Quads).
    """
    if not centers:
        return

    shader = get_shader('SDF_CIRCLE')
    if not shader:
        return
        
    r = radius * prefs_line_width()
    size = r + 2.0
    uv_scale = size / r
    
    all_pos = []
    all_uv = []
    
    # Pre-calculate offsets
    # Quad structure (2 triangles):
    # 0---1
    # | / |
    # 2---3
    # Order: 0, 2, 1, 1, 2, 3 (CCW)
    
    # Offsets
    o0 = (-size, -size) # TL
    o1 = ( size, -size) # TR
    o2 = (-size,  size) # BL
    o3 = ( size,  size) # BR
    
    # UVs
    u0 = (-uv_scale, -uv_scale)
    u1 = ( uv_scale, -uv_scale)
    u2 = (-uv_scale,  uv_scale)
    u3 = ( uv_scale,  uv_scale)
    
    for (cx, cy) in centers:
        # Vertex positions
        p0 = (cx + o0[0], cy + o0[1])
        p1 = (cx + o1[0], cy + o1[1])
        p2 = (cx + o2[0], cy + o2[1])
        p3 = (cx + o3[0], cy + o3[1])
        
        # Triangle 1
        all_pos.extend([p0, p2, p1])
        all_uv.extend([u0, u2, u1])
        
        # Triangle 2
        all_pos.extend([p1, p2, p3])
        all_uv.extend([u1, u2, u3])
        
    batch = batch_for_shader(shader, 'TRIS', {"pos": all_pos, "uv": all_uv})
    
    shader.bind()
    shader.uniform_float("color", color)
    
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _rainbow_rgba(step_t, time_sec, theme_id=0):
    t = time_sec * 0.5
    pulse_t = time_sec * 1.0
    pulse_center = pulse_t % 1.0

    flow_phase = t * 3.0 - step_t * 4.0

    raw_dist = (pulse_center - step_t) % 1.0
    if raw_dist > 0.5:
        front_dist = 1.0 - raw_dist
        pulse = exp(-(front_dist * front_dist) / (2.0 * 0.01 * 0.01))
    else:
        pulse = exp(-(raw_dist * raw_dist) / (2.0 * 0.2 * 0.2))

    if theme_id == 1: # Cyberpunk
        hue = 0.5 + 0.33 * (0.5 + 0.5 * sin(flow_phase * 1.5))
        saturation = 0.9
        value = 1.0
        boost = 1.0 + 4.0 * pulse
        sat_damp = 1.0 - 0.95 * pulse
    elif theme_id == 2: # Gold
        hue = 0.15 * (0.5 + 0.5 * sin(flow_phase * 0.5))
        saturation = 1.0
        value = 0.9
        boost = 1.0 + 2.0 * pulse
        sat_damp = 1.0 - 0.95 * pulse
    elif theme_id == 3: # Matrix
        hue = 0.33
        saturation = 1.0
        value = 0.2 + 0.8 * pulse
        boost = 1.0 + 5.0 * pulse
        sat_damp = 1.0
    elif theme_id == 4: # Ice
        hue = 0.55 + 0.1 * (0.5 + 0.5 * sin(flow_phase * 0.8))
        saturation = 0.4 + 0.4 * pulse
        value = 0.9
        boost = 1.0 + 1.0 * pulse
        sat_damp = 1.0
    elif theme_id == 5: # Cute Pink
        hue = 0.88 + 0.1 * (0.5 + 0.5 * sin(flow_phase * 1.2))
        saturation = 0.85 + 0.15 * pulse
        value = 1.0
        boost = 1.0 + 1.5 * pulse
        sat_damp = 1.0
    else: # Classic
        hue = (flow_phase / (2 * pi)) % 1.0
        saturation = 0.65
        value = 0.95
        boost = 1.0 + 3.0 * pulse
        sat_damp = 1.0 - 0.95 * pulse

    r, g, b = colorsys.hsv_to_rgb(hue, saturation * sat_damp, min(1.0, value * boost))
    return (r, g, b, 1.0)


def draw_rainbow_strip(vertices, size, alpha_mod=1.0, time_sec=None, theme_id=0):
    if not vertices or len(vertices) < 2:
        return

    if time_sec is None:
        time_sec = time.time()
    
    shader = get_shader('RAINBOW')
    if not shader:
        return

    # Generate geometry
    width = max(3.0, size * prefs_line_width())
    pos_data, uv_data = _get_line_strip_geometry(vertices, width)
    
    if not pos_data:
        return

    batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": pos_data, "uv": uv_data})

    shader.bind()
    # Fix float precision issue in GLSL by wrapping time
    # Also ensures pulse calculation remains stable
    shader.uniform_float("u_time", time_sec % 1000.0)
    shader.uniform_float("u_alpha", alpha_mod)
    shader.uniform_float("u_theme", float(theme_id))
    
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_rainbow_line(x1, y1, x2, y2, size, segments=40, time_sec=None, theme_id=0):
    # Calculate length first
    length = sqrt((x2 - x1)**2 + (y2 - y1)**2)
    segments = max(20, int(length / 5)) 

    # Bezier curve control points
    curv_factor = get_curving_factor()

    if curv_factor <= 0.001:
        cx1, cy1 = x1, y1
        cx2, cy2 = x2, y2
    else:
        handle_len = get_adaptive_handle_offset(x1, y1, x2, y2, curv_factor)
        
        cx1 = x1 + handle_len
        cy1 = y1
        cx2 = x2 - handle_len
        cy2 = y2

    vertices = []
    for i in range(segments + 1):
        step_t = i / segments
        inv_t = 1 - step_t
        inv_t2 = inv_t * inv_t
        inv_t3 = inv_t2 * inv_t
        step_t2 = step_t * step_t
        step_t3 = step_t2 * step_t
        
        px = (inv_t3 * x1 +
              3 * inv_t2 * step_t * cx1 +
              3 * inv_t * step_t2 * cx2 +
              step_t3 * x2)
              
        py = (inv_t3 * y1 +
              3 * inv_t2 * step_t * cy1 +
              3 * inv_t * step_t2 * cy2 +
              step_t3 * y2)

        vertices.append((px, py))
        
    draw_rainbow_strip(vertices, size, time_sec=time_sec)


def draw_bezier_line(x1, y1, x2, y2, size, colour=(1.0, 1.0, 1.0, 0.7), segments=40):
    shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    shader.bind()
    shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
    shader.uniform_float("lineWidth", size * prefs_line_width())

    vertices = []
    
    # Calculate length to adjust segments
    length = sqrt((x2 - x1)**2 + (y2 - y1)**2)
    segments = max(10, int(length / 10))

    # Logic matching Blender's noodle curving
    curv_factor = get_curving_factor()

    if curv_factor <= 0.001:
        cx1, cy1 = x1, y1
        cx2, cy2 = x2, y2
    else:
        handle_len = get_adaptive_handle_offset(x1, y1, x2, y2, curv_factor)
        
        cx1 = x1 + handle_len
        cy1 = y1
        cx2 = x2 - handle_len
        cy2 = y2

    for i in range(segments + 1):
        step_t = i / segments
        inv_t = 1 - step_t
        inv_t2 = inv_t * inv_t
        inv_t3 = inv_t2 * inv_t
        step_t2 = step_t * step_t
        step_t3 = step_t2 * step_t
        
        px = (inv_t3 * x1 +
              3 * inv_t2 * step_t * cx1 +
              3 * inv_t * step_t2 * cx2 +
              step_t3 * x2)
              
        py = (inv_t3 * y1 +
              3 * inv_t2 * step_t * cy1 +
              3 * inv_t * step_t2 * cy2 +
              step_t3 * y2)
        vertices.append((px, py))

    # Uniform color
    draw_solid_strip_expanded(vertices, size, colour)


def draw_line(x1, y1, x2, y2, size, colour=(1.0, 1.0, 1.0, 0.7)):
    draw_solid_strip_expanded([(x1, y1), (x2, y2)], size, colour)


def draw_circle_2d_filled(mx, my, radius, colour=(1.0, 1.0, 1.0, 0.7)):
    shader = get_shader('SDF_CIRCLE')
    if not shader:
        return
        
    r = radius * prefs_line_width()
    # Expand slightly to account for AA
    size = r + 2.0 
    
    # Quad vertices
    vertices = [
        (mx - size, my - size),
        (mx + size, my - size),
        (mx - size, my + size),
        (mx + size, my + size),
    ]
    
    # UVs (-1 to 1) need to be mapped to the size
    # Actually, we can just pass UVs for the quad corners
    # (size/r) to keep 1.0 as the radius boundary
    uv_scale = size / r
    uvs = [
        (-uv_scale, -uv_scale),
        ( uv_scale, -uv_scale),
        (-uv_scale,  uv_scale),
        ( uv_scale,  uv_scale),
    ]
    
    batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": vertices, "uv": uvs})
    
    shader.bind()
    shader.uniform_float("color", colour)
    
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_rounded_node_border(node, radius=8, colour=(1.0, 1.0, 1.0, 0.7)):
    shader = get_shader('SDF_ROUND_BOX')
    if not shader:
        return

    radius_px = radius * prefs_line_width()
    
    nlocx, nlocy = abs_node_location(node)
    nlocx = (nlocx + 1) * dpi_fac()
    nlocy = (nlocy + 1) * dpi_fac()
    ndimx = node.dimensions.x
    ndimy = node.dimensions.y

    if node.type == 'REROUTE':
        nlocy -= 1
        ndimx = 0
        ndimy = 0
        radius_px += 6 * prefs_line_width() # Adjust relative to original logic

    v2r = bpy.context.region.view2d.view_to_region

    if node.hide and node.type not in {'REROUTE', 'FRAME'}:
        y_center = nlocy - (9.0 * dpi_fac())
        y_min = y_center - (ndimy * 0.5)
        y_max = y_center + (ndimy * 0.5)
        p1 = v2r(nlocx, y_min, clip=False)
        p2 = v2r(nlocx + ndimx, y_max, clip=False)
    else:
        p1 = v2r(nlocx, nlocy, clip=False)
        p2 = v2r(nlocx + ndimx, nlocy - ndimy, clip=False)

    if not p1 or not p2:
        return

    rmin_x = min(p1[0], p2[0])
    rmax_x = max(p1[0], p2[0])
    rmin_y = min(p1[1], p2[1])
    rmax_y = max(p1[1], p2[1])
    
    # Center and Half-Size in screen pixels
    center_x = (rmin_x + rmax_x) * 0.5
    center_y = (rmin_y + rmax_y) * 0.5
    
    hw = (rmax_x - rmin_x) * 0.5
    hh = (rmax_y - rmin_y) * 0.5
    
    # We want to draw a quad that covers the box + radius + padding
    pad = radius_px + 2.0
    
    vertices = [
        (center_x - hw - pad, center_y - hh - pad),
        (center_x + hw + pad, center_y - hh - pad),
        (center_x - hw - pad, center_y + hh + pad),
        (center_x + hw + pad, center_y + hh + pad),
    ]
    
    # UVs are local coordinates in pixels from center
    uvs = [
        (-hw - pad, -hh - pad),
        ( hw + pad, -hh - pad),
        (-hw - pad,  hh + pad),
        ( hw + pad,  hh + pad),
    ]
    
    batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": vertices, "uv": uvs})
    
    shader.bind()
    shader.uniform_float("color", colour)
    shader.uniform_float("rect_half_size", (hw, hh))
    shader.uniform_float("radius", radius_px)
    
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_rounded_node_outline(node, radius=8, stroke_width=2.0, colour=(1.0, 1.0, 1.0, 0.7)):
    shader = get_shader('SDF_ROUND_BOX_OUTLINE')
    if not shader:
        return

    radius_px = radius * prefs_line_width()
    stroke_px = max(0.0, stroke_width * prefs_line_width())

    nlocx, nlocy = abs_node_location(node)
    nlocx = (nlocx + 1) * dpi_fac()
    nlocy = (nlocy + 1) * dpi_fac()
    ndimx = node.dimensions.x
    ndimy = node.dimensions.y

    if node.type == 'REROUTE':
        nlocy -= 1
        ndimx = 0
        ndimy = 0
        radius_px += 6 * prefs_line_width()

    v2r = bpy.context.region.view2d.view_to_region

    if node.hide and node.type not in {'REROUTE', 'FRAME'}:
        y_center = nlocy - (9.0 * dpi_fac())
        y_min = y_center - (ndimy * 0.5)
        y_max = y_center + (ndimy * 0.5)
        p1 = v2r(nlocx, y_min, clip=False)
        p2 = v2r(nlocx + ndimx, y_max, clip=False)
    else:
        p1 = v2r(nlocx, nlocy, clip=False)
        p2 = v2r(nlocx + ndimx, nlocy - ndimy, clip=False)

    if not p1 or not p2:
        return

    rmin_x = min(p1[0], p2[0])
    rmax_x = max(p1[0], p2[0])
    rmin_y = min(p1[1], p2[1])
    rmax_y = max(p1[1], p2[1])

    center_x = (rmin_x + rmax_x) * 0.5
    center_y = (rmin_y + rmax_y) * 0.5

    hw = (rmax_x - rmin_x) * 0.5
    hh = (rmax_y - rmin_y) * 0.5

    pad = radius_px + stroke_px + 2.0

    vertices = [
        (center_x - hw - pad, center_y - hh - pad),
        (center_x + hw + pad, center_y - hh - pad),
        (center_x - hw - pad, center_y + hh + pad),
        (center_x + hw + pad, center_y + hh + pad),
    ]

    uvs = [
        (-hw - pad, -hh - pad),
        ( hw + pad, -hh - pad),
        (-hw - pad,  hh + pad),
        ( hw + pad,  hh + pad),
    ]

    batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": vertices, "uv": uvs})

    shader.bind()
    shader.uniform_float("color", colour)
    shader.uniform_float("rect_half_size", (hw, hh))
    shader.uniform_float("radius", radius_px)
    shader.uniform_float("stroke_width", stroke_px)

    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_rainbow_node_outline(node, radius=8, stroke_width=2.0, alpha_mod=1.0, time_sec=None, theme_id=0):
    shader = get_shader('RAINBOW_BOX_OUTLINE')
    if not shader:
        return

    if time_sec is None:
        time_sec = time.time()

    stroke_px = max(0.0, stroke_width * prefs_line_width() * 0.7)

    nlocx, nlocy = abs_node_location(node)
    nlocx = nlocx * dpi_fac()
    nlocy = nlocy * dpi_fac()
    ndimx = node.dimensions.x
    ndimy = node.dimensions.y

    v2r = bpy.context.region.view2d.view_to_region

    # Calculate view scale to keep radius proportional to node size
    p_ref_1 = v2r(nlocx, nlocy, clip=False)
    p_ref_2 = v2r(nlocx + 100.0, nlocy, clip=False)
    
    view_scale = 1.0
    if p_ref_1 and p_ref_2:
        view_scale = abs(p_ref_2[0] - p_ref_1[0]) / 100.0

    # Scale stroke width with zoom
    stroke_px *= view_scale
    
    # Use scaled radius
    radius_px = (radius - 2.0) * view_scale

    if node.type == 'REROUTE':
        nlocy -= 1
        ndimx = 0
        ndimy = 0
        radius_px += 4.0 * view_scale

    if node.hide and node.type not in {'REROUTE', 'FRAME'}:
        y_center = nlocy - (9.0 * dpi_fac())
        y_min = y_center - (ndimy * 0.5)
        y_max = y_center + (ndimy * 0.5)
        p1 = v2r(nlocx, y_min, clip=False)
        p2 = v2r(nlocx + ndimx, y_max, clip=False)
    else:
        p1 = v2r(nlocx, nlocy, clip=False)
        p2 = v2r(nlocx + ndimx, nlocy - ndimy, clip=False)

    if not p1 or not p2:
        return

    rmin_x = min(p1[0], p2[0])
    rmax_x = max(p1[0], p2[0])
    rmin_y = min(p1[1], p2[1])
    rmax_y = max(p1[1], p2[1])

    center_x = (rmin_x + rmax_x) * 0.5
    center_y = (rmin_y + rmax_y) * 0.5

    hw = (rmax_x - rmin_x) * 0.5
    hh = (rmax_y - rmin_y) * 0.5

    pad = radius_px + stroke_px + 2.0

    vertices = [
        (center_x - hw - pad, center_y - hh - pad),
        (center_x + hw + pad, center_y - hh - pad),
        (center_x - hw - pad, center_y + hh + pad),
        (center_x + hw + pad, center_y + hh + pad),
    ]

    uvs = [
        (-hw - pad, -hh - pad),
        ( hw + pad, -hh - pad),
        (-hw - pad,  hh + pad),
        ( hw + pad,  hh + pad),
    ]

    # Calculate gaps for sockets
    gaps = []
    gap_radius_px = 7.0 * view_scale
    
    # Only calculate if stroke is visible
    if stroke_px > 0.1:
        def collect_gaps(sockets, is_output):
            for i, socket in enumerate(sockets):
                if not socket.enabled or socket.hide:
                    continue
                if hasattr(socket, "is_icon_visible") and not socket.is_icon_visible:
                    continue
                lx, ly = get_socket_loc(node, is_output, i)
                pt = v2r(lx, ly, clip=False)
                if pt:
                    gaps.append((pt[0] - center_x, pt[1] - center_y + 0.5))

        collect_gaps(node.inputs, False)
        collect_gaps(node.outputs, True)

    gap_count = len(gaps)
    gap_limit = _RAINBOW_GAP_LIMIT
    if gap_count > gap_limit:
        gap_count = gap_limit
        gaps = gaps[:gap_limit]
    
    batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": vertices, "uv": uvs})

    shader.bind()
    shader.uniform_float("u_time", time_sec % 1000.0)
    shader.uniform_float("u_alpha", alpha_mod)
    shader.uniform_float("u_theme", float(theme_id))
    shader.uniform_float("rect_half_size", (hw, hh))
    shader.uniform_float("radius", radius_px)
    shader.uniform_float("stroke_width", stroke_px)

    ubo_floats = [0.0] * ((gap_limit + 1) * 4)
    for i, (gx, gy) in enumerate(gaps):
        base = i * 4
        ubo_floats[base] = gx
        ubo_floats[base + 1] = gy

    meta_base = gap_limit * 4
    ubo_floats[meta_base] = gap_radius_px
    ubo_floats[meta_base + 1] = float(gap_count)

    ubo_buf = gpu.types.Buffer('FLOAT', len(ubo_floats), ubo_floats)
    ubo = gpu.types.GPUUniformBuf(ubo_buf)
    shader.uniform_block("u_params", ubo)

    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def draw_callback_nodeoutline(self, context, mode):
    if self.mouse_path:
        gpu.state.blend_set('ALPHA')

        nodes, _links = get_nodes_links(context)

        if mode == "LINK":
            col_outer = (1.0, 0.2, 0.2, 0.4)
            col_inner = (0.0, 0.0, 0.0, 0.5)
            col_circle_inner = (0.3, 0.05, 0.05, 1.0)
        elif mode == "LINKMENU":
            col_outer = (0.4, 0.6, 1.0, 0.4)
            col_inner = (0.0, 0.0, 0.0, 0.5)
            col_circle_inner = (0.08, 0.15, .3, 1.0)
        elif mode == "MIX":
            col_outer = (0.2, 1.0, 0.2, 0.4)
            col_inner = (0.0, 0.0, 0.0, 0.5)
            col_circle_inner = (0.05, 0.3, 0.05, 1.0)

        m1x = self.mouse_path[0][0]
        m1y = self.mouse_path[0][1]
        m2x = self.mouse_path[-1][0]
        m2y = self.mouse_path[-1][1]

        n1 = nodes[context.scene.NWLazySource]
        n2 = nodes[context.scene.NWLazyTarget]

        if n1 == n2:
            col_outer = (0.4, 0.4, 0.4, 0.4)
            col_inner = (0.0, 0.0, 0.0, 0.5)
            col_circle_inner = (0.2, 0.2, 0.2, 1.0)

        draw_rounded_node_outline(n1, radius=6, stroke_width=2.0, colour=col_outer)
        draw_rounded_node_outline(n1, radius=5, stroke_width=1.0, colour=col_inner)
        draw_rounded_node_outline(n2, radius=6, stroke_width=2.0, colour=col_outer)
        draw_rounded_node_outline(n2, radius=5, stroke_width=1.0, colour=col_inner)

        draw_bezier_line(m1x, m1y, m2x, m2y, 7.5, col_outer)  # line outline
        draw_rainbow_line(m1x, m1y, m2x, m2y, 4.5)  # rainbow inner

        # circle outline
        draw_circle_2d_filled(m1x, m1y, 7, col_outer)
        draw_circle_2d_filled(m2x, m2y, 7, col_outer)

        # circle inner
        draw_circle_2d_filled(m1x, m1y, 5, col_circle_inner)
        draw_circle_2d_filled(m2x, m2y, 5, col_circle_inner)

        gpu.state.blend_set('NONE')
    
    # Self-driving redraw loop
    if hasattr(context, "area") and context.area:
        _AREAS_TO_REDRAW.add(context.area)
    if not bpy.app.timers.is_registered(force_redraw):
        bpy.app.timers.register(force_redraw, first_interval=0.03)


def force_redraw():
    try:
        if _AREAS_TO_REDRAW:
            for area in _AREAS_TO_REDRAW:
                try:
                    area.tag_redraw()
                except:
                    pass
            _AREAS_TO_REDRAW.clear()
        else:
            # Fallback if set is empty but timer running (shouldn't happen often)
            pass
    except:
        pass
    return None  # Run once, will be re-registered by draw callback if needed


def get_socket_loc(node, is_output, index):
    """Estimate socket location in node logical space."""
    
    # Try to get exact location from C struct first (Best method)
    try:
        sockets = node.outputs if is_output else node.inputs
        if index < len(sockets):
            socket = sockets[index]
            # Offset logic provided by user
            offset = 520 
            if bpy.app.version >= (5, 1, 0): 
                offset = 456  # 520-64 5.1 removed short_label
            
            # Read directly from memory
            # Returns (x, y) in node logical space
            vec = Vec2((c_float * 2).from_address(c_void_p.from_address(socket.as_pointer() + offset).value + 24))
            return vec.x, vec.y
    except Exception:
        # Fallback to heuristic if anything fails
        pass

    if node.type == 'REROUTE':
        # Reroute nodes are small dots, just use their location
        # Apply the same coordinate transform logic as standard nodes if needed
        nlocx, nlocy = abs_node_location(node)
        fac = dpi_fac()
        return (nlocx + 1) * fac, (nlocy + 1) * fac
    
    # Standard Node
    fac = dpi_fac()
    nlocx, nlocy = abs_node_location(node)
    
    # Apply coordinate scaling consistent with draw_rounded_node_border
    base_x = nlocx * fac
    base_y = nlocy * fac
    
    # X Position
    if is_output:
        x = base_x + node.dimensions.x
    else:
        x = base_x
        
    # Y Position
    # Heuristics based on user feedback
    # Header is roughly 30-32 units high (scaled)
    # Sockets are roughly 21-22 units high (scaled)
    # We target the center of the socket
    
    header_height = 32.0 * fac
    socket_height = 21.0 * fac
    
    # Start below the header
    y = base_y - header_height
    
    # Find index among ENABLED sockets only
    sockets = node.outputs if is_output else node.inputs
    enabled_sockets = [s for s in sockets if s.enabled]
    
    try:
        real_idx = enabled_sockets.index(sockets[index])
    except (ValueError, IndexError):
        real_idx = 0
        
    # Move down to specific socket
    # Center vertically: Move down by N sockets, then move down half a socket height
    y = y - (real_idx * socket_height) - (socket_height * 0.5)

    # Fine-tuning based on side
    # Output was too low -> Move UP (add to Y)
    # Input was too high -> Move DOWN (subtract from Y)
    if is_output:
        y += 0.5 * fac  # Output correction
    else:
        y -= 0.5 * fac  # Input correction
    
    return x, y


def draw_solid_strip_expanded(vertices, size, color):
    if not vertices or len(vertices) < 2:
        return
    
    width = max(3.0, size * prefs_line_width())
    pos_data, uv_data = _get_line_strip_geometry(vertices, width)
    if not pos_data:
        return
        
    shader = get_shader('SMOOTH_COLOR')
    if not shader:
        # Fallback to basic uniform color if shader fails
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": pos_data})
        shader.bind()
        shader.uniform_float("color", color)
    else:
        batch = batch_for_shader(shader, 'TRI_STRIP', {"pos": pos_data, "uv": uv_data})
        shader.bind()
        shader.uniform_float("color", color)
    
    gpu.state.blend_set('ALPHA')
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _get_socket_index_cached(cache, node, socket, is_output):
    key = (node.as_pointer(), bool(is_output))
    socket_map = cache.get(key)
    if socket_map is None:
        sockets = node.outputs if is_output else node.inputs
        socket_map = {s.as_pointer(): i for i, s in enumerate(sockets)}
        cache[key] = socket_map
    return socket_map.get(socket.as_pointer())


def draw_callback_highlight_connections():
    context = bpy.context
    # Ensure we are in a Node Editor
    if context.space_data is None or context.space_data.type != 'NODE_EDITOR':
        return

    # Check if we have a node tree
    tree = context.space_data.node_tree
    if not tree:
        return

    # Check for selected nodes
    # We only want to draw if there are selected nodes
    selected_nodes = context.selected_nodes
    if not selected_nodes:
        return

    # Check preference
    addon_id = (__package__ or "").split(".", 1)[0] or "colorful_node_wrangler"
    addon = context.preferences.addons.get(addon_id)
    if addon and not getattr(addon.preferences, "show_connected_rainbow", True):
        return

    # Theme and Performance properties
    theme_id = 0
    if addon:
        try:
            theme_id = int(getattr(addon.preferences, "visual_theme", "0"))
        except ValueError:
            theme_id = 0

    # Performance Mode Optimization (Scheme A)
    if addon and getattr(addon.preferences, "render_quality", "PERFORMANCE") == "PERFORMANCE":
        if len(selected_nodes) > 5:
            active_node = context.active_node
            selected_nodes = [active_node] if active_node and active_node in selected_nodes else []
            if not selected_nodes:
                return

    thickness_mul = getattr(getattr(addon, "preferences", None), "connected_rainbow_thickness", 1.0) if addon else 1.0        
    # Collect unique links to highlight
    # (link, is_output_from_selected)
    initial_links = set()
    
    # Draw Rainbow Outline for selected nodes
    time_sec = time.time()
    for node in selected_nodes:
        draw_rainbow_node_outline(node, radius=8, stroke_width=2.1, alpha_mod=0.8, time_sec=time_sec, theme_id=theme_id)

    for node in selected_nodes:
        # Output links (Flowing OUT from selected node)
        for output in node.outputs:
            if output.enabled:
                for link in output.links:
                    initial_links.add(link)
                    
        # Input links (Flowing INTO selected node)
        for input in node.inputs:
            if input.enabled:
                for link in input.links:
                    initial_links.add(link)
    
    if not initial_links:
        # Self-driving redraw loop even if no links, to animate border
        if hasattr(context, "area") and context.area:
            _AREAS_TO_REDRAW.add(context.area)
        if not bpy.app.timers.is_registered(force_redraw):
            bpy.app.timers.register(force_redraw, first_interval=0.03)
        return

    links_to_draw = set()
    links_to_process = list(initial_links)
    
    while links_to_process:
        link = links_to_process.pop(0)
        if link in links_to_draw:
            continue
        links_to_draw.add(link)
        
        # Pass through REROUTE nodes
        if link.to_node.type == 'REROUTE':
            for output in link.to_node.outputs:
                if output.enabled:
                    for l in output.links:
                        if l not in links_to_draw:
                            links_to_process.append(l)
                            
        if link.from_node.type == 'REROUTE':
            for input in link.from_node.inputs:
                if input.enabled:
                    for l in input.links:
                        if l not in links_to_draw:
                            links_to_process.append(l)

    gpu.state.blend_set('ALPHA')
    
    # Get curving preference
    curv_factor = get_curving_factor()
    v2d = context.region.view2d
    zoom = _view2d_zoom_factor(v2d)
    region = context.region
    viewport_w = region.width
    viewport_h = region.height

    # Constants
    time_sec = time.time()
    backing_col = (0.0, 0.0, 0.0, 0.55)
    start_col = _rainbow_rgba(0.0, time_sec, theme_id)
    end_col = _rainbow_rgba(1.0, time_sec, theme_id)
    
    # Dimensions
    width_backing = 9.0 * zoom
    width_rainbow = 4.5 * zoom
    
    r_backing_circle = 7.0 * zoom
    r_rainbow_circle = 5.0 * zoom

    margin = (max(width_backing, r_backing_circle * 2.0) * prefs_line_width() * thickness_mul) + 16.0

    socket_index_cache = {}

    # Pre-calculate widths
    width_backing_px = max(2.0, width_backing * prefs_line_width() * thickness_mul)
    width_rainbow_px = max(1.5, width_rainbow * prefs_line_width() * thickness_mul)

    for link in links_to_draw:
        fs = getattr(link, "from_socket", None)
        ts = getattr(link, "to_socket", None)
        if not fs or not ts:
            continue
        if not (is_visible_socket(fs) and is_visible_socket(ts)):
            continue

        n1 = link.from_node
        n2 = link.to_node

        from_idx = _get_socket_index_cached(socket_index_cache, n1, fs, True)
        to_idx = _get_socket_index_cached(socket_index_cache, n2, ts, False)
        if from_idx is None or to_idx is None:
            continue

        l1x, l1y = get_socket_loc(n1, True, from_idx)
        l2x, l2y = get_socket_loc(n2, False, to_idx)

        m1x, m1y = v2d.view_to_region(l1x, l1y, clip=False)
        m2x, m2y = v2d.view_to_region(l2x, l2y, clip=False)

        dx = m2x - m1x
        dy = m2y - m1y

        if curv_factor <= 0.001:
            c1x, c1y = m1x, m1y
            c2x, c2y = m2x, m2y
        else:
            handle_len = get_adaptive_handle_offset(m1x, m1y, m2x, m2y, curv_factor)
            c1x, c1y = m1x + handle_len, m1y
            c2x, c2y = m2x - handle_len, m2y

        min_x = min(m1x, m2x, c1x, c2x)
        max_x = max(m1x, m2x, c1x, c2x)
        min_y = min(m1y, m2y, c1y, c2y)
        max_y = max(m1y, m2y, c1y, c2y)
        if (
            max_x < -margin
            or min_x > viewport_w + margin
            or max_y < -margin
            or min_y > viewport_h + margin
        ):
            continue

        pts = get_native_link_points(link, v2d, curv_factor)
        if pts and len(pts) >= 2:
            sx, sy = pts[0]
            tx, ty = pts[-1]
            if not (isfinite(sx) and isfinite(sy) and isfinite(tx) and isfinite(ty)):
                pts = None
            else:
                threshold = max(120.0, 60.0 * zoom) * prefs_line_width()
                if hypot(sx - m1x, sy - m1y) > threshold or hypot(tx - m2x, ty - m2y) > threshold:
                    pts = None
        else:
            pts = None

        if not pts:
            length = sqrt(dx * dx + dy * dy)
            segments = max(10, int(length / 10))

            if curv_factor <= 0.001:
                cx1, cy1 = m1x, m1y
                cx2, cy2 = m2x, m2y
            else:
                handle_len = get_adaptive_handle_offset(m1x, m1y, m2x, m2y, curv_factor)

                cx1 = m1x + handle_len
                cy1 = m1y
                cx2 = m2x - handle_len
                cy2 = m2y

            pts = []
            for i in range(segments + 1):
                step_t = i / segments
                inv_t = 1 - step_t
                inv_t2 = inv_t * inv_t
                inv_t3 = inv_t2 * inv_t
                step_t2 = step_t * step_t
                step_t3 = step_t2 * step_t

                px = (inv_t3 * m1x +
                      3 * inv_t2 * step_t * cx1 +
                      3 * inv_t * step_t2 * cx2 +
                      step_t3 * m2x)

                py = (inv_t3 * m1y +
                      3 * inv_t2 * step_t * cy1 +
                      3 * inv_t * step_t2 * cy2 +
                      step_t3 * m2y)
                pts.append((px, py))

        if not pts or len(pts) < 2:
            continue

        sx, sy = pts[0]
        tx, ty = pts[-1]
        
        # Draw Immediately (Backing then Rainbow) to ensure correct layering
        # 1. Backing
        draw_batch_lines([pts], 'SMOOTH_COLOR', width_backing_px, backing_col)
        draw_batch_circles([(sx, sy), (tx, ty)], r_backing_circle * thickness_mul, backing_col)
        
        # 2. Rainbow
        draw_batch_lines([pts], 'RAINBOW', width_rainbow_px, time_sec=time_sec, theme_id=theme_id)
        draw_batch_circles([(sx, sy)], r_rainbow_circle * thickness_mul, start_col)
        draw_batch_circles([(tx, ty)], r_rainbow_circle * thickness_mul, end_col)

    gpu.state.blend_set('NONE')

    # Self-driving redraw loop
    if hasattr(context, "area") and context.area:
        _AREAS_TO_REDRAW.add(context.area)
    if not bpy.app.timers.is_registered(force_redraw):
        bpy.app.timers.register(force_redraw, first_interval=0.03)
