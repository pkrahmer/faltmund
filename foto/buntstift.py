"""
buntstift – macht aus der flach ausgemalten Vorlage eine Buntstift-Bemalung auf Papier.

Pipeline (alles in numpy/PIL, 4096² ≙ 19 cm, also ~21,5 px/mm):
  1. flache Farbvorlage aus faltmund.textur (Farbmodus des Motivs)
  2. Farbflächen leicht verwackeln (Buntstift geht mal über die Linie, mal nicht ganz hin)
  3. Strichbild: tausende einzelne Buntstiftstriche in zwei Lagen, je Zone eigene Richtung
  4. Papierzahn: feines Korn, in dessen Tälern kein Pigment landet (weiße Pünktchen)
  5. Konturen als weicher Graphit/Fineliner mit Korn
  6. Falzlinien: an jedem Knick bricht die Farbschicht – feine helle Faserlinie
Außerdem eine Höhenkarte (Papierzahn + Falzrillen) für den Bump im Shader.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from faltmund import textur

PAPIER = np.array([246, 243, 236], dtype=np.float32)       # leicht warmes Zeichenpapier


def _rauschen(n, skala, seed):
    """glattes Wertrauschen, Frequenz ~ 1/skala Pixel, Werte 0..1"""
    rng = np.random.default_rng(seed)
    k = max(2, int(n / skala))
    g = rng.random((k + 1, k + 1)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32) / 255.0


def _striche(n, winkel_feld, seed, dichte=1.0, breite=(9, 16), laenge=(160, 520), alpha=(70, 150)):
    """Strichbild: viele kurze, leicht gebogene Striche, Richtung aus winkel_feld (Grad)"""
    rng = np.random.default_rng(seed)
    im = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(im)
    anzahl = int(dichte * n * n / 2600)
    for _ in range(anzahl):
        x, y = rng.random() * n, rng.random() * n
        w = math.radians(winkel_feld[int(y) % n, int(x) % n] + rng.normal(0, 4))
        L = rng.uniform(*laenge)
        krumm = rng.normal(0, 0.06)
        pts = []
        for t in np.linspace(-0.5, 0.5, 7):
            a = w + krumm * t * 3
            pts.append((x + math.cos(a) * L * t, y + math.sin(a) * L * t))
        d.line(pts, fill=int(rng.uniform(*alpha)), width=int(rng.uniform(*breite)), joint="curve")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32) / 255.0


def falzlinien():
    """alle Falzlinien in Papierkoordinaten"""
    ls = [((q, 0), (q, 1)) for q in (0.25, 0.5, 0.75)] + [((0, q), (1, q)) for q in (0.25, 0.5, 0.75)]
    ls += [((0, 0), (1, 1)), ((1, 0), (0, 1))]
    ls += [((0.5, 0), (1, 0.5)), ((1, 0.5), (0.5, 1)), ((0.5, 1), (0, 0.5)), ((0, 0.5), (0.5, 0))]
    return ls


def bemalen(motiv, n=4096, seed=7):
    """liefert (farbe RGB uint8, hoehe float32 0..1)"""
    flach = np.asarray(textur(motiv, px=n), dtype=np.float32)
    lum = flach @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    kontur = lum < 70                                                   # schwarze Linien

    # 2. Farbflächen verwackeln: Abtastung um bis zu ~0,4 mm versetzen
    dx = (_rauschen(n, 90, seed + 1) - 0.5) * 18
    dy = (_rauschen(n, 90, seed + 2) - 0.5) * 18
    yy, xx = np.mgrid[0:n, 0:n]
    xs = np.clip(xx + dx, 0, n - 1).astype(np.int32); ys = np.clip(yy + dy, 0, n - 1).astype(np.int32)
    farbe = flach[ys, xs]
    kontur_v = kontur[ys // 1, xs // 1]
    weiss = (farbe.min(axis=2) > 235)                                   # nicht ausgemalt (Zähne, Augäpfel)

    # 3. Strichbild: zwei Lagen, Grundrichtung je Viertel verschieden, sanft variierend
    grund = 38 + (_rauschen(n, 700, seed + 3) - 0.5) * 50
    lage1 = _striche(n, grund, seed + 4)
    lage2 = _striche(n, grund - 75, seed + 5, dichte=0.55, alpha=(45, 110))
    druck = 0.78 + 0.22 * _rauschen(n, 260, seed + 6)                   # Druck der Hand
    deckung = 1 - (1 - lage1) * (1 - lage2)
    deckung = np.clip(deckung * 1.45, 0, 1) * druck

    # 4. Papierzahn: in den Tälern bleibt Papier frei
    zahn = _rauschen(n, 2.2, seed + 7) * 0.45 + _rauschen(n, 5, seed + 8) * 0.55
    frei = np.clip((0.30 - zahn) / 0.10, 0, 1)                            # 1 = Tal
    deckung = deckung * (1 - 0.85 * frei)

    # Pigment: Buntstift ist lasierend – Farbe multipliziert sich aufs Papier, Druck vertieft sie
    pig = np.clip(farbe / PAPIER, 0, 1.2)
    satt = 0.8 + 0.4 * deckung
    out = PAPIER * (1 - deckung[..., None] * (1 - pig ** (1.0 / satt[..., None]) * 1.0))
    out = np.where(weiss[..., None], PAPIER * (0.985 + 0.015 * zahn[..., None]), out)

    # 5. Konturen: dunkler Graphit mit Korn, Kanten weich
    k = np.asarray(Image.fromarray((kontur_v * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float32) / 255
    graphit = np.array([38, 36, 40], dtype=np.float32)
    kk = (k * (0.82 + 0.18 * (1 - frei)))[..., None]
    out = out * (1 - kk) + graphit * kk

    # 6. Falzlinien: helle Faserlinie, wo die Farbschicht bricht; Rille in der Höhenkarte
    falz = Image.new("L", (n, n), 0); d = ImageDraw.Draw(falz)
    for a, b in falzlinien():
        d.line([(a[0] * n, a[1] * n), (b[0] * n, b[1] * n)], fill=255, width=5)
    falz = np.asarray(falz.filter(ImageFilter.GaussianBlur(2.5)), dtype=np.float32) / 255
    bruch = falz * (0.5 + 0.5 * _rauschen(n, 4, seed + 9)) * 0.55
    out = out * (1 - bruch[..., None]) + PAPIER * bruch[..., None]

    # leichte Gesamtvariation (Papier nicht perfekt gleichmäßig)
    out *= (0.97 + 0.03 * _rauschen(n, 400, seed + 10))[..., None]

    hoehe = 0.55 * zahn + 0.15 * deckung - 0.6 * falz
    hoehe = (hoehe - hoehe.min()) / (hoehe.max() - hoehe.min())
    return np.clip(out, 0, 255).astype(np.uint8), hoehe.astype(np.float32)


if __name__ == "__main__":
    from motiv_frosch import Frosch
    farbe, hoehe = bemalen(Frosch())
    here = os.path.dirname(os.path.abspath(__file__))
    Image.fromarray(farbe).save(os.path.join(here, "frosch_buntstift.png"))
    Image.fromarray((hoehe * 65535).astype(np.uint16)).save(os.path.join(here, "frosch_hoehe.png"))
    print("ok")
