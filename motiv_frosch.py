"""
Motiv: Faltfrosch – Zunge beim normalen Öffnen, Gruselgebiss beim seitlichen.

Aufruf:  python3 motiv_frosch.py   →  faltfrosch.svg / .pdf / .png
"""
import math
from faltmund import (Page, render, save, add, ANLEITUNG_STANDARD,
                      LINE, THIN, WHITE, BLACK)


# ---------------------------------------------------------------- Bausteine
def rachen(pg, fl, r=0.048):
    """dunkler Schlund als Kreissektor an der Rachen-Ecke"""
    pg.polyline([fl.rachen] + fl.arc_um_rachen(r, 13), BLACK, close=True)


def zahnfleisch(pg, fl, d=0.014, style=LINE):
    """Linie parallel zur Lippe, Abstand d, bis zur Hypotenuse"""
    pg.line(fl.L(0.0, d), fl.L(fl.lippe_len - d, d), style)


def zahn(pg, fl, sc, hw, h, d):
    """Fangzahn: Basis auf der Zahnfleischlinie (Tiefe d), Spitze zum Mundinneren"""
    b0, b1, tip = fl.L(sc - hw, d), fl.L(sc + hw, d), fl.L(sc, d + h)
    c0, c1 = fl.L(sc - hw * 0.62, d + h * 0.48), fl.L(sc + hw * 0.62, d + h * 0.48)
    pg.path([("M", b0), ("Q", c0, tip), ("Q", c1, b1)], f'fill="{pg.farbe("zahn")}" stroke="#000" stroke-width="0.45" stroke-linejoin="round"', close=True)


def gebiss(pg, fl):
    rachen(pg, fl)
    d0 = 0.014
    zahnfleisch(pg, fl, d0)
    # hintere Reihe auf einem Grat weiter innen (Haifisch)
    d1 = 0.105
    pg.line(fl.L(0.0, d1), fl.L(fl.lippe_len - d1, d1), THIN)
    for sc, hw, h in [(0.018, 0.011, 0.028), (0.048, 0.011, 0.026), (0.078, 0.010, 0.022),
                      (0.106, 0.009, 0.017), (0.130, 0.007, 0.011)]:
        zahn(pg, fl, sc, hw, h, d1)
    # vordere Reihe: große Fangzähne, dazwischen kleine, zum Mundwinkel hin kleiner
    for sc, hw, h in [(0.028, 0.020, 0.078), (0.062, 0.011, 0.034), (0.096, 0.019, 0.070), (0.128, 0.010, 0.030),
                      (0.160, 0.017, 0.056), (0.189, 0.009, 0.024), (0.213, 0.012, 0.022), (0.233, 0.006, 0.009)]:
        zahn(pg, fl, sc, hw, h, d0)


def gaumen(pg, fl):
    rachen(pg, fl)
    for r in (0.085, 0.135, 0.185):                     # Gaumenfalten
        pg.polyline(fl.arc_um_rachen(r, 16), THIN)
    zahnfleisch(pg, fl)
    # Zäpfchen: halbe Ellipse, flache Seite auf der Diagonale (= Kiefernaht in 3D)
    s0, rx, ry = 0.088, 0.021, 0.013
    pts = [fl.Q(s0 + rx * math.cos(t), ry * math.sin(t)) for t in (math.pi * i / 18 for i in range(19))]
    pg.polyline(pts, f'fill="{pg.farbe("zunge")}" stroke="#000" stroke-width="0.4" stroke-linejoin="round"', close=True)


def zunge(pg, fl):
    rachen(pg, fl)
    zahnfleisch(pg, fl)
    Q = fl.Q   # (s entlang Diagonale vom Rachen, w Breite) – halbe Zunge, im Dreieck gilt w <= s und s + w <= 0.354
    pg.path([("M", Q(0.030, 0.0)),
             ("Q", Q(0.040, 0.036), Q(0.075, 0.052)),
             ("Q", Q(0.105, 0.076), Q(0.140, 0.086)),
             ("Q", Q(0.172, 0.094), Q(0.205, 0.090)),
             ("Q", Q(0.238, 0.084), Q(0.262, 0.064)),
             ("Q", Q(0.292, 0.036), Q(0.300, 0.0))],
            f'fill="{pg.farbe("zunge")}" stroke="#000" stroke-width="0.5" stroke-linejoin="round"', close=True)
    pg.path([("M", Q(0.130, 0.045)), ("Q", Q(0.172, 0.064), Q(0.215, 0.060))], THIN)   # Glanzlicht


def auge(pg, c, mirror):
    r = 0.05
    pg.circle(c, r, f'fill="{pg.farbe("augapfel")}" stroke="#000" stroke-width="0.5"')
    pg.polyline([add(c, (math.cos(math.radians(a)), math.sin(math.radians(a))), r * 1.12) for a in range(205, 336, 5)], LINE)
    pg.circle(c, 0.03, f'fill="{pg.farbe("iris")}" stroke="#000" stroke-width="0.4"')
    pg.ellipse(c, 0.02, 0.013, 'fill="#111"')                          # liegende Froschpupille
    pg.circle(add(c, (-0.008 if mirror else 0.008, -0.005)), 0.005, 'fill="#fff"')


def nasenloch(pg, c):
    pg.ellipse(c, 0.007, 0.0045, 'fill="#111"')


def fliege(pg, c, scale=1.0, rot=0):
    x, y = pg.P(c); k = 0.012 * pg.S * scale; f = pg.f
    pg.group(transform=f"translate({f(x)},{f(y)}) rotate({rot})")
    for sx, rr in ((-1, -25), (1, 25)):                                 # Flügel
        pg.emit(f'<ellipse cx="{f(sx*k*0.9)}" cy="{f(-k*1.1)}" rx="{f(k*1.5)}" ry="{f(k*0.6)}" fill="#fff" stroke="#000" stroke-width="0.3" transform="rotate({rr})"/>')
    for sx in (-1, 1):                                                  # Beine
        for dy in (-0.4, 0.1, 0.6):
            pg.emit(f'<polyline points="{f(sx*k*0.7)},{f(k*dy)} {f(sx*k*1.5)},{f(k*(dy-0.3))} {f(sx*k*2.0)},{f(k*(dy+0.4))}" {THIN}/>')
    pg.emit(f'<ellipse cx="0" cy="{f(k*0.3)}" rx="{f(k*0.8)}" ry="{f(k*1.3)}" fill="#fff" stroke="#000" stroke-width="0.35"/>')
    pg.emit(f'<line x1="{f(-k*0.55)}" y1="{f(k*0.5)}" x2="{f(k*0.55)}" y2="{f(k*0.5)}" {THIN}/>')
    pg.emit(f'<line x1="{f(-k*0.4)}" y1="{f(k*1.0)}" x2="{f(k*0.4)}" y2="{f(k*1.0)}" {THIN}/>')
    pg.emit(f'<circle cx="0" cy="{f(-k*1.35)}" r="{f(k*0.6)}" fill="#fff" stroke="#000" stroke-width="0.35"/>')
    for sx in (-1, 1):
        pg.emit(f'<circle cx="{f(sx*k*0.28)}" cy="{f(-k*1.45)}" r="{f(k*0.18)}" fill="#111"/>')
    pg.end()


# ---------------------------------------------------------------- Motiv
class Frosch:
    titel = "Faltfrosch zum Ausmalen"
    farben = {"haut": "#6db33f", "fleck": "#4f8f2c", "mund": "#c9302c", "zunge": "#f08aa4", "zahn": "#fffdf3",
              "augapfel": "#ffffff", "iris": "#f2c94a", "rachen": "#3a0f12"}

    def zonenfarbe(self, zone):
        return "mund" if hasattr(zone, "rachen") else "haut"
    anleitung = ANLEITUNG_STANDARD + [
        "Mund normal auf: Zunge. Mund seitlich auf: Gruselgebiss! Unter den Klappen verstecken sich zwei Fliegen.",
    ]

    # Flecken in Taschen-Koordinaten (x, y vom Papier-Eck ins Papier hinein), obere und untere Taschen
    FLECKEN_OBEN = [(0.045, 0.115, 0.014), (0.095, 0.185, 0.011), (0.04, 0.2, 0.008), (0.16, 0.225, 0.009), (0.02, 0.05, 0.007)]
    FLECKEN_UNTEN = [(0.06, 0.20, 0.012), (0.17, 0.22, 0.008), (0.04, 0.10, 0.009), (0.12, 0.13, 0.015), (0.20, 0.06, 0.010), (0.07, 0.035, 0.007)]

    def flap(self, pg, fl):
        if fl.oeffnung == "seitlich":
            gebiss(pg, fl)                       # alle vier: Gruselgebiss
        elif fl.kiefer == "oben":
            gaumen(pg, fl)                       # Oberkiefer (unter den Augen): Gaumen + Zäpfchen
        else:
            zunge(pg, fl)                        # Unterkiefer: Zunge an der Kiefernaht

    def pocket(self, pg, pk):
        oben = pk.ecke[1] == 0
        links = pk.ecke[0] == 0
        for x, y, r in (self.FLECKEN_OBEN if oben else self.FLECKEN_UNTEN):
            pg.circle(pk.at(x, y), r, f'fill="{pg.farbe("fleck")}" stroke="#000" stroke-width="0.35"')
        if oben:
            # Augen auf der Dach-Hälfte (an der oberen Papierkante), Nasenloch an der Schnauzenspitze
            h = pk.halves["oben"]
            auge(pg, h.incenter, mirror=not links)
            nasenloch(pg, add(h.mitte, (-0.014 if links else 0.014, 0.012)))

    def secret(self, pg, sc):
        if sc.flap.name == "B2":
            fliege(pg, sc.incenter, 1.0, -30)
        elif sc.flap.name == "A2":
            fliege(pg, sc.incenter, 0.9, 20)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "faltfrosch"
    save(render(Frosch()), out, motiv=Frosch(), clip=True)
    print("geschrieben:", out + ".svg/.pdf/.png")
