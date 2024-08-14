# by Maki - 2024

import bpy
import struct
from collections import namedtuple

# =====CONFIGURATION

file = 'D:/_PROJECTS/battledat/c0m042.dat'
SCALE = 4096.0  # 4096.0 for FF8 - that's what we usually use
SKIP_TEXTURES = True  # set to True if you don't want to load textures


# =====FUN


# ====== SKELETON (sec 1) =============

def read_skeleton(_ptr_skeleton):
    return 0


## ====== GEOMETRY (sec 2) =============

class Vertex:
    def __init__(self, x, y, z):
        self.x = x / SCALE
        self.y = y / SCALE
        self.z = z / SCALE


class Triangle:
    def __init__(self, v1, v2, v3, uv1, uv2, tex_id, uv3, tex_id_2):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.u1 = uv1 & 0x00FF
        self.v1 = (uv1 & 0xFF00) >> 8
        self.u2 = uv2 & 0x00FF
        self.v2 = (uv2 & 0xFF00) >> 8
        self.tex_id = tex_id
        self.u3 = uv3 & 0x00FF
        self.v3 = (uv3 & 0xFF00) >> 8
        self.tex_id_2 = tex_id_2


class Quad:
    def __init__(self, v1, v2, v3, v4, uv1, uv2, uv3, uv4, tex_id, tex_id_2):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.v4 = v4
        self.u1 = uv1 & 0x00FF
        self.v1 = (uv1 & 0xFF00) >> 8
        self.tex_id = tex_id
        self.u2 = uv2 & 0x00FF
        self.v2 = (uv2 & 0xFF00) >> 8
        self.tex_id_2 = tex_id_2
        self.u3 = uv3 & 0x00FF
        self.v3 = (uv3 & 0xFF00) >> 8
        self.u4 = uv4 & 0x00FF
        self.v4 = (uv4 & 0xFF00) >> 8


class ObjectData:
    def __init__(self, vertex_data, triangles, quads):
        self.vertex_data = vertex_data
        self.triangles = triangles
        self.quads = quads


class VertexData:
    def __init__(self, bone_id, vertices):
        self.bone_id = bone_id
        self.vertices = vertices


def read_vertex_data(_ptr_vertex_data):  # _ptr_vertex_data is useless here, but I keep it for consistency
    bone_id = struct.unpack('H', fd.read(2))[0]
    num_vertices = struct.unpack('H', fd.read(2))[0]
    vertices = [Vertex(*struct.unpack('3h', fd.read(6))) for _ in range(num_vertices)]
    print('Bone ID: ' + str(bone_id) + ', Number of vertices: ' + str(num_vertices))
    return VertexData(bone_id, vertices)


def read_object_data(_ptr_object):
    fd.seek(_ptr_object, 0)
    num_vertex_data = struct.unpack('H', fd.read(2))[0]
    print('Number of vertex data: ' + str(num_vertex_data))
    vertex_data = [read_vertex_data(fd.tell()) for _ in range(num_vertex_data)]
    seek_pos = 4 - (fd.tell() % 4)  # align to 4 bytes
    fd.seek(seek_pos, 1)
    num_triangles = struct.unpack('H', fd.read(2))[0]
    print('Number of triangles: ' + str(num_triangles))
    num_quads = struct.unpack('H', fd.read(2))[0]
    print('Number of quads: ' + str(num_quads))
    triangles = [Triangle(*struct.unpack('8H', fd.read(16))) for _ in range(num_triangles)]
    quads = [Quad(*struct.unpack('10H', fd.read(20))) for _ in range(num_quads)]
    
    return 0


def read_geometry(_ptr_geometry):
    fd.seek(_ptr_geometry, 0)
    num_objects = struct.unpack('I', fd.read(4))[0]
    ptr_objects = [struct.unpack('I', fd.read(4))[0] + _ptr_geometry for _ in range(num_objects)]
    total_vertices = struct.unpack('I', fd.read(4))[0]
    print('Number of objects: ' + str(num_objects) + ', total vertices: ' + str(total_vertices))
    objects = [read_object_data(ptr) for ptr in ptr_objects]

    return 0


# ====== ANIMATION (sec 3) =============

def read_animation(_ptr_animation):
    return 0


# ====== TEXTURE (sec 11) =============

# 8BPP TIM was 1555 ABGR, right?
def read_clut(ptr):
    colors_buffer = fd.read(512)
    return [((color & 0x1F) * 8, (color >> 5 & 0x1F) * 8, (color >> 10 & 0x1F) * 8, (color >> 15) * 255)
            for color in struct.unpack('256H', colors_buffer)]


def read_tim(ptr):
    fd.seek(ptr, 0)
    magic = struct.unpack('I', fd.read(4))[0]
    if magic != 0x10:
        raise Exception('Invalid TIM magic: ' + str(magic))

    tim_type = struct.unpack('I', fd.read(4))[0]
    if tim_type != 0x09:
        raise Exception('Unsupported TIM type: ' + str(tim_type))

    clut_size = struct.unpack('I', fd.read(4))[0] - 12
    pal_x = struct.unpack('H', fd.read(2))[0]
    pal_y = struct.unpack('H', fd.read(2))[0]

    num_colors = struct.unpack('H', fd.read(2))[0]
    if num_colors != 256:
        raise Exception('Invalid number of colors: ' + str(num_colors))

    num_cluts = struct.unpack('H', fd.read(2))[0]
    if num_cluts * num_colors * 2 != clut_size:  # just to be sure
        raise Exception('Invalid CLUT size: ' + str(clut_size) + ', expected ' + str(num_cluts * num_colors))

    cluts = []
    for _ in range(num_cluts):
        cluts.append(read_clut(fd.tell()))

    print("Clut parsed: " + str(len(cluts)) + " cluts")

    img_size = struct.unpack('I', fd.read(4))[0]
    img_x = struct.unpack('H', fd.read(2))[0]
    img_y = struct.unpack('H', fd.read(2))[0]
    img_w = struct.unpack('H', fd.read(2))[0] * 2
    img_h = struct.unpack('H', fd.read(2))[0]

    # read image data
    img_buffer = fd.read(img_w * img_h)
    print('TIM: ' + str(img_w) + 'x' + str(img_h))

    if SKIP_TEXTURES:
        return 0  # skip textures if desired

    # create image
    img = bpy.data.images.new('TIM', img_w, img_h)
    img.pixels = [0] * img_w * img_h * 4
    for y in range(img_h):
        for x in range(img_w):
            i = (y * img_w + x) * 4
            flipped_i = ((img_h - 1 - y) * img_w + x) * 4
            r, g, b, a = cluts[img_buffer[i // 4] // 256][img_buffer[i // 4] % 256]
            img.pixels[flipped_i:flipped_i + 4] = [r / 255.0, g / 255.0, b / 255.0, a / 255.0]


def read_textures(_ptr_texture):
    fd.seek(_ptr_texture, 0)
    num_textures = struct.unpack('I', fd.read(4))[0]
    print('Number of textures: ' + str(num_textures))
    ptr_textures = [struct.unpack('I', fd.read(4))[0] + _ptr_texture for _ in range(num_textures)]
    for ptr in ptr_textures:
        read_tim(ptr)
    return 0


# ===== MAIN =========


fd = open(file, 'rb')
if not fd:
    raise Exception('File not found')

print('Opened file: ' + file)

# 1. Read header - it should have 11 sections
header = struct.unpack('I', fd.read(4))[0]
if header != 0x0B:
    raise Exception('Invalid header. Expected 11 sections, got ' + str(header))

ptr_skeleton = struct.unpack('I', fd.read(4))[0]
ptr_geometry = struct.unpack('I', fd.read(4))[0]
ptr_animation = struct.unpack('I', fd.read(4))[0]
fd.seek(7 * 4, 1)  # skip 7 sections
ptr_texture = struct.unpack('I', fd.read(4))[0]
ptr_eof = struct.unpack('I', fd.read(4))[0]

fd.seek(0, 2)  # seek to end
eof = fd.tell()
if ptr_eof != eof:
    raise Exception('Invalid EOF pointer. Expected ' + str(eof) + ', got ' + str(ptr_eof))

read_textures(ptr_texture)  # This creates the blender textures
geometry = read_geometry(ptr_geometry)

fd.close()
