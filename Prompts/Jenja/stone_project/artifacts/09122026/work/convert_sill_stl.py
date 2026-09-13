"""Convert the existing triangulated 3DFACE DXF without remeshing.
Usage: python convert_sill_stl.py source.dxf destination.stl report.json
STL coordinates retain the millimetre values from the DXF.
"""
from pathlib import Path
import sys, struct, hashlib, json
from collections import Counter, defaultdict
sys.path.insert(0, str(Path(__file__).parent / 'cadlib'))
import ezdxf
import numpy as np

source, target, report_path = map(Path, sys.argv[1:4])
if target.exists():
    raise FileExistsError(target)
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
doc = ezdxf.readfile(source)
audit = doc.audit()
assert not audit.errors and not audit.fixes
assert doc.units == 4, 'Source must use millimetres'
triangles = []
for face in doc.modelspace():
    assert face.dxftype() == '3DFACE', 'Unexpected entity; conversion stopped'
    assert face.dxf.vtx3.isclose(face.dxf.vtx2), 'Source face is not a triangle'
    triangles.append([tuple(face.dxf.get('vtx'+str(i))) for i in range(3)])
original = np.asarray(triangles, dtype=np.float64)
assert len(original) > 0 and np.isfinite(original).all()
normals = np.cross(original[:,1]-original[:,0],original[:,2]-original[:,0])
normals /= np.linalg.norm(normals,axis=1)[:,None]
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('xb') as f:
    f.write(b'Window sill | coordinates in mm | DXF mesh preserved'.ljust(80,b'\0'))
    f.write(struct.pack('<I', len(original)))
    for normal, triangle in zip(normals, original):
        f.write(struct.pack('<12fH', *normal, *triangle.flatten(), 0))

# Read the binary payload back and validate the geometry actually written.
data = target.read_bytes()
count = struct.unpack_from('<I', data, 80)[0]
assert len(data) == 84+50*count and count == len(original)
loaded, loaded_normals = [], []
for index in range(count):
    record = struct.unpack_from('<12fH', data, 84+50*index)
    assert record[-1] == 0
    loaded_normals.append(record[:3])
    loaded.append(np.array(record[3:12]).reshape(3,3))
mesh = np.array(loaded)
assert np.isfinite(mesh).all()
crosses = np.cross(mesh[:,1]-mesh[:,0],mesh[:,2]-mesh[:,0])
assert np.min(np.linalg.norm(crosses,axis=1)) > 1e-9
unit_normals = crosses/np.linalg.norm(crosses,axis=1)[:,None]
assert np.min(np.sum(unit_normals*np.array(loaded_normals),axis=1)) > 0.99999
edges, directed = Counter(), Counter()
graph = defaultdict(set)
for triangle in mesh:
    ps = [tuple(p) for p in triangle]
    for u,v in zip(ps,ps[1:]+ps[:1]):
        edges[tuple(sorted((u,v)))] += 1
        directed[(u,v)] += 1
        graph[u].add(v); graph[v].add(u)
assert set(edges.values()) == {2}, 'Open or non-manifold edges'
assert all(directed[(v,u)] == n for (u,v),n in directed.items()), 'Inconsistent winding'
unseen=set(graph); components=0
while unseen:
    components += 1
    stack=[unseen.pop()]
    while stack:
        new=graph[stack.pop()] & unseen
        unseen.difference_update(new); stack.extend(new)
assert components == 1
assert len(graph)-len(edges)+count == 2
bounds = [mesh.min(axis=(0,1)).tolist(), mesh.max(axis=(0,1)).tolist()]
size = np.ptp(mesh.reshape(-1,3),axis=0)
assert np.allclose(size,(1600,270,30),rtol=0,atol=0.0001)
max_error = float(np.max(np.linalg.norm(mesh-original,axis=2)))
assert max_error < 0.0001
volume = float(np.einsum('ij,ij->i',mesh[:,0],np.cross(mesh[:,1],mesh[:,2])).sum()/6)
source_volume = float(np.einsum('ij,ij->i',original[:,0],np.cross(original[:,1],original[:,2])).sum()/6)
assert volume > 0 and abs(volume-source_volume)/source_volume < 1e-6
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
report = {
    'source': str(source), 'source_sha256': source_hash,
    'output': target.name, 'output_sha256': hashlib.sha256(data).hexdigest(),
    'format': 'binary STL', 'coordinate_units': 'mm (select mm on import; STL has no standard units field)',
    'triangles': count, 'vertices':len(graph), 'connected_components':components,
    'closed_manifold':True, 'consistent_winding':True, 'normals_verified':True,
    'degenerate_triangles':0, 'bounds_mm':bounds, 'size_mm':size.tolist(),
    'volume_mm3':volume, 'source_volume_mm3':source_volume,
    'max_conversion_vertex_error_mm':max_error,
    'remeshed':False, 'ArtCAM_import_tested':False,
}
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
