"""Binary STL in mm -> one faceted solid STEP AP214; verify using OpenCASCADE.

No scaling, healing, remeshing, or overwrite. Does not create native SLDPRT.
Dependencies: numpy, gmsh (including its native DLL).
"""
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import argparse
import hashlib
import json
import struct
import sys
import tempfile
import numpy as np


def read_mesh(source):
    data = source.read_bytes()
    if len(data) < 84:
        raise ValueError('Expected a binary STL with at least one triangle')
    count = struct.unpack_from('<I', data, 80)[0]
    if count == 0 or len(data) != 84 + count * 50:
        raise ValueError('Only exact-length binary STL is supported; ASCII requires a separate conversion')
    triangles = np.array([struct.unpack_from('<12fH', data, 84 + 50*i)[3:12]
                          for i in range(count)], dtype=float).reshape(-1, 3, 3)
    if not np.isfinite(triangles).all():
        raise ValueError('Non-finite coordinates')
    cross = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    if np.any(np.linalg.norm(cross, axis=1) <= 1e-12):
        raise ValueError('Degenerate triangles')
    vertices, indices = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
    indices = indices.reshape(-1, 3)
    edges = defaultdict(list)
    adjacency = [[] for _ in range(count)]
    for face, ids in enumerate(indices):
        for a, b in zip(ids, np.roll(ids, -1)):
            edges[tuple(sorted((int(a), int(b))))].append((face, int(a), int(b)))
    for uses in edges.values():
        if len(uses) != 2 or uses[0][1:] != uses[1][1:][::-1]:
            raise ValueError('Mesh is open, non-manifold, or inconsistently oriented; no automatic repair')
        a, b = uses[0][0], uses[1][0]
        adjacency[a].append(b)
        adjacency[b].append(a)
    seen, pending = {0}, [0]
    while pending:
        for neighbor in adjacency[pending.pop()]:
            if neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    if len(seen) != count:
        raise ValueError('Expected one connected shell; multiple shells need a separate decision')
    shifted = triangles - vertices.mean(axis=0)
    volume = float(np.einsum('ij,ij->i', shifted[:, 0], np.cross(shifted[:, 1], shifted[:, 2])).sum()/6)
    if volume <= 0:
        raise ValueError('Volume is non-positive; inspect orientation')
    bounds = np.array([vertices.min(axis=0), vertices.max(axis=0)])
    report = dict(source_file=str(source), source_sha256=hashlib.sha256(data).hexdigest(),
                  units='mm', triangles=count, vertices=len(vertices), edges=len(edges),
                  connected_shells=1, closed=True, consistently_oriented=True,
                  euler_characteristic=len(vertices)-len(edges)+count,
                  bounds_mm=bounds.tolist(), size_mm=(bounds[1]-bounds[0]).tolist(),
                  mesh_volume_mm3=volume)
    return triangles, report


def write_brep(triangles, path):
    records = []

    def add(s):
        records.append(s)
        return f'#{len(records)}'

    def number(v):
        s = format(float(v), '.15g').replace('e', 'E')
        if '.' not in s and 'E' not in s:
            s += '.'
        return s

    def vec(v):
        return '(' + ','.join(number(x) for x in v) + ')'

    def refs(v):
        return '(' + ','.join(v) + ')'

    app = add("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
    add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,{app})")
    pc = add(f"PRODUCT_CONTEXT('',{app},'mechanical')")
    product = add(f"PRODUCT('Mesh part','Mesh part','Solid from source STL',{refs([pc])})")
    formation = add(f"PRODUCT_DEFINITION_FORMATION('1','',{product})")
    context = add(f"PRODUCT_DEFINITION_CONTEXT('part definition',{app},'design')")
    definition = add(f"PRODUCT_DEFINITION('design','',{formation},{context})")
    shape = add(f"PRODUCT_DEFINITION_SHAPE('','',{definition})")
    millimetre = add('(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))')
    radian = add('(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))')
    steradian = add('(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())')
    uncertainty = add(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-6),{millimetre},'distance_accuracy_value','topology tolerance in mm')")
    representation_context = add(f"(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(({uncertainty}))GLOBAL_UNIT_ASSIGNED_CONTEXT(({millimetre},{radian},{steradian}))REPRESENTATION_CONTEXT('','3D'))")
    origin = add("CARTESIAN_POINT('',(0.,0.,0.))")
    zdir = add("DIRECTION('',(0.,0.,1.))")
    xdir = add("DIRECTION('',(1.,0.,0.))")
    axis = add(f"AXIS2_PLACEMENT_3D('',{origin},{zdir},{xdir})")

    points, vertices, edges = {}, {}, {}
    faces = []
    for tri in triangles:
        keys = [tuple(p) for p in tri]
        for p in keys:
            if p not in points:
                points[p] = add(f"CARTESIAN_POINT('',{vec(p)})")
                vertices[p] = add(f"VERTEX_POINT('',{points[p]})")
        oriented = []
        for p, q in zip(keys, keys[1:] + keys[:1]):
            key = tuple(sorted((p, q)))
            if key not in edges:
                a, b = key
                direction = np.subtract(b, a)
                direction /= np.linalg.norm(direction)
                dr = add(f"DIRECTION('',{vec(direction)})")
                vr = add(f"VECTOR('',{dr},1.)")
                ln = add(f"LINE('',{points[a]},{vr})")
                edges[key] = add(f"EDGE_CURVE('',{vertices[a]},{vertices[b]},{ln},.T.)")
            sense = '.T.' if p == key[0] else '.F.'
            oriented.append(add(f"ORIENTED_EDGE('',*,*,{edges[key]},{sense})"))
        loop = add(f"EDGE_LOOP('',{refs(oriented)})")
        bound = add(f"FACE_OUTER_BOUND('',{loop},.T.)")
        u = tri[1] - tri[0]
        u /= np.linalg.norm(u)
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        normal /= np.linalg.norm(normal)
        nd = add(f"DIRECTION('',{vec(normal)})")
        ud = add(f"DIRECTION('',{vec(u)})")
        placement = add(f"AXIS2_PLACEMENT_3D('',{points[keys[0]]},{nd},{ud})")
        plane = add(f"PLANE('',{placement})")
        faces.append(add(f"ADVANCED_FACE('',({bound}),{plane},.T.)"))

    shell = add(f"CLOSED_SHELL('',{refs(faces)})")
    solid = add(f"MANIFOLD_SOLID_BREP('Mesh solid',{shell})")
    representation = add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('',({axis},{solid}),{representation_context})")
    add(f"SHAPE_DEFINITION_REPRESENTATION({shape},{representation})")
    header = "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('Solid BREP from verified STL; millimetres'),'2;1');\n"
    header += f"FILE_NAME('mesh.step','{datetime.now().isoformat(timespec='seconds')}',(''),(''),'STL to AP214 BREP','CAD exchange','');\n"
    header += "FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\nENDSEC;\nDATA;\n"
    path.write_text(header + ''.join(f'#{i}={s};\n' for i, s in enumerate(records, 1)) + 'ENDSEC;\nEND-ISO-10303-21;\n', encoding='ascii')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--units', choices=['mm'], required=True,
                        help='Explicit declaration: source STL coordinates are millimetres')
    parser.add_argument('--expected-size', nargs=3, type=float, metavar=('X', 'Y', 'Z'))
    parser.add_argument('--gmsh-path', type=Path, help='Existing folder with gmsh.py and native library')
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    report_path = output.with_suffix('.verification.json')
    if output.suffix.lower() not in ('.step', '.stp'):
        parser.error('Output extension must be .step or .stp')
    if output.exists() or report_path.exists():
        parser.error('Output or report exists; choose another filename')
    if not output.parent.is_dir():
        parser.error('Output directory must already exist')
    triangles, report = read_mesh(source)
    if args.expected_size is not None and not np.allclose(
            report['size_mm'], args.expected_size, rtol=0, atol=.001):
        raise ValueError(f"Unexpected axis-aligned dimensions: {report['size_mm']}")
    if args.gmsh_path:
        sys.path.insert(0, str(args.gmsh_path.resolve()))
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setString('Geometry.OCCTargetUnit', 'MM')
        def measure():
            solids = gmsh.model.getEntities(3)
            if len(solids) != 1:
                raise ValueError(f'Expected 1 solid; got {len(solids)}')
            tag = solids[0][1]
            box = np.array(gmsh.model.occ.getBoundingBox(3, tag)).reshape(2, 3)
            volume = gmsh.model.occ.getMass(3, tag)
            if not np.allclose(box, report['bounds_mm'], rtol=0, atol=.001):
                raise ValueError('STEP bounds differ from STL')
            if abs(volume-report['mesh_volume_mm3'])/report['mesh_volume_mm3'] > 1e-6:
                raise ValueError('STEP volume differs from STL')
            return dict(solid_bodies=1, bounds_mm=box.tolist(),
                        size_mm=(box[1]-box[0]).tolist(), volume_mm3=volume,
                        faces=len(gmsh.model.getEntities(2)))
        with tempfile.TemporaryDirectory(prefix='step_check_', dir=output.parent) as temp:
            step = Path(temp)/'mesh.step'
            write_brep(triangles, step)
            gmsh.model.occ.importShapes(str(step), highestDimOnly=True)
            gmsh.model.occ.synchronize()
            report['initial_step_read'] = measure()
            gmsh.write(str(step))
            gmsh.clear()
            gmsh.model.occ.importShapes(str(step), highestDimOnly=True)
            gmsh.model.occ.synchronize()
            report['final_step_read'] = measure()
            data = step.read_bytes()
            if b'AUTOMOTIVE_DESIGN' not in data[:5000]:
                raise ValueError('Exported STEP is not AP214')
            if hashlib.sha256(source.read_bytes()).hexdigest() != report['source_sha256']:
                raise ValueError('Source changed during conversion')
            report.update(step_file=output.name, step_sha256=hashlib.sha256(data).hexdigest(),
                          step_format='STEP AP214 / AUTOMOTIVE_DESIGN',
                          validation_kernel='OpenCASCADE via Gmsh '+gmsh.__version__,
                          roundtrip_passed=True, geometry_type='Faceted solid BREP from source STL',
                          SW2016_native_open_tested=False, native_SLDPRT_2016_created=False,
                          self_intersection_tested=False,
                          checked_at=datetime.now().isoformat(timespec='seconds'))
            # Publish only after checks; exclusive creation prevents silent replacement.
            with output.open('xb') as stream:
                stream.write(data)
            with report_path.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
    finally:
        gmsh.finalize()
    print(json.dumps(dict(step=str(output), report=str(report_path),
                         size_mm=report['size_mm'], roundtrip_passed=True), ensure_ascii=False))


if __name__ == '__main__':
    main()
