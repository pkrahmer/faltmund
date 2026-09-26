"""
Motiv: Claude als Faltmund – Selbstporträt eines Sprachmodells.

Haut wie Textzeilen, neugierige Augen, ein Cursor als Schnauze. Normal auf: eine
Sprechblase mit drei Punkten als Zunge („… tippt gerade"), Sterne am Gaumen.
Seitlich auf: ein Gebiss aus Klammern und Satzzeichen. Unter den Klappen: ein Bug
und eine Glühbirne.

Aufruf:  python3 motiv_claude.py   →  claude.svg / .pdf / .png / _3d.png
"""
import math
from faltmund import render, save, add, ANLEITUNG_STANDARD, LINE, THIN
from motiv_frosch import rachen, zahnfleisch


# ---------------------------------------------------------------- Bausteine
def zeilen(pg, pk):
    """Textzeilen-Muster: kurze Striche unterschiedlicher Länge, wie ein Absatz ohne Wörter"""
    rnd = 0
    for row in range(1, 12):
        y = row * 0.02 + 0.006
        x = 0.014
        while x < 0.23:
            rnd = (rnd * 1103515245 + 12345 + row * 7) % (2 ** 31)
            laenge = 0.012 + (rnd % 100) / 100 * 0.03
            if x + laenge > 0.236: break
            if not pg.farbig:
                pg.line(pk.at(x, y), pk.at(x + laenge, y), 'stroke="#000" stroke-width="0.35" stroke-linecap="round"')
            else:
                pg.line(pk.at(x, y), pk.at(x + laenge, y), f'stroke="{pg.palette["zeile"]}" stroke-width="0.6" stroke-linecap="round"')
            x += laenge + 0.009


def auge(pg, c, mirror, braue_hoch):
    r = 0.048
    pg.circle(c, r, f'fill="{pg.farbe("augapfel")}" stroke="#000" stroke-width="0.5"')
    pg.circle(add(c, (0.004 if not mirror else -0.004, 0.004)), 0.026, f'fill="{pg.farbe("iris")}" stroke="#000" stroke-width="0.4"')
    pg.circle(add(c, (0.004 if not mirror else -0.004, 0.004)), 0.012, 'fill="#111"')
    pg.circle(add(c, (0.012 if not mirror else -0.012, -0.008)), 0.006, 'fill="#fff"')
    # Braue: Bogen über dem Auge, eine Seite höher gezogen (neugierig)
    lift = 0.02 if braue_hoch else 0.0
    pts = []
    for a in range(210, 331, 6):
        t = (a - 210) / 120
        pts.append((c[0] + math.cos(math.radians(a)) * r * 1.35,
                    c[1] + math.sin(math.radians(a)) * r * 1.15 - lift * (t if not mirror else 1 - t)))
    pg.polyline(pts, 'stroke="#000" stroke-width="0.9" fill="none" stroke-linecap="round"')


def cursor(pg, c, vertikal):
    """blinkender Text-Cursor an der Schnauzenspitze"""
    w, h = (0.006, 0.022) if vertikal else (0.022, 0.006)
    pg.polyline([(c[0] - w, c[1] - h), (c[0] + w, c[1] - h), (c[0] + w, c[1] + h), (c[0] - w, c[1] + h)],
                'fill="#111" stroke="none"', close=True)


def klammergebiss(pg, fl):
    """Zähne aus Satzzeichen, entlang der Lippe aufgereiht, Spitze zum Mundinneren"""
    rachen(pg, fl)
    zahnfleisch(pg, fl)
    deg = math.degrees(math.atan2(fl.n[1], fl.n[0]))          # Zeichen „stehen" senkrecht zur Lippe
    zeichen = ["{", "(", "[", "|", ")", "}", "]"]
    groessen = [15, 14, 13, 11, 9, 7, 5]
    s = 0.03
    for ch, g in zip(zeichen, groessen):
        d = 0.016 + g * 0.0035                              # Zeichenmitte so, dass die Basis am Zahnfleisch sitzt
        if d + g * 0.002 > fl.lippe_max_d(s): break
        pg.text(fl.L(s, d), ch, size=g, style=f'fill="{pg.farbe("zahn")}" stroke="#000" stroke-width="0.45" font-family="DejaVu Sans Mono, Courier New, monospace" font-weight="bold"',
                anchor="middle", rot=deg + 90)
        s += 0.004 + g * 0.0022
    # zweite Reihe: kleine Sternchen und Semikolons weiter innen
    d1 = 0.115
    s = 0.02
    for ch in ("*", ";", "*"):
        if d1 > fl.lippe_max_d(s) - 0.012: break
        pg.text(fl.L(s, d1), ch, size=7, style=f'fill="{pg.farbe("zahn")}" stroke="#000" stroke-width="0.3" font-family="DejaVu Sans Mono, Courier New, monospace"',
                anchor="middle", rot=deg + 90)
        s += 0.034


def stern(pg, c, r, style):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
    pg.polyline(pts, style, close=True)


def gaumenhimmel(pg, fl):
    """Gedankenhimmel: Sterne am Gaumen, groß nahe der Naht, klein zum Mundwinkel"""
    rachen(pg, fl)
    zahnfleisch(pg, fl)
    st = f'fill="{pg.farbe("stern")}" stroke="#000" stroke-width="0.35" stroke-linejoin="round"'
    for s, w, r in ((0.10, 0.03, 0.016), (0.17, 0.05, 0.013), (0.23, 0.045, 0.010), (0.14, 0.09, 0.009),
                    (0.26, 0.10, 0.007), (0.08, 0.07, 0.007), (0.21, 0.15, 0.006), (0.30, 0.04, 0.006)):
        if w < fl.naht_max_w(s) - r:
            stern(pg, fl.Q(s, w), r, st)
    for s, w in ((0.06, 0.05), (0.19, 0.12), (0.28, 0.08), (0.12, 0.11)):
        if w < fl.naht_max_w(s) - 0.004:
            pg.circle(fl.Q(s, w), 0.0025, 'fill="#111"')


def sprechblase(pg, fl):
    """halbe Sprechblase mit flacher Seite auf der Naht – in 3D eine ganze, mit drei Punkten"""
    rachen(pg, fl)
    zahnfleisch(pg, fl)
    Q = fl.Q
    pg.path([("M", Q(0.055, 0.0)), ("Q", Q(0.055, 0.075), Q(0.13, 0.085)),
             ("L", Q(0.215, 0.088)), ("Q", Q(0.28, 0.085), Q(0.285, 0.0))],
            f'fill="{pg.farbe("zunge")}" stroke="#000" stroke-width="0.5" stroke-linejoin="round"', close=True)
    # Zipfel der Blase zum Rachen hin
    pg.path([("M", Q(0.068, 0.0)), ("L", Q(0.025, 0.012)), ("L", Q(0.075, 0.03))],
            f'fill="{pg.farbe("zunge")}" stroke="#000" stroke-width="0.5" stroke-linejoin="round"', close=True)
    # drei Punkte: Halbkreise auf der Naht, in 3D ganze Punkte
    for s in (0.125, 0.17, 0.215):
        pts = [Q(s + 0.013 * math.cos(math.radians(a)), 0.013 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        pg.polyline(pts, 'fill="#111" stroke="none"', close=True)


def bug(pg, c):
    """ein Bug – der Käfer, den ich unter der Klappe verstecke"""
    k = 0.012
    pg.ellipse(c, k * 1.1, k * 1.5, 'fill="#fff" stroke="#000" stroke-width="0.4"')
    pg.line((c[0], c[1] - k * 1.5), (c[0], c[1] + k * 1.5), THIN)
    pg.circle((c[0], c[1] - k * 1.7), k * 0.55, 'fill="#111"')
    for sx in (-1, 1):
        for dy in (-0.6, 0.1, 0.8):
            pg.polyline([(c[0] + sx * k * 0.9, c[1] + k * dy), (c[0] + sx * k * 1.8, c[1] + k * (dy - 0.4)), (c[0] + sx * k * 2.3, c[1] + k * (dy + 0.3))], THIN)
        pg.line((c[0] + sx * k * 0.3, c[1] - k * 2.1), (c[0] + sx * k * 1.0, c[1] - k * 2.9), THIN)
    for x, y in ((-0.5, -0.4), (0.5, 0.1), (-0.4, 0.8)):
        pg.circle((c[0] + x * k, c[1] + y * k), k * 0.2, 'fill="#111"')


def gluehbirne(pg, c):
    k = 0.014
    pg.circle((c[0], c[1] - k * 0.6), k * 1.3, 'fill="#fff" stroke="#000" stroke-width="0.45"')
    pg.polyline([(c[0] - k * 0.6, c[1] + k * 0.5), (c[0] + k * 0.6, c[1] + k * 0.5), (c[0] + k * 0.55, c[1] + k * 1.5), (c[0] - k * 0.55, c[1] + k * 1.5)],
                'fill="#fff" stroke="#000" stroke-width="0.45" stroke-linejoin="round"', close=True)
    pg.line((c[0] - k * 0.5, c[1] + k * 0.9), (c[0] + k * 0.5, c[1] + k * 0.9), THIN)
    pg.polyline([(c[0] - k * 0.35, c[1] + k * 0.4), (c[0] - k * 0.2, c[1] - k * 0.4), (c[0] + k * 0.2, c[1] - k * 0.4), (c[0] + k * 0.35, c[1] + k * 0.4)], THIN)
    for a in range(-150, -29, 40):
        r = math.radians(a)
        pg.line((c[0] + math.cos(r) * k * 1.7, c[1] - k * 0.6 + math.sin(r) * k * 1.7),
                (c[0] + math.cos(r) * k * 2.3, c[1] - k * 0.6 + math.sin(r) * k * 2.3), THIN)


# ---------------------------------------------------------------- Motiv
class Claude:
    titel = "Faltmund Claude – zum Ausmalen"
    anleitung = ANLEITUNG_STANDARD + [
        "Mund normal auf: Sprechblase (… tippt gerade). Mund seitlich auf: das Klammergebiss! Unter den Klappen: ein Bug und eine Idee.",
    ]
    farben = {"haut": "#f2c894", "zeile": "#c98a4a", "mund": "#3b2a66", "rachen": "#1b1433", "zunge": "#ffffff",
              "zahn": "#fff3d6", "augapfel": "#ffffff", "iris": "#4a7fb5", "stern": "#ffe27a"}

    def zonenfarbe(self, zone):
        return "mund" if hasattr(zone, "rachen") else "haut"

    def flap(self, pg, fl):
        if fl.oeffnung == "seitlich":
            klammergebiss(pg, fl)
        elif fl.kiefer == "oben":
            gaumenhimmel(pg, fl)
        else:
            sprechblase(pg, fl)

    def pocket(self, pg, pk):
        oben = pk.ecke[1] == 0
        links = pk.ecke[0] == 0
        zeilen(pg, pk)
        if oben:
            h = pk.halves["oben"]
            auge(pg, h.incenter, mirror=not links, braue_hoch=links)
            cursor(pg, add(h.mitte, (-0.02 if links else 0.02, 0.016)), vertikal=True)

    def secret(self, pg, sc):
        if sc.flap.name == "B2":
            bug(pg, sc.incenter)
        elif sc.flap.name == "A2":
            gluehbirne(pg, sc.incenter)


if __name__ == "__main__":
    save(render(Claude()), "claude", motiv=Claude())
    print("geschrieben: claude.svg/.pdf/.png/_3d.png")
