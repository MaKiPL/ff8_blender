# by Maki - 2024

import bpy
import struct

# =====CONFIGURATION

file = 'D:/_PROJECTS/battledat/c0m042.dat'


# =====FUN


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

    # create image
    img = bpy.data.images.new('TIM', img_w, img_h)
    img.pixels = [0] * img_w * img_h * 4
    for y in range(img_h):
        for x in range(img_w):
            i = (y * img_w + x) * 4
            flipped_i = ((img_h - 1 - y) * img_w + x) * 4
            r, g, b, a = cluts[img_buffer[i // 4] // 256][img_buffer[i // 4] % 256]
            img.pixels[flipped_i:flipped_i + 4] = [r / 255.0, g / 255.0, b / 255.0, a / 255.0]

    return 0


def read_textures(_ptr_texture):
    fd.seek(_ptr_texture, 0)
    num_textures = struct.unpack('I', fd.read(4))[0]
    print('Number of textures: ' + str(num_textures))
    ptr_textures = [struct.unpack('I', fd.read(4))[0] + _ptr_texture for _ in range(num_textures)]
    for ptr in ptr_textures:
        read_tim(ptr)
    return 0


# =====MAIN


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

read_textures(ptr_texture)

fd.close()
