"""Bounded structural probes for observed FFBE BISHAMON files.

No BMB timeline/player is implemented. Unknown fields stay explicitly unknown.
M3R decoding supports only the validated one-material, 36-byte vertex layout.
"""
import math
import re
import struct


def ibmb_info(body):
    if len(body)<128 or body[:4]!=b'IBMB':raise ValueError('Not a complete IBMB header')
    words=struct.unpack_from('<24I',body)
    start,end=words[22:24]
    if not 128<=start<end<=len(body):raise ValueError('IBMB name-region bounds')
    names=[];cursor=start
    while cursor<end:
        if all(v==0xBA for v in body[cursor:end]):break
        stop=body.find(b'\x00',cursor,end)
        if stop<0:raise ValueError('Unterminated IBMB name')
        value=body[cursor:stop]
        if value:
            try:text=value.decode('ascii')
            except UnicodeDecodeError:raise ValueError('Unsupported IBMB name encoding')
            if not all(32<=v<127 for v in value):raise ValueError('Unsupported IBMB name bytes')
            names.append({'offset':cursor,'name':text})
        cursor=stop+1
    return {'magic':'IBMB','bytes':len(body),'raw_tag_04':words[1],'raw_tag_08':words[2],
            'raw_count_10':words[4],'raw_count_14':words[5],
            'name_region':[start,end],'names':names,
            'header_words':[{'offset':i*4,'value':n} for i,n in enumerate(words)],
            'timeline_decoded':False,'material_binding_decoded':False,
            'note':'Raw tags/counts are observed fields, not a published BMB version/type specification.'}


def m3r_mesh(body):
    if len(body)<152 or body[:4]!=b'BR3M':raise ValueError('Not a complete BR3M file')
    h=struct.unpack_from('<16I',body)
    version,meshes=h[1:3]
    names,material,indices,vertices,tail,end,declared=h[4:11]
    if version not in (34,35) or meshes!=1:raise ValueError('Unsupported M3R version/mesh layout')
    if not 64<=names<=material<indices<vertices<tail<=end==declared==len(body):raise ValueError('M3R section bounds')
    if material+88!=indices:raise ValueError('Unsupported M3R material record size')
    stride,count,base,index_count=struct.unpack_from('<4I',body,material+32)
    if stride!=36 or not 0<count<=100000 or base!=0 or not 0<index_count<=300000 or index_count%3:
        raise ValueError('Unsupported M3R vertex/index declaration')
    vertex_end=vertices+count*stride
    if vertex_end>tail or tail-vertex_end not in (0,8) or any(v!=0xBA for v in body[vertex_end:tail]) or indices+index_count*2>vertices:raise ValueError('M3R buffer lengths')
    face_indices=list(struct.unpack_from('<'+'H'*index_count,body,indices))
    if max(face_indices)>=count:raise ValueError('M3R index out of range')
    positions=[];normals=[];uvs=[];colors=[]
    for i in range(count):
        p=vertices+i*stride
        xyz=struct.unpack_from('<3f',body,p);color=struct.unpack_from('<I',body,p+12)[0]
        normal=struct.unpack_from('<3f',body,p+16);uv=struct.unpack_from('<2f',body,p+28)
        if not all(math.isfinite(v) for v in (*xyz,*normal,*uv)):raise ValueError('Non-finite M3R geometry')
        if not .9<=sum(v*v for v in normal)<=1.1:raise ValueError('Unvalidated M3R normal layout')
        positions.extend(xyz);normals.extend(normal);uvs.extend(uv);colors.append(color)
    raw_names=body[names:material].split(b'\x00')
    strings=[n.decode('ascii') for n in raw_names if n and all(32<=v<127 for v in n)]
    return {'schema':1,'magic':'BR3M','raw_version':version,'vertices':count,'triangles':index_count//3,
            'positions':positions,'normals':normals,'uvs':uvs,'vertex_colors_raw':colors,'indices':face_indices,
            'texture_names':strings,'bounds':[[min(positions[k::3]),max(positions[k::3])] for k in range(3)],
            'sections':{'names':names,'material':material,'indices':indices,'vertices':vertices,'uninterpreted_tail':tail},
            'uninterpreted_tail_bytes':end-tail,'material_words':list(struct.unpack_from('<22I',body,material)),
            'appearance_verified':False,'timeline_present_in_decoded_geometry':False}


# Observed serialization layouts only; these are not general BISHAMON readers.
IBMB_RECORD_SIZES = {0x51: {0: 768, 3: 1984, 6: 1952},
                     0x01030101: {0: 704, 2: 2128, 3: 1840, 6: 1904}}


def ibmb_records(body):
    """Walk the complete pre-name region without assigning animation semantics.

    Child counts give a consistent preorder tree. On the newer layout the
    Memorial reader independently corroborates this traversal. On tag 0x51
    parent links remain an inference, not a recovered runtime hierarchy.
    """
    info = ibmb_info(body)
    sizes = IBMB_RECORD_SIZES.get(info['raw_tag_04'])
    if sizes is None:
        raise ValueError('Unsupported IBMB record layout')
    cursor = 0x60
    end = info['name_region'][0]
    records = []
    stack = []
    while cursor < end:
        if len(records) >= 4096 or cursor + 32 > end:
            raise ValueError('IBMB record bounds/count')
        kind, size, children = struct.unpack_from('<3I', body, cursor)
        if sizes.get(kind) != size or cursor + size > end:
            raise ValueError('Unsupported IBMB record type/size')
        while stack and stack[-1][1] == 0:
            stack.pop()
        if records and not stack:
            raise ValueError('IBMB disconnected preorder tree')
        if children > 4096:
            raise ValueError('IBMB child count')
        parent = stack[-1][0] if stack else None
        if stack:
            stack[-1][1] -= 1
        records.append({'offset': cursor, 'raw_type': kind, 'size': size,
                        'raw_child_count_08': children, 'preorder_parent_candidate': parent})
        if children:
            stack.append([cursor, children])
        cursor += size
    if any(remaining for _, remaining in stack):
        raise ValueError('IBMB incomplete preorder tree')
    return {'records': records, 'region': [0x60, end],
            'hierarchy_status': 'consistent preorder interpretation; runtime binding not established',
            'timeline_decoded': False}


def ibmb_resource_tables(body):
    """Offset tables corroborated ONLY for the 0x01030101 reader variant.

    Names are dependencies, not proof of a particular model/texture node binding.
    """
    info = ibmb_info(body)
    if info['raw_tag_04'] != 0x01030101 or info['raw_tag_08'] != 0x41:
        raise ValueError('Unsupported/unfixed IBMB resource-table layout')
    names = {row['offset']: row['name'] for row in info['names']}
    base = info['name_region'][1]
    tables = {}
    for label, count_field, offset_field in [('texture_dependencies', 0x10, 0x20),
                                             ('model_dependencies', 0x14, 0x24)]:
        count = struct.unpack_from('<I', body, count_field)[0]
        offset = struct.unpack_from('<I', body, offset_field)[0]
        start = base + offset
        if count > 4096 or start < base or start + count * 8 > len(body):
            raise ValueError('IBMB resource-table bounds')
        rows = []
        for i in range(count):
            field = start + i * 8
            relative = struct.unpack_from('<Q', body, field)[0]
            absolute = info['name_region'][0] + relative
            if absolute not in names:
                raise ValueError('IBMB resource reference is not a name boundary')
            rows.append({'index': i, 'field_offset': field, 'name_offset': absolute,
                         'name': names[absolute]})
        tables[label] = rows
    return tables


def ibmb_word_differences(left, right):
    """Exact aligned differences; float interpretation is only a candidate."""
    a, b = ibmb_records(left), ibmb_records(right)
    if len(left) != len(right) or a != b or len(left) % 4:
        raise ValueError('Incompatible IBMB comparison layouts')
    rows = []
    for offset in range(0, len(left), 4):
        x, y = struct.unpack_from('<I', left, offset)[0], struct.unpack_from('<I', right, offset)[0]
        if x == y:
            continue
        node = next((r for r in a['records'] if r['offset'] <= offset < r['offset'] + r['size']), None)
        floats = [struct.unpack('<f', struct.pack('<I', v))[0] for v in (x, y)]
        rows.append({'offset': offset, 'left_u32': x, 'right_u32': y,
                     'finite_float_candidates': floats if all(math.isfinite(v) for v in floats) else None,
                     'record_offset': node['offset'] if node else None,
                     'raw_type': node['raw_type'] if node else None,
                     'record_relative_offset': offset-node['offset'] if node else None})
    return rows
