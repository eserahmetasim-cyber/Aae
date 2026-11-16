# AAE adventure motoru + sürücüyü üçgen listesine aktarır (Aae deposundaki uc_boyut.py yazılımsal 3B motoru için).
# blender -b -P adv_ucgen_disa.py -- <cikti.npz> [hedef_ucgen_sayisi]
# Eksen dönüşümü: Blender (X sağ, Y ileri, Z yukarı) -> uc_boyut (X sağ, Y yukarı, Z ileri): (x, z, y).
# Gruplar: govde, surucu, teker_arka, teker_on. Tekerler kendi aks merkezine göre (aks konumu ayrı kaydedilir).
import bpy, sys, os, math, bmesh
import numpy as np
from mathutils import Vector
ARG = sys.argv[sys.argv.index("--") + 1:]
CIKTI = ARG[0]
HEDEF = int(ARG[1]) if len(ARG) > 1 else 9000
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
exec(open(r"D:\IcerikFabrikasi\library\_work\blender3b\adv_kur.py", encoding="utf-8").read())
bpy.context.view_layer.update()


def lin2srgb(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def renk_oku(m):
    if m is None or not m.use_nodes:
        return (150, 150, 150), False, 1.0
    b = m.node_tree.nodes.get("Principled BSDF")
    if b is None:
        return (150, 150, 150), False, 1.0
    c = b.inputs["Base Color"].default_value
    alfa = b.inputs["Alpha"].default_value
    e = b.inputs["Emission Strength"].default_value
    if e > 2.0:                                       # lamba / LED: ışıksız ve yayılım rengiyle
        ec = b.inputs["Emission Color"].default_value
        return tuple(int(255 * lin2srgb(ec[i])) for i in range(3)), True, alfa
    return tuple(int(255 * lin2srgb(c[i])) for i in range(3)), False, alfa


meshler = [o for o in bpy.data.objects if o.type in ("MESH", "CURVE") and not o.hide_render]
toplam = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in meshler:
    try:
        me = o.evaluated_get(dg).to_mesh()
        toplam += sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
    except RuntimeError:
        pass
oran = min(1.0, HEDEF / max(1, toplam))
print("TOPLAM_UCGEN", toplam, "ORAN", round(oran, 3))
egriler = [o for o in meshler if o.type == "CURVE"]
if egriler:
    bpy.ops.object.select_all(action="DESELECT")
    for o in egriler: o.select_set(True)
    bpy.context.view_layer.objects.active = egriler[0]
    bpy.ops.object.convert(target="MESH")
meshler = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]
for o in meshler:
    if oran < 1.0:
        d = o.modifiers.new("dec", "DECIMATE")
        d.ratio = 0.2 if o.name.startswith("teker_") else max(0.05, oran)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

ON_TAKIM = ("catal_", "aks_ayak", "kaliper_on", "alt_kelepce", "ust_kelepce", "on_camurluk", "gidon",
            "el_koruma", "ayna")
aks = {"teker_arka": Vector(ADV_ARKA_AKS), "teker_on": Vector(ADV_ON_AKS)}


def grup(o):
    p = o
    while p is not None:
        if p.name.startswith("teker_arka"): return "teker_arka"
        if p.name.startswith("teker_on"): return "teker_on"
        if p == ADV_SURUCU or p.name.startswith("surucu"): return "surucu"
        if p.name.startswith(ON_TAKIM): return "on_takim"
        p = p.parent
    return "govde"


veri = {g: {"t": [], "r": [], "i": []} for g in ("govde", "surucu", "on_takim", "teker_arka", "teker_on")}
for o in meshler:
    ev = o.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        continue
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    mw = o.matrix_world
    g = grup(o)
    mats = [s.material for s in o.material_slots]
    renkler = [renk_oku(m) for m in mats] or [((150, 150, 150), False, 1.0)]
    for p in me.polygons:
        rk, isiksiz, alfa = renkler[min(p.material_index, len(renkler) - 1)]
        if alfa < 0.35:
            rk = tuple(int(0.55 * x + 0.45 * 150) for x in rk)   # şeffaf ön cam: açık gri-mavi tek ton
        ns = [mw @ me.vertices[v].co for v in p.vertices]
        if g in aks:
            ns = [n - aks[g] for n in ns]
        veri[g]["t"].append([[n.x, n.z, n.y] for n in ns])
        veri[g]["r"].append(rk)
        veri[g]["i"].append(isiksiz)
    ev.to_mesh_clear()

kayit = {}
for g, v in veri.items():
    kayit[g + "_ucgen"] = np.asarray(v["t"], np.float32).reshape(-1, 3, 3)
    kayit[g + "_renk"] = np.asarray(v["r"], np.uint8).reshape(-1, 3)
    kayit[g + "_isiksiz"] = np.asarray(v["i"], bool)
    print("GRUP", g, len(v["t"]))
for g, a in aks.items():
    kayit[g + "_aks"] = np.asarray([a.x, a.z, a.y], np.float32)
os.makedirs(os.path.dirname(CIKTI), exist_ok=True)
np.savez_compressed(CIKTI, **kayit)
print("BITTI", CIKTI)
