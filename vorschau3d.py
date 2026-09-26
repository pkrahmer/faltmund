"""
vorschau3d – farbige 3D-Vorschau eines Faltmund-Motivs in beiden Öffnungen.

Das ist ein Anschauungsmodell, kein physikalisch exaktes Faltmodell: Der echte
Faltmund hat Finger in den Taschen und verformt sich weich. Hier werden die
Zonen als starre Dreiecke so im Raum angeordnet, wie man sie beim Aufziehen
sieht, und mit der ausgemalten Vorlage (faltmund.textur) texturiert:

  * Rachen C hinten in der Mitte, dort laufen die vier sichtbaren Klappen zusammen
  * Mundwinkel K1/K2 auf der Scharnierachse (normal: links/rechts, seitlich: oben/unten)
  * Kieferspitzen T1/T2 vorne (normal: oben/unten, seitlich: links/rechts)
  * jede Klappe = (Mundwinkel, Kieferspitze, Rachen)
  * je Tasche zwei Hälften: die an der Lippe der Klappe (H, K, T) und die
    andere (H, R, T) mit dem Firstpunkt R hinter der Spitze; H = Hinterkopf

Aufruf:  vorschau(motiv, "normal") -> PIL.Image ;  vorschau_beide(motiv) -> beide nebeneinander
"""
import math
from PIL import Image, ImageDraw, ImageEnhance

from faltmund import Layout, textur

# ------------------------------------------------------------- Vektoren 3D
def v_add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def v_sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def v_scale(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def v_dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def v_cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def v_norm(a):
    l = math.sqrt(v_dot(a, a)) or 1.0
    return v_scale(a, 1 / l)


def sgn(x): return -1 if x < 0.5 else 1      # Seite eines Papierpunkts relativ zur Blattmitte


# ------------------------------------------------------------- Modell
def modell(oeffnung):
    """Liste von Flächen: (uv-Dreieck | None, xyz-Dreieck, art).
    art: 'innen' (Mundhöhle), 'aussen' (Tasche), 'haut' (Füllfläche ohne Textur).

    Je Kiefer ein Rahmen: a = Richtung zur Kieferspitze, b = seitlich. Punkte:
      T = Kieferspitze vorne, H = Hinterkopf-First hinten, K = Mundwinkel (auf b),
      R = seitlicher Firstpunkt. Der Kiefer ist ein Dach mit First H–T: die beiden
      Taschenhälften an den Lippen laufen zu den Mundwinkeln, die anderen beiden zu R."""
    lay = Layout()
    C = (0.0, 0.0, -1.0)                                   # Rachen
    normal = oeffnung == "normal"

    def A(p):        # Kieferachse (Einheitsvektor) für einen Papierpunkt der Spitze
        return (0.0, -sgn(p[1]), 0.0) if normal else (sgn(p[0]), 0.0, 0.0)

    def B(p):        # seitliche Achse für einen Papierpunkt (Mundwinkel-Seite)
        return (sgn(p[0]), 0.0, 0.0) if normal else (0.0, -sgn(p[1]), 0.0)

    def T(a): return v_add(v_scale(a, 0.7), (0, 0, 0.6))
    def Hf(a): return v_add(v_scale(a, 0.9), (0, 0, -1.4))
    def K(b): return b
    def R(a, b): return v_add(v_add(v_scale(a, 0.55), v_scale(b, 0.75)), (0, 0, -0.5))

    faces = []
    for fl in lay.flaps:
        if fl.oeffnung != oeffnung:
            continue
        a, b = A(fl.spitze), B(fl.spitze)
        t, h, k, r = T(a), Hf(a), K(b), R(a, b)
        faces.append(([fl.winkel, fl.spitze, fl.rachen], [k, t, C], "innen"))
        pk = next(p for p in lay.pockets if p.spitze == fl.spitze)
        for name, hf in pk.halves.items():
            if hf.mitte == fl.winkel:                         # Hälfte an der Lippe dieser Klappe
                faces.append(([hf.ecke, hf.mitte, hf.spitze], [h, k, t], "aussen"))
            else:                                             # die andere Hälfte, zum seitlichen First
                faces.append(([hf.ecke, hf.mitte, hf.spitze], [h, r, t], "aussen"))
        faces.append((None, [h, r, k], "haut"))               # Seite zwischen First- und Lippenhälfte
    # Rückseite je Kiefer und zwischen den Kiefern (nur von hinten sichtbar)
    for sa in (-1, 1):
        a = (0.0, sa, 0.0) if normal else (sa, 0.0, 0.0)
        h = Hf(a)
        r1, r2 = (R(a, (-1, 0, 0)), R(a, (1, 0, 0))) if normal else (R(a, (0, -1, 0)), R(a, (0, 1, 0)))
        faces.append((None, [h, r1, r2], "haut"))
    hN, hS = (Hf((0, 1, 0)), Hf((0, -1, 0))) if normal else (Hf((1, 0, 0)), Hf((-1, 0, 0)))
    for k in ([(-1, 0, 0), (1, 0, 0)] if normal else [(0, -1, 0), (0, 1, 0)]):
        faces.append((None, [hN, hS, k], "haut"))
    return faces


# ------------------------------------------------------------- Kamera
def drehen(p, yaw, pitch):
    x, y, z = p
    a = math.radians(yaw); x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    b = math.radians(pitch); y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
    return (x, y, z)


def kamera(p, yaw=-28.0, pitch=18.0, dist=4.2, f=2.2, size=800):
    """Modellpunkt -> (Bildpunkt, Tiefe). Dreht die Szene, dann Perspektive."""
    x, y, z = drehen(p, yaw, pitch)
    d = dist - z
    s = size * 0.5
    return (s + x * f / d * s, s - y * f / d * s), d


def sichtbar(xyz, art, yaw, pitch, dist=4.2):
    """Backface-Culling: Außenflächen zeigen vom Kopfinneren weg, Innenflächen zur Mundhöhle."""
    n = v_norm(v_cross(v_sub(xyz[1], xyz[0]), v_sub(xyz[2], xyz[0])))
    c = v_scale(v_add(v_add(xyz[0], xyz[1]), xyz[2]), 1 / 3)
    bezug = (0.0, 0.0, 0.45) if art == "innen" else (0.0, 0.0, -0.75)
    if v_dot(n, v_sub(bezug, c)) < 0 and art == "innen": n = v_scale(n, -1)
    if v_dot(n, v_sub(c, bezug)) < 0 and art != "innen": n = v_scale(n, -1)
    cr, nr = drehen(c, yaw, pitch), drehen(n, yaw, pitch)
    return v_dot(nr, v_sub((0.0, 0.0, dist), cr)) > 0


def licht_faktor(tri, yaw=-28.0, pitch=18.0):
    """einfache Lambert-Schattierung mit Licht von vorne oben links"""
    n = v_norm(v_cross(v_sub(tri[1], tri[0]), v_sub(tri[2], tri[0])))
    light = v_norm((-0.45, 0.8, 0.9))
    return 0.62 + 0.38 * abs(v_dot(n, light))


# ------------------------------------------------------------- Rendern (Z-Buffer)
def vorschau(motiv, oeffnung="normal", size=800, tex=None, yaw=-16.0, pitch=26.0):
    """Rastert alle Flächen mit Tiefenpuffer: pro Pixel gewinnt die nächste Fläche.
    Texturkoordinaten werden baryzentrisch interpoliert (affin – für die kleinen Dreiecke ausreichend)."""
    import numpy as np
    tex = tex or textur(motiv)
    T = np.asarray(tex, dtype=np.float32)
    TW = T.shape[0]
    farben = getattr(motiv, "farben", {})
    fuell = {"haut": farben.get("haut", "#88aabb"), "mund": farben.get("mund", "#c9302c")}
    img = np.full((size, size, 3), 255, dtype=np.float32)
    zbuf = np.full((size, size), np.inf, dtype=np.float32)
    ys, xs = np.mgrid[0:size, 0:size]
    px, py = xs + 0.5, ys + 0.5
    for uv, xyz, art in modell(oeffnung):
        scr = [kamera(p, yaw, pitch, size=size) for p in xyz]
        (x0, y0), d0 = scr[0]; (x1, y1), d1 = scr[1]; (x2, y2), d2 = scr[2]
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(det) < 1e-9:
            continue
        # Bounding-Box
        xa, xb = max(int(min(x0, x1, x2)), 0), min(int(max(x0, x1, x2)) + 1, size)
        ya, yb = max(int(min(y0, y1, y2)), 0), min(int(max(y0, y1, y2)) + 1, size)
        if xa >= xb or ya >= yb:
            continue
        X, Y = px[ya:yb, xa:xb], py[ya:yb, xa:xb]
        l0 = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / det
        l1 = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / det
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
        depth = l0 * d0 + l1 * d1 + l2 * d2
        zb = zbuf[ya:yb, xa:xb]
        win = inside & (depth < zb)
        if not win.any():
            continue
        if uv is None:
            col = fuell[art].lstrip("#")
            rgb = np.array([int(col[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
            color = np.broadcast_to(rgb, (yb - ya, xb - xa, 3))
        else:
            u = (l0 * uv[0][0] + l1 * uv[1][0] + l2 * uv[2][0]) * (TW - 1)
            v = (l0 * uv[0][1] + l1 * uv[1][1] + l2 * uv[2][1]) * (TW - 1)
            ui = np.clip(np.rint(u), 0, TW - 1).astype(int)
            vi = np.clip(np.rint(v), 0, TW - 1).astype(int)
            color = T[vi, ui]
        color = np.clip(color * licht_faktor(xyz, yaw, pitch), 0, 255)
        sub = img[ya:yb, xa:xb]
        sub[win] = color[win]
        zb[win] = depth[win]
    return Image.fromarray(img.astype(np.uint8))


def vorschau_beide(motiv, size=800):
    tex = textur(motiv)
    a = vorschau(motiv, "normal", size, tex)
    b = vorschau(motiv, "seitlich", size, tex)
    out = Image.new("RGB", (2 * size + 40, size + 60), (255, 255, 255))
    out.paste(a, (0, 40)); out.paste(b, (size + 40, 40))
    d = ImageDraw.Draw(out)
    d.text((size // 2 - 60, 12), "Mund normal auf", fill=(60, 60, 60))
    d.text((size + 40 + size // 2 - 60, 12), "Mund seitlich auf", fill=(60, 60, 60))
    return out
