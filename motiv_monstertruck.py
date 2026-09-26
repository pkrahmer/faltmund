"""
Motiv: Friedhofs-Monstertruck – eigener Entwurf (keine Marken-Lackierung).

Obere Taschen: Kabine mit Scheinwerfer-Augen, Nieten, Grabsteinen, Fledermäusen
und Flammen. Untere Taschen: Monsterreifen mit Stollenprofil. Seitlich auf:
Chromzähne und Nieten im Kühlergrill. Normal auf: Grabstein als Zunge, Auspuff-
rohre am Gaumen. Unter den Klappen: ein Gespenst und ein Knochen.

Aufruf:  python3 motiv_monstertruck.py   →  monstertruck.svg / .pdf / .png / _3d.png
"""
import math
from faltmund import render, save, add, ANLEITUNG_STANDARD, LINE, THIN
from motiv_frosch import rachen, zahnfleisch


# ---------------------------------------------------------------- Bausteine
def scheinwerfer(pg, c, mirror):
    """runder Scheinwerfer in eckigem Gehäuse"""
    r = 0.046
    pg.polyline([add(c, (-r * 1.15, -r * 1.15)), add(c, (r * 1.15, -r * 1.15)), add(c, (r * 1.15, r * 1.15)), add(c, (-r * 1.15, r * 1.15))],
                f'fill="{pg.farbe("chrom")}" stroke="#000" stroke-width="0.5" stroke-linejoin="round"', close=True)
    pg.circle(c, r, f'fill="{pg.farbe("licht")}" stroke="#000" stroke-width="0.5"')
    pg.circle(c, r * 0.62, 'fill="none" stroke="#000" stroke-width="0.35"')
    pg.circle(c, r * 0.28, f'fill="{pg.farbe("gluehfaden")}" stroke="#000" stroke-width="0.35"')
    for a in (45, 135, 225, 315):                                 # Kreuz-Streuscheibe
        pg.line(add(c, (math.cos(math.radians(a)) * r * 0.3, math.sin(math.radians(a)) * r * 0.3)),
                add(c, (math.cos(math.radians(a)) * r * 0.95, math.sin(math.radians(a)) * r * 0.95)), THIN)
    # grimmiges Lid: Blech-Blende schräg über dem Licht
    s = -1 if mirror else 1
    pg.path([("M", add(c, (-r * 1.15 * s, -r * 1.15))), ("L", add(c, (r * 1.15 * s, -r * 1.15))), ("L", add(c, (r * 1.15 * s, -r * 0.15))), ("L", add(c, (-r * 1.15 * s, -r * 0.75)))],
            f'fill="{pg.farbe("haut")}" stroke="#000" stroke-width="0.5" stroke-linejoin="round"', close=True)


def niete(pg, c):
    pg.circle(c, 0.006, f'fill="{pg.farbe("chrom")}" stroke="#000" stroke-width="0.35"')
    pg.circle(c, 0.0025, 'fill="#111"')


def grabstein(pg, c, w=0.03, h=0.04, kreuz=True):
    x, y = c
    pg.path([("M", (x - w / 2, y + h / 2)), ("L", (x - w / 2, y - h / 2 + w / 2)), ("Q", (x - w / 2, y - h / 2), (x, y - h / 2)),
             ("Q", (x + w / 2, y - h / 2), (x + w / 2, y - h / 2 + w / 2)), ("L", (x + w / 2, y + h / 2))],
            f'fill="{pg.farbe("stein")}" stroke="#000" stroke-width="0.45" stroke-linejoin="round"', close=True)
    if kreuz:
        pg.line((x, y - h * 0.28), (x, y + h * 0.2), 'stroke="#000" stroke-width="0.6"')
        pg.line((x - w * 0.25, y - h * 0.1), (x + w * 0.25, y - h * 0.1), 'stroke="#000" stroke-width="0.6"')


def fledermaus(pg, c, w=0.032):
    x, y = c
    pg.path([("M", (x, y + w * 0.12)), ("Q", (x - w * 0.15, y - w * 0.05), (x - w * 0.3, y + w * 0.05)),
             ("Q", (x - w * 0.4, y - w * 0.15), (x - w * 0.5, y)), ("Q", (x - w * 0.3, y - w * 0.35), (x - w * 0.06, y - w * 0.2)),
             ("L", (x - w * 0.05, y - w * 0.32)), ("L", (x, y - w * 0.22)), ("L", (x + w * 0.05, y - w * 0.32)), ("L", (x + w * 0.06, y - w * 0.2)),
             ("Q", (x + w * 0.3, y - w * 0.35), (x + w * 0.5, y)), ("Q", (x + w * 0.4, y - w * 0.15), (x + w * 0.3, y + w * 0.05)),
             ("Q", (x + w * 0.15, y - w * 0.05), (x, y + w * 0.12))],
            'fill="#111" stroke="#000" stroke-width="0.3" stroke-linejoin="round"', close=True)


def flamme(pg, basis, spitze, breite):
    """züngelnde Flamme von basis nach spitze: breit am Fuß, zwei Nebenzungen, Spitze"""
    bx, by = basis; sx, sy = spitze
    dx, dy = sx - bx, sy - by
    nx, ny = -dy, dx
    l = math.hypot(nx, ny) or 1
    nx, ny = nx / l * breite, ny / l * breite
    def P(t, w): return (bx + dx * t + nx * w, by + dy * t + ny * w)
    pg.path([("M", P(0, -1.0)), ("Q", P(0.25, -1.6), P(0.45, -0.9)), ("Q", P(0.55, -1.5), P(0.75, -0.5)),
             ("Q", P(0.9, -0.3), P(1.0, 0.0)), ("Q", P(0.8, 0.5), P(0.62, 0.3)), ("Q", P(0.5, 1.4), P(0.3, 0.7)),
             ("Q", P(0.2, 1.5), P(0.0, 1.0))],
            f'fill="{pg.farbe("flamme")}" stroke="#000" stroke-width="0.45" stroke-linejoin="round"', close=True)


def reifen(pg, pk):
    """Stollenprofil: versetzte Blöcke in Reihen quer zur Laufrichtung"""
    for row in range(6):
        y = 0.02 + row * 0.037
        off = 0.0 if row % 2 == 0 else 0.03
        x = 0.012 + off
        while x + 0.04 < 0.245:
            a, b = pk.at(x, y), pk.at(x + 0.04, y + 0.024)
            pg.path([("M", pk.at(x, y)), ("L", pk.at(x + 0.04, y)), ("L", pk.at(x + 0.046, y + 0.012)), ("L", pk.at(x + 0.04, y + 0.024)),
                     ("L", pk.at(x, y + 0.024)), ("L", pk.at(x + 0.006, y + 0.012))],
                    f'fill="{pg.farbe("stollen")}" stroke="#000" stroke-width="0.4" stroke-linejoin="round"', close=True)
            x += 0.06


def chromzaehne(pg, fl):
    rachen(pg, fl)
    # Kühlergrill: Lippe als Chromleiste mit Nieten
    zahnfleisch(pg, fl, 0.016)
    for s in (0.02, 0.07, 0.12, 0.17, 0.215):
        niete(pg, fl.L(s, 0.008))
    # kantige Metallzähne, vorne groß, zum Mundwinkel hin kleiner
    for sc, hw, h in ((0.032, 0.02, 0.075), (0.078, 0.017, 0.06), (0.12, 0.015, 0.05), (0.158, 0.013, 0.04), (0.192, 0.01, 0.028), (0.218, 0.007, 0.014)):
        b0, b1, tip = fl.L(sc - hw, 0.016), fl.L(sc + hw, 0.016), fl.L(sc, 0.016 + h)
        m0, m1 = fl.L(sc - hw * 0.7, 0.016 + h * 0.35), fl.L(sc + hw * 0.7, 0.016 + h * 0.35)
        pg.path([("M", b0), ("L", m0), ("L", tip), ("L", m1), ("L", b1)],
                f'fill="{pg.farbe("chrom")}" stroke="#000" stroke-width="0.45" stroke-linejoin="round"', close=True)
        pg.line(fl.L(sc - hw * 0.3, 0.016 + h * 0.2), fl.L(sc - hw * 0.15, 0.016 + h * 0.7), THIN)   # Glanzkante


def auspuff(pg, fl):
    """Gaumen: zwei Auspuffrohre entlang der Naht, Rauchringe dazwischen"""
    rachen(pg, fl)
    zahnfleisch(pg, fl)
    Q = fl.Q
    for w0 in (0.028, 0.085):
        if w0 + 0.024 > fl.naht_max_w(0.16): continue
        pg.path([("M", Q(0.07, w0)), ("L", Q(0.30, w0)), ("L", Q(0.30, w0 + 0.022)), ("L", Q(0.07, w0 + 0.022))],
                f'fill="{pg.farbe("chrom")}" stroke="#000" stroke-width="0.45" stroke-linejoin="round"', close=True)
        pg.line(Q(0.07, w0 + 0.006), Q(0.30, w0 + 0.006), THIN)
        pg.ellipse(Q(0.30, w0 + 0.011), 0.006, 0.011, f'fill="#111" stroke="#000" stroke-width="0.4"', rot=45)
    for s, w, r in ((0.2, 0.065, 0.007), (0.24, 0.06, 0.005), (0.15, 0.065, 0.005)):
        pg.circle(Q(s, w), r, 'fill="none" stroke="#000" stroke-width="0.35"')


def grabstein_zunge(pg, fl):
    """halber Grabstein mit flacher Seite auf der Naht – in 3D ein ganzer, mit Kreuz"""
    rachen(pg, fl)
    zahnfleisch(pg, fl)
    Q = fl.Q
    pg.path([("M", Q(0.05, 0.0)), ("Q", Q(0.05, 0.07), Q(0.12, 0.078)), ("L", Q(0.26, 0.08)), ("L", Q(0.28, 0.0))],
            f'fill="{pg.farbe("stein")}" stroke="#000" stroke-width="0.5" stroke-linejoin="round"', close=True)
    # Sockel
    pg.path([("M", Q(0.26, 0.0)), ("L", Q(0.26, 0.095)), ("L", Q(0.295, 0.095)), ("L", Q(0.295, 0.0))],
            f'fill="{pg.farbe("stein")}" stroke="#000" stroke-width="0.5" stroke-linejoin="round"', close=True)
    # Kreuz: Balken auf der Naht (halb je Seite), Querbalken
    pg.path([("M", Q(0.09, 0.0)), ("L", Q(0.09, 0.012)), ("L", Q(0.22, 0.012)), ("L", Q(0.22, 0.0))], 'fill="#111"', close=True)
    pg.path([("M", Q(0.125, 0.0)), ("L", Q(0.125, 0.045)), ("L", Q(0.148, 0.045)), ("L", Q(0.148, 0.0))], 'fill="#111"', close=True)
    # Riss
    pg.polyline([Q(0.2, 0.078), Q(0.215, 0.06), Q(0.205, 0.045), Q(0.225, 0.03)], THIN)


def gespenst(pg, c):
    k = 0.014
    x, y = c
    pg.path([("M", (x - k, y + k * 1.4)), ("L", (x - k, y - k * 0.4)), ("Q", (x - k, y - k * 1.8), (x, y - k * 1.8)),
             ("Q", (x + k, y - k * 1.8), (x + k, y - k * 0.4)), ("L", (x + k, y + k * 1.4)),
             ("L", (x + k * 0.5, y + k * 0.9)), ("L", (x, y + k * 1.4)), ("L", (x - k * 0.5, y + k * 0.9))],
            'fill="#fff" stroke="#000" stroke-width="0.45" stroke-linejoin="round"', close=True)
    pg.circle((x - k * 0.35, y - k * 0.7), k * 0.18, 'fill="#111"')
    pg.circle((x + k * 0.35, y - k * 0.7), k * 0.18, 'fill="#111"')
    pg.ellipse((x, y - k * 0.1), k * 0.18, k * 0.28, 'fill="#111"')


def knochen(pg, c):
    k = 0.012
    x, y = c
    pg.path([("M", (x - k * 1.6, y - k * 0.4)), ("L", (x + k * 1.6, y - k * 0.4)), ("L", (x + k * 1.6, y + k * 0.4)), ("L", (x - k * 1.6, y + k * 0.4))],
            'fill="#fff" stroke="#000" stroke-width="0.45"', close=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pg.circle((x + sx * k * 1.7, y + sy * k * 0.45), k * 0.55, 'fill="#fff" stroke="#000" stroke-width="0.45"')
    pg.polyline([(x - k * 1.6, y - k * 0.4), (x + k * 1.6, y - k * 0.4), (x + k * 1.6, y + k * 0.4), (x - k * 1.6, y + k * 0.4)],
                'fill="#fff" stroke="none"', close=True)


def mond(pg, c, r=0.02):
    pg.circle(c, r, f'fill="{pg.farbe("licht")}" stroke="#000" stroke-width="0.45"')
    pg.circle((c[0] + r * 0.55, c[1] - r * 0.25), r * 0.85, f'fill="{pg.farbe("haut")}" stroke="none"')
    pts = [(c[0] + r * 0.55 + math.cos(math.radians(a)) * r * 0.85, c[1] - r * 0.25 + math.sin(math.radians(a)) * r * 0.85) for a in range(95, 266, 10)]
    pg.polyline(pts, 'stroke="#000" stroke-width="0.45" fill="none"')


def zaun(pg, pk, y0=0.205, y1=0.238, x0=0.012, x1=0.2):
    """schiefer Friedhofszaun: Latten mit Spitzen, zwei Querlatten"""
    x, i = x0, 0
    while x < x1:
        kipp = (0.004, -0.003, 0.002, -0.004, 0.003)[i % 5]
        top = y0 + (0.004 if i % 2 else 0.0)
        pg.polyline([pk.at(x, y1), pk.at(x + kipp, top + 0.006), pk.at(x + kipp + 0.004, top), pk.at(x + kipp + 0.008, top + 0.006), pk.at(x + 0.008, y1)],
                    f'fill="{pg.farbe("zaun")}" stroke="#000" stroke-width="0.4" stroke-linejoin="round"', close=True)
        x += 0.02; i += 1
    for y in (y0 + 0.012, y0 + 0.024):
        pg.line(pk.at(x0 - 0.004, y), pk.at(x1 + 0.002, y + 0.003), 'stroke="#000" stroke-width="0.6"')


def hand(pg, c):
    """Hand, die aus dem Boden greift"""
    x, y = c; k = 0.01
    pg.path([("M", (x - k * 0.7, y)), ("L", (x - k * 0.8, y - k * 1.2)), ("L", (x - k * 1.4, y - k * 2.2)), ("L", (x - k * 1.0, y - k * 2.4)),
             ("L", (x - k * 0.5, y - k * 1.7)), ("L", (x - k * 0.6, y - k * 3.0)), ("L", (x - k * 0.2, y - k * 3.1)), ("L", (x - k * 0.1, y - k * 1.9)),
             ("L", (x + k * 0.1, y - k * 3.3)), ("L", (x + k * 0.5, y - k * 3.2)), ("L", (x + k * 0.4, y - k * 1.8)),
             ("L", (x + k * 0.8, y - k * 2.9)), ("L", (x + k * 1.2, y - k * 2.7)), ("L", (x + k * 0.8, y - k * 1.2)), ("L", (x + k * 0.7, y))],
            f'fill="{pg.farbe("hand")}" stroke="#000" stroke-width="0.4" stroke-linejoin="round"', close=True)
    pg.path([("M", (x - k * 1.4, y + k * 0.2)), ("Q", (x, y - k * 0.6), (x + k * 1.4, y + k * 0.2))], f'fill="{pg.farbe("erde")}" stroke="#000" stroke-width="0.4"', close=True)


def namensschild(pg, pk):
    """Feld für Truck-Namen und Startnummer, zum Selbstbeschriften"""
    a, b = pk.at(0.014, 0.124), pk.at(0.118, 0.162)
    x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
    pg.polyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'fill="#fff" stroke="#000" stroke-width="0.6"', close=True)
    pg.polyline([(x0 + 0.003, y0 + 0.003), (x1 - 0.003, y0 + 0.003), (x1 - 0.003, y1 - 0.003), (x0 + 0.003, y1 - 0.003)], THIN, close=True)
    if not pg.farbig:
        pg.text(((x0 + x1) / 2, y1 - 0.006), "Name", size=2.2, style='fill="#aaa"', anchor="middle")
    c = pk.at(0.034, 0.094)
    pg.circle(c, 0.024, 'fill="#fff" stroke="#000" stroke-width="0.6"')
    pg.circle(c, 0.0205, THIN)
    if not pg.farbig:
        pg.text((c[0], c[1] + 0.017), "Nr.", size=2.2, style='fill="#aaa"', anchor="middle")
    else:
        pg.text((c[0], c[1] + 0.012), "7", size=9, style='fill="#111" font-weight="bold"', anchor="middle")


# ---------------------------------------------------------------- Motiv
class Monstertruck:
    titel = "Konstantins Monstertruck"
    anleitung = ANLEITUNG_STANDARD + [
        "Name und Startnummer auf die Tür schreiben! Mund normal auf: Grabstein-Zunge und Auspuff. Mund seitlich auf: Chromgebiss! Unter den Klappen: Gespenst und Knochen.",
    ]
    farben = {"haut": "#5a2d82", "flamme": "#ff8c1a", "chrom": "#dfe3e8", "licht": "#ffe66d", "gluehfaden": "#ffffff",
              "mund": "#b8322b", "rachen": "#1a0f1f", "stein": "#9a9a9a", "stollen": "#2b2b2b", "zahn": "#dfe3e8", "zaun": "#6b5a4a", "hand": "#a7d676", "erde": "#5b3a22"}

    def zonenfarbe(self, zone):
        if hasattr(zone, "rachen"): return "mund"
        return "haut" if zone.ecke[1] == 0 else "stollen"

    def flap(self, pg, fl):
        if fl.oeffnung == "seitlich":
            chromzaehne(pg, fl)
        elif fl.kiefer == "oben":
            auspuff(pg, fl)
        else:
            grabstein_zunge(pg, fl)

    def pocket(self, pg, pk):
        oben = pk.ecke[1] == 0
        links = pk.ecke[0] == 0
        if not oben:
            reifen(pg, pk)
            return
        # Flammen aus der Papierecke entlang der Diagonale
        for (bx, by, sx, sy, br) in ((0.012, 0.012, 0.115, 0.105, 0.013),):
            flamme(pg, pk.at(bx, by), pk.at(sx, sy), br)
        # Nieten entlang der Lippenkanten
        for t in (0.03, 0.09):
            niete(pg, pk.at(0.24, t))
        for t in (0.03, 0.09, 0.15, 0.21):
            niete(pg, pk.at(t, 0.244))
        # Dachhälfte: Scheinwerfer, Vollmond, Gespenst
        h = pk.halves["oben"]
        scheinwerfer(pg, h.incenter, mirror=not links)
        mond(pg, pk.at(0.09, 0.03))
        gespenst(pg, pk.at(0.212, 0.172))
        # Seitenhälfte = Tür: Namensschild, Startnummer, Friedhof mit Zaun und Hand
        namensschild(pg, pk)
        grabstein(pg, pk.at(0.155, 0.2), w=0.024, h=0.032)
        zaun(pg, pk)
        hand(pg, pk.at(0.085, 0.206))
        fledermaus(pg, pk.at(0.155, 0.152), w=0.026)

    def secret(self, pg, sc):
        if sc.flap.name == "B2":
            gespenst(pg, sc.incenter)
        elif sc.flap.name == "A2":
            knochen(pg, sc.incenter)


if __name__ == "__main__":
    save(render(Monstertruck()), "monstertruck", motiv=Monstertruck())
    print("geschrieben: monstertruck.svg/.pdf/.png/_3d.png")
