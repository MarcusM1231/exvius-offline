"""Validate PNG chunks, scanlines and actual transparent pixels without raster conversion."""
import struct
import zlib


def png_info(body, require_transparency=True, raster=None, maximum_dimension=2048):
    if maximum_dimension not in (2048,4096):raise ValueError('Unsupported PNG dimension budget')
    if not body.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Expected PNG signature')
    chunks = []
    position = 8
    while position < len(body):
        if position + 12 > len(body):
            raise ValueError('Truncated PNG chunk')
        length = struct.unpack_from('>I', body, position)[0]
        end = position + length + 12
        if end > len(body):
            raise ValueError('PNG chunk exceeds file')
        kind = body[position + 4:position + 8]
        data = body[position + 8:end - 4]
        if zlib.crc32(kind + data) != struct.unpack_from('>I', body, end - 4)[0]:
            raise ValueError('PNG chunk checksum mismatch')
        chunks.append((kind, data))
        position = end
        if kind == b'IEND':
            break
    if not chunks or chunks[0][0] != b'IHDR' or chunks[-1] != (b'IEND', b'') or position != len(body):
        raise ValueError('Invalid PNG chunk ordering/end')
    if sum(k == b'IHDR' for k, _ in chunks) != 1 or len(chunks[0][1]) != 13:
        raise ValueError('Invalid PNG header')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunks[0][1])
    if not 0 < width <= maximum_dimension or not 0 < height <= maximum_dimension or compression or filtering or interlace:
        raise ValueError('Unsupported PNG dimensions/interlace')
    if color == 3 and depth in (1, 2, 4, 8):
        channels = 1
    elif color in (0, 2, 4, 6) and depth == 8:
        channels = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    else:
        raise ValueError('Unsupported PNG color/depth')
    palette = next((d for k, d in chunks if k == b'PLTE'), b'')
    alpha = next((d for k, d in chunks if k == b'tRNS'), b'')
    if color == 3 and (not palette or len(palette) % 3 or len(palette) > 768 or len(alpha) > len(palette) // 3):
        raise ValueError('Invalid PNG palette')
    row_size = (width * channels * depth + 7) // 8
    bpp = max(1, (channels * depth + 7) // 8)
    compressed = b''.join(d for k, d in chunks if k == b'IDAT')
    expected = (row_size + 1) * height
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, expected + 1)
    if len(raw) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Invalid PNG image-data length')
    if raster is not None:
        # Optional build-time accelerator: structural/CRC/zlib checks above stay
        # identical. Pillow supplies the fully decoded scanlines in C.
        if raster.size != (width,height) or any(raw[y*(row_size+1)]>4 for y in range(height)):
            raise ValueError('Invalid decoded PNG dimensions/filter')
        if color == 3 and (raster.mode != 'P' or any(count and index>=len(palette)//3 for index,count in enumerate(raster.histogram()))):
            raise ValueError('PNG pixel exceeds palette')
        histogram=raster.convert('RGBA').getchannel('A').histogram()
        transparent=sum(histogram[:255])
        if require_transparency and not transparent:raise ValueError('PNG has no actual transparent pixels')
        return {'width':width,'height':height,'bit_depth':depth,'color_type':color,'transparent_pixels':transparent}
    previous = bytearray(row_size)
    transparent = 0
    def paeth(a, b, c):
        p = a + b - c
        distances = (abs(p-a), abs(p-b), abs(p-c))
        return (a, b, c)[distances.index(min(distances))]
    for y in range(height):
        start = y * (row_size + 1)
        mode = raw[start]
        if mode > 4:
            raise ValueError('Invalid PNG row filter')
        row = bytearray(raw[start + 1:start + 1 + row_size])
        if mode:
            for x in range(row_size):
                a = row[x-bpp] if x >= bpp else 0
                b = previous[x]
                c = previous[x-bpp] if x >= bpp else 0
                if mode == 1: correction = a
                elif mode == 2: correction = b
                elif mode == 3: correction = (a+b)//2
                else: correction = paeth(a,b,c)
                row[x] = (row[x] + correction) & 255
        for x in range(width):
            if color == 3:
                shift = 8 - depth - (x * depth) % 8
                index = (row[(x * depth)//8] >> shift) & ((1 << depth)-1)
                if index >= len(palette)//3:
                    raise ValueError('PNG pixel exceeds palette')
                transparent += index < len(alpha) and alpha[index] < 255
            elif color in (4, 6):
                transparent += row[x*channels+channels-1] < 255
            elif color == 0 and len(alpha) == 2:
                transparent += row[x] == int.from_bytes(alpha, 'big')
            elif color == 2 and len(alpha) == 6:
                transparent += tuple(row[x*3:x*3+3]) == struct.unpack('>HHH', alpha)
        previous = row
    if require_transparency and not transparent:
        raise ValueError('PNG has no actual transparent pixels')
    return {'width': width, 'height': height, 'bit_depth': depth, 'color_type': color,
            'transparent_pixels': transparent}
