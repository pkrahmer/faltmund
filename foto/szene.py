"""
szene – fotorealistischer Faltmund auf dem Kinderschreibtisch (Blender/Cycles als Python-Modul).

    python3 szene.py test 60        # ein Probebild von Bild 60 → probe_060.png
    python3 szene.py alle           # alle Bilder nach frames/ (setzt fort, wo es aufgehört hat)

Papier: feines Dreiecksnetz, das exakt entlang der Falzlinien trianguliert ist; jeder Netzpunkt
folgt starr seinem Dreieck aus faltung.py, an den Falzen wird über ~1,5 mm gerundet. Dicke 0,12 mm,
bedruckte Seite mit Buntstifttextur und Papierbump, Rückseite blankes Papier, etwas Durchscheinen.
"""
import sys, os, math, time
import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER); sys.path.insert(0, os.path.join(HIER, ".."))
import bpy
from mathutils import Vector, Matrix, Euler
from faltung import DREIECKE, TRI_IDX, PUNKTE, BLATT

FRAMES = np.load(os.path.join(HIER, "ablauf.npy"))           # (n, 20, 3) in Metern
N_FEIN = 128                                                  # Netzauflösung je Blattkante (~1,5 mm)
AUFL = 1080


# ---------------------------------------------------------------- feines Papiernetz
def _coarse_tri_of(u, v):
    """Index des äußeren Grobdreiecks, das (u, v) enthält, und baryzentrische Koordinaten"""
    for k, t in enumerate(DREIECKE):
        (x0, y0), (x1, y1), (x2, y2) = t
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        l0 = ((y1 - y2) * (u - x2) + (x2 - x1) * (v - y2)) / det
        l1 = ((y2 - y0) * (u - x2) + (x0 - x2) * (v - y2)) / det
        l2 = 1 - l0 - l1
        if min(l0, l1, l2) > -1e-9:
            return k, (l0, l1, l2)
    return None, None


def feines_netz():
    n = N_FEIN
    verts, bary, tri_of, uv = [], [], [], []
    vid = {}
    for j in range(n + 1):
        for i in range(n + 1):
            u, v = i / n, j / n
            k, b = _coarse_tri_of(u, v)
            if k is None:
                continue
            vid[(i, j)] = len(verts)
            verts.append((u, v)); bary.append(b); tri_of.append(k); uv.append((u, 1 - v))
    faces = []
    for j in range(n):
        for i in range(n):
            I, J = int(4 * i / n), int(4 * j / n)                        # Grobzelle
            haupt = (I == J) or abs(I - J) == 2                           # gleiche Teilung wie netz()
            a, b_, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
            tris = [(a, b_, c), (a, c, d)] if haupt else [(a, b_, d), (b_, c, d)]
            for t in tris:
                if all(p in vid for p in t):
                    cu = sum(p[0] for p in t) / 3 / n; cv = sum(p[1] for p in t) / 3 / n
                    k, _ = _coarse_tri_of(cu, cv)
                    if k is not None:
                        faces.append(tuple(vid[p] for p in reversed(t)))   # Normale nach außen = bemalte Seite
    return np.array(verts), np.array(bary), np.array(tri_of), np.array(uv), faces


FEIN_UV, FEIN_BARY, FEIN_TRI, FEIN_TEX, FEIN_FACES = feines_netz()


def _falz_abstand(u, v):
    """Abstand eines Papierpunkts zur nächsten Falzlinie (Papiereinheiten)"""
    d = np.minimum.reduce([np.abs(u - q) for q in (0.25, 0.5, 0.75)] + [np.abs(v - q) for q in (0.25, 0.5, 0.75)])
    d = np.minimum(d, np.abs(u - v) / math.sqrt(2)); d = np.minimum(d, np.abs(u + v - 1) / math.sqrt(2))
    for c in (0.5, 1.5):
        d = np.minimum(d, np.abs(u + v - c) / math.sqrt(2))
    for c in (-0.5, 0.5):
        d = np.minimum(d, np.abs(u - v - c) / math.sqrt(2))
    return d


FALZ_D = _falz_abstand(FEIN_UV[:, 0], FEIN_UV[:, 1])
# Nachbarschaft für die Rundung an den Falzen
_NB = [[] for _ in range(len(FEIN_UV))]
for f in FEIN_FACES:
    for a in f:
        for b in f:
            if a != b: _NB[a].append(b)
NB = [np.array(sorted(set(x))) for x in _NB]
RUND = np.where(FALZ_D < 0.008)[0]                                    # ~1,5 mm beidseits


def fein_lage(X):
    """Positionen aller Netzpunkte für eine Groblage X (20×3)"""
    T = X[TRI_IDX[FEIN_TRI]]                                          # (m, 3, 3)
    P = np.einsum("mk,mkc->mc", FEIN_BARY, T)
    # Rundung: an den Falzen ein paar Glättungsschritte (Papier knickt nicht messerscharf)
    for _ in range(4):
        Q = P.copy()
        for i in RUND:
            Q[i] = 0.5 * P[i] + 0.5 * P[NB[i]].mean(axis=0)
        P = Q
    return P


# ---------------------------------------------------------------- Szene
def mat_papier(name, farbbild, hoehenbild):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; ns = nt.nodes; ls = nt.links
    bsdf = ns["Principled BSDF"]
    tex = ns.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(farbbild); tex.interpolation = "Cubic"
    hi = ns.new("ShaderNodeTexImage"); hi.image = bpy.data.images.load(hoehenbild); hi.image.colorspace_settings.name = "Non-Color"
    bump = ns.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.00015
    ls.new(hi.outputs["Color"], bump.inputs["Height"]); ls.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    ls.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.78
    bsdf.inputs["Sheen Weight"].default_value = 0.08; bsdf.inputs["Sheen Roughness"].default_value = 0.6
    bsdf.inputs["Subsurface Weight"].default_value = 0.06
    bsdf.inputs["Subsurface Radius"].default_value = (0.0006, 0.0005, 0.0004)
    bsdf.inputs["Transmission Weight"].default_value = 0.0
    return m


def mat_rueckseite():
    m = bpy.data.materials.new("Papier hinten"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.90, 0.88, 0.83, 1)
    b.inputs["Roughness"].default_value = 0.82
    b.inputs["Subsurface Weight"].default_value = 0.08
    b.inputs["Subsurface Radius"].default_value = (0.0006, 0.0005, 0.0004)
    return m


def mat_einfach(name, farbe, rau=0.5, metall=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*farbe, 1); b.inputs["Roughness"].default_value = rau
    b.inputs["Metallic"].default_value = metall; b.inputs["Coat Weight"].default_value = coat
    return m


def mat_holz(name, hell=(0.62, 0.45, 0.28), dunkel=(0.45, 0.30, 0.17), skala=6.0, rau=0.45):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; ns = nt.nodes; ls = nt.links
    b = ns["Principled BSDF"]
    co = ns.new("ShaderNodeTexCoord")
    mp = ns.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (skala, skala * 0.12, skala)
    ls.new(co.outputs["Object"], mp.inputs["Vector"])
    nz = ns.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
    ls.new(mp.outputs["Vector"], nz.inputs["Vector"])
    wv = ns.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.inputs["Scale"].default_value = 2.2
    wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 4
    ls.new(mp.outputs["Vector"], wv.inputs["Vector"])
    mx = ns.new("ShaderNodeMix"); mx.data_type = "FLOAT"; mx.inputs["Factor"].default_value = 0.35
    ls.new(wv.outputs["Fac"], mx.inputs["A"]); ls.new(nz.outputs["Fac"], mx.inputs["B"])
    ramp = ns.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dunkel, 1); ramp.color_ramp.elements[1].color = (*hell, 1)
    ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[1].position = 0.75
    ls.new(mx.outputs["Result"], ramp.inputs["Fac"]); ls.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rau; b.inputs["Coat Weight"].default_value = 0.15
    bump = ns.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.05
    ls.new(mx.outputs["Result"], bump.inputs["Height"]); ls.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def objekt(name, mesh, mat=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    if mat: o.data.materials.append(mat)
    return o


def buntstift(name, farbe, laenge, loc, rot_z, seed):
    """sechseckiger Buntstift: lackierter Schaft, Holzkegel, farbige Mine"""
    rng = np.random.default_rng(seed)
    r = 0.0036
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=r, depth=laenge, location=(0, 0, 0))
    schaft = bpy.context.object; schaft.name = name
    bpy.ops.object.modifier_add(type="BEVEL"); schaft.modifiers[-1].width = 0.0006; schaft.modifiers[-1].segments = 2
    schaft.data.materials.append(mat_einfach(name + " Lack", farbe, rau=0.28, coat=0.6))
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=r * 0.92, radius2=0.0009, depth=0.017, location=(0, 0, laenge / 2 + 0.0085))
    kegel = bpy.context.object
    kegel.data.materials.append(mat_holz(name + " Holz", hell=(0.85, 0.66, 0.45), dunkel=(0.72, 0.52, 0.33), skala=80, rau=0.7))
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.00095, radius2=0.0002, depth=0.0035, location=(0, 0, laenge / 2 + 0.0170 + 0.0012))
    mine = bpy.context.object; mine.data.materials.append(mat_einfach(name + " Mine", farbe, rau=0.6))
    for o in (kegel, mine):
        o.parent = schaft
    schaft.rotation_euler = (math.pi / 2, 0, rot_z)
    schaft.location = (loc[0], loc[1], r * 0.866)
    return schaft


def baue_szene(farbbild, hoehenbild):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.cycles.samples = 40; sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.render.resolution_x = sc.render.resolution_y = AUFL; sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -1.5
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_depth = "16"

    # Welt: gedämpftes Tageslicht
    w = bpy.data.worlds.new("Welt"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.55, 0.62, 0.72, 1); bg.inputs["Strength"].default_value = 0.12

    # Schreibtisch: helles Birkenholz
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.15, 0)); tisch = bpy.context.object; tisch.name = "Tisch"
    tisch.scale = (1.4, 0.9, 1)
    tisch.data.materials.append(mat_holz("Birke", hell=(0.80, 0.63, 0.44), dunkel=(0.66, 0.48, 0.30), skala=5.0, rau=0.42))
    # Tischkante / Wand dahinter
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.60, 0.4), rotation=(math.pi / 2, 0, 0)); wand = bpy.context.object
    wand.scale = (1.6, 0.8, 1); wand.data.materials.append(mat_einfach("Wand", (0.83, 0.80, 0.72), rau=0.9))
    # Kinderbilder an der Wand (weit unscharf)
    rng = np.random.default_rng(3)
    for k, (x, z, f) in enumerate([(-0.28, 0.33, (0.95, 0.75, 0.30)), (-0.05, 0.40, (0.45, 0.70, 0.90)),
                                   (0.2, 0.31, (0.92, 0.45, 0.40)), (0.36, 0.44, (0.55, 0.80, 0.45))]):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, 0.595, z), rotation=(math.pi / 2, rng.normal(0, 0.05), 0))
        b = bpy.context.object; b.scale = (0.15, 0.21, 1)
        b.data.materials.append(mat_einfach(f"Bild{k}", (0.95, 0.94, 0.9), rau=0.85))
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x + rng.normal(0, 0.01), 0.592, z + rng.normal(0, 0.01)), rotation=(math.pi / 2, 0, rng.normal(0, 0.3)))
        c = bpy.context.object; c.scale = (0.08, 0.1, 1); c.data.materials.append(mat_einfach(f"Motiv{k}", f, rau=0.8))

    # Buntstifte verstreut
    farben = [(0.80, 0.08, 0.06), (0.95, 0.60, 0.05), (0.10, 0.45, 0.12), (0.08, 0.25, 0.70), (0.55, 0.20, 0.55), (0.95, 0.85, 0.15), (0.45, 0.25, 0.10)]
    lagen = [(-0.11, -0.10, 0.55), (0.12, 0.09, -0.35), (-0.07, 0.15, 1.35), (0.16, -0.02, 1.9), (-0.17, 0.07, -0.25), (0.05, 0.25, 0.2), (-0.20, 0.22, 1.1)]
    for k, (f, (x, y, rz)) in enumerate(zip(farben, lagen)):
        buntstift(f"Stift{k}", f, 0.12 + 0.05 * rng.random(), (x, y), rz, k)
    # Spitzer und Radiergummi
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.09, 0.04, 0.007)); sp = bpy.context.object
    sp.scale = (0.025, 0.014, 0.014); sp.rotation_euler = (0, 0, 0.5)
    bpy.ops.object.modifier_add(type="BEVEL"); sp.modifiers[-1].width = 0.002; sp.modifiers[-1].segments = 3
    sp.data.materials.append(mat_einfach("Spitzer", (0.75, 0.76, 0.78), rau=0.25, metall=1.0))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.11, 0.03, 0.006)); rg = bpy.context.object
    rg.scale = (0.04, 0.018, 0.012); rg.rotation_euler = (0, 0, -0.3)
    bpy.ops.object.modifier_add(type="BEVEL"); rg.modifiers[-1].width = 0.003; rg.modifiers[-1].segments = 4
    rg.data.materials.append(mat_einfach("Radierer", (0.93, 0.92, 0.88), rau=0.7))
    # Spitzerspäne: gewellte Ringe
    for k in range(4):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.006 + 0.002 * k, minor_radius=0.0006, location=(0.075 + 0.011 * k, 0.012 + 0.008 * (k % 2), 0.0008))
        t = bpy.context.object; t.scale = (1, 1, 0.25); t.rotation_euler = (0.1, 0.2, k)
        t.data.materials.append(mat_holz(f"Span{k}", hell=(0.88, 0.70, 0.50), dunkel=(0.75, 0.55, 0.36), skala=90, rau=0.7))
    # Ausgedruckte Vorlage hinten links
    vorlage = os.path.join(HIER, "..", "faltfrosch.png")
    if os.path.exists(vorlage):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.06, 0.24, 0.0004), rotation=(0, 0, 0.3)); bl = bpy.context.object
        bl.scale = (0.21, 0.297, 1)
        m = bpy.data.materials.new("Vorlage"); m.use_nodes = True
        tx = m.node_tree.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(vorlage)
        m.node_tree.links.new(tx.outputs["Color"], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
        m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
        bl.data.materials.append(m)

    # Papier-Faltmund
    me = bpy.data.meshes.new("Faltmund")
    me.from_pydata([(0, 0, 0)] * len(FEIN_UV), [], FEIN_FACES)
    uvl = me.uv_layers.new(name="UV")
    for poly in me.polygons:
        for li, vi in zip(poly.loop_indices, poly.vertices):
            uvl.data[li].uv = FEIN_TEX[vi]
    fm = objekt("Faltmund", me)
    me.materials.append(mat_papier("Papier", farbbild, hoehenbild)); me.materials.append(mat_rueckseite())
    for p in me.polygons: p.use_smooth = True
    so = fm.modifiers.new("Dicke", "SOLIDIFY"); so.thickness = 0.00012; so.offset = -1; so.material_offset = 1
    so.use_even_offset = True

    # Licht: Schreibtischlampe (warm, gerichtet) von links oben, Fenster (kühl, groß) von rechts hinten
    bpy.ops.object.light_add(type="AREA", location=(-0.22, -0.05, 0.38)); lampe = bpy.context.object
    lampe.data.shape = "DISK"; lampe.data.size = 0.09; lampe.data.energy = 7; lampe.data.color = (1.0, 0.80, 0.58)
    lampe.data.spread = math.radians(70)
    lampe.rotation_euler = Euler((0, 0, 0)); lampe.rotation_euler = (Vector((0.02, 0.05, 0.03)) - lampe.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(0.55, 0.45, 0.45)); fenster = bpy.context.object
    fenster.data.size = 0.9; fenster.data.energy = 22; fenster.data.color = (0.80, 0.88, 1.0)
    fenster.rotation_euler = (Vector((0, 0.05, 0.05)) - fenster.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(0.05, -0.45, 0.25)); aufheller = bpy.context.object
    aufheller.data.size = 0.5; aufheller.data.energy = 1.5; aufheller.data.color = (1.0, 0.95, 0.9)
    aufheller.rotation_euler = (Vector((0, 0.05, 0.04)) - aufheller.location).to_track_quat("-Z", "Y").to_euler()

    # Kamera
    cd = bpy.data.cameras.new("Kamera"); cam = bpy.data.objects.new("Kamera", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.lens = 70; cd.sensor_width = 36; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.4; cd.dof.aperture_blades = 7
    cd.clip_start = 0.01
    return fm, cam


# ---------------------------------------------------------------- Pose pro Bild
# Faltmund: Spitzen zur Kamera, leicht angehoben; er liegt auf dem Tisch auf
KIPP = Matrix.Rotation(math.radians(72), 4, "X")          # Achse z (Spitzen) → zur Kamera (-y), etwas nach oben
DREH = Matrix.Rotation(math.radians(8), 4, "Z")


def pose(fm, i):
    X = FRAMES[i]
    P = fein_lage(X)
    M = DREH @ KIPP
    Pw = np.array([(M @ Vector(p)).to_tuple() for p in P])
    Pw[:, 2] -= Pw[:, 2].min() - 0.0002                    # auf dem Tisch aufliegen
    Pw[:, 1] -= 0.0                                           # Mitte des Tisches
    me = fm.data
    me.vertices.foreach_set("co", Pw.astype(np.float32).ravel())
    me.update()
    return Pw


def kamera(cam, i, n, Pw):
    t = i / max(1, n - 1)
    # langsame Kreisfahrt (~22°) mit leichtem Heranfahren, Blick auf die Mitte des Faltmunds
    ziel = Vector((0.0, 0.0, 0.045))
    w = math.radians(-14 + 22 * (0.5 - 0.5 * math.cos(math.pi * t)))
    r = 0.42 - 0.04 * t
    h = 0.16 + 0.015 * math.sin(math.pi * t)
    cam.location = (ziel.x + r * math.sin(w), ziel.y - r * math.cos(w), h)
    cam.rotation_euler = (ziel - cam.location).to_track_quat("-Z", "Y").to_euler()
    # Fokus auf die Spitzen (vorderster Punkt)
    vorne = Pw[np.argmin(Pw[:, 1])]
    cam.data.dof.focus_distance = (Vector(vorne) - cam.location).length * 0.97 + 0.02


def render(i, pfad, samples=None):
    sc = bpy.context.scene
    if samples: sc.cycles.samples = samples
    fm = bpy.data.objects["Faltmund"]; cam = bpy.data.objects["Kamera"]
    Pw = pose(fm, i); kamera(cam, i, len(FRAMES), Pw)
    sc.render.filepath = pfad
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    farbe = os.path.join(HIER, "frosch_buntstift.png"); hoehe = os.path.join(HIER, "frosch_hoehe.png")
    baue_szene(farbe, hoehe)
    if sys.argv[1] == "test":
        i = int(sys.argv[2]); s = int(sys.argv[3]) if len(sys.argv) > 3 else None
        t = time.time(); render(i, os.path.join(HIER, f"probe_{i:03d}.png"), s); print("Sekunden:", round(time.time() - t))
    else:
        os.makedirs(os.path.join(HIER, "frames"), exist_ok=True)
        budget = float(sys.argv[2]) if len(sys.argv) > 2 else 1e9          # Sekunden; danach sauber aufhören
        start = time.time()
        for i in range(len(FRAMES)):
            if time.time() - start > budget: break
            p = os.path.join(HIER, "frames", f"{i:04d}.png")
            if os.path.exists(p): continue
            t = time.time(); render(i, p); print(i, "fertig in", round(time.time() - t), "s", flush=True)
