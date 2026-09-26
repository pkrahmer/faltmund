"""
Motiv: Topfkaktus in Pixel-Optik – der Kaktus aus dem Karopapier-Tierchen
(minis/tierchen) als Faltmund. Alles liegt auf einem Karoraster von 13 Kästchen
je Eckquadrat (52 × 52 auf dem Blatt), jedes Kästchen wird einzeln ausgemalt.

Farbcode je Zone (steht auch als Legende auf dem Blatt):
  Haut (obere Taschen) grün, Topf (untere Taschen) braun, Mundinneres rot.
  Buchstaben: w = weiß lassen, r = rosa, h = hellblau.  Schwarze Kästchen bleiben schwarz.

Aufruf:  python3 motiv_kaktus.py   →  kaktus.svg / .pdf / .png
"""
from faltmund import render, save, inside, ANLEITUNG_STANDARD

N = 52                      # Kästchen je Blattkante (13 je Eckquadrat)
C = 1.0 / N                 # Kästchengröße in Papier-Einheiten (≈ 3,7 mm bei 19 cm)

CELL = 'fill="none" stroke="#000" stroke-width="0.22"'
CELL_BLACK = 'fill="#111" stroke="#000" stroke-width="0.22"'
LETTER = 'fill="#888"'


def cell_center(i, j):
    return ((i + 0.5) * C, (j + 0.5) * C)


def pixel(pg, i, j, code):
    """Ein Kästchen zeichnen. code: '.' = Zonenfarbe (leer), '#' = schwarz, sonst Buchstabe."""
    x, y = i * C, j * C
    pg.polyline([(x, y), (x + C, y), (x + C, y + C), (x, y + C)], CELL_BLACK if code == "#" else CELL, close=True)
    if code not in (".", "#"):
        cx, cy = cell_center(i, j)
        pg.text((cx, cy + 0.0035), code, size=2.1, style=LETTER, anchor="middle")


def raster(pg, poly, code_fn):
    """Alle Kästchen, deren Mitte im Polygon liegt; code_fn(i, j) liefert den Code."""
    for j in range(N):
        for i in range(N):
            if inside(cell_center(i, j), poly):
                pixel(pg, i, j, code_fn(i, j))


# ---------------------------------------------------------------- Zonenmuster
STACHELN = {(3, 3), (7, 1), (10, 5), (1, 8), (5, 7), (9, 9), (2, 11), (12, 9), (6, 12), (11, 2)}
BLUME = {(11, 0): "r", (10, 1): "r", (12, 1): "r", (11, 2): "r", (11, 1): "."}       # [.P. / PBP / .P.] an der Schnauzenspitze
AUGE = {(8, 3): "#", (9, 3): "w", (8, 4): "#", (9, 4): "#"}                            # 2×2 mit Glanzpunkt


class Kaktus:
    titel = "Topfkaktus zum Ausmalen – Pixel"
    anleitung = ANLEITUNG_STANDARD + [
        "Kästchen: obere Taschen grün, Topf braun, Mund rot. w = weiß lassen, r = rosa, h = hellblau, schwarz bleibt schwarz.",
        "Mund normal auf: Zunge. Mund seitlich auf: Pixelgebiss! Unter den Klappen: ein Schluck Wasser.",
    ]

    # --- Taschen: Koordinaten (x, y) in Kästchen von der Papierecke ins Blatt hinein
    def pocket(self, pg, pk):
        oben = pk.ecke[1] == 0
        sx, sy = pk._sx, pk._sy
        cx0 = 0 if pk.ecke[0] == 0 else N - 1          # Kästchenindex der Papierecke
        cy0 = 0 if oben else N - 1

        def code(i, j):
            x, y = (i - cx0) * sx, (j - cy0) * sy        # lokal 0..12
            if oben:
                if (x, y) in BLUME: return BLUME[(x, y)]
                if (x, y) in AUGE: return AUGE[(x, y)]
                return "#" if (x, y) in STACHELN else "."
            # Topf: Rand als schwarze Reihe zur Lippe hin, darunter ein heller Streifen
            if y == 12: return "#"
            if y == 11: return "w"
            if y == 0 or x == 0: return "#"              # Topfboden / Außenkante
            return "."
        raster(pg, pk.poly, code)

    # --- Klappen: Kästchen in (s, d) = entlang der Lippe / Tiefe ins Dreieck (wie fl.L, ganzzahlig).
    #     Der Rachen liegt bei (0, 13); Kästchen mit s + d == 12 schmiegen sich an die Diagonale (Kiefernaht).
    def flap(self, pg, fl):
        def sd(i, j):
            cx, cy = cell_center(i, j)
            ox, oy = cx - fl.winkel[0], cy - fl.winkel[1]
            return int((ox * fl.e[0] + oy * fl.e[1]) / C), int((ox * fl.n[0] + oy * fl.n[1]) / C)

        def rachen_nah(i, j):
            cx, cy = cell_center(i, j)
            return ((cx - fl.rachen[0]) ** 2 + (cy - fl.rachen[1]) ** 2) < (2.3 * C) ** 2

        def an_der_naht(k, breite):
            """Block, der bei k Kästchen vom Rachen an der Diagonale liegt und `breite` Kästchen ins Dreieck reicht"""
            return {(k - a, 12 - k - b) for a in range(breite) for b in range(breite) if a + b < breite}

        marken = {}
        if fl.oeffnung == "seitlich":                                        # Pixelgebiss
            for s, laenge in ((0, 4), (2, 4), (4, 3), (6, 3), (8, 2), (10, 1)):   # vordere Reihe, große Zähne
                for d in range(1, 1 + laenge): marken[(s, d)] = "w"
            for s in (0, 2, 4):                                                # hintere Reihe
                for d in (6, 7): marken[(s, d)] = "w"
        elif fl.kiefer == "oben":                                            # Gaumen: Zäpfchen an der Naht
            for c in an_der_naht(3, 2): marken[c] = "r"
        else:                                                                # Zunge an der Naht
            for k, breite in ((2, 1), (3, 2), (4, 3), (5, 4), (6, 4), (7, 4), (8, 4), (9, 3), (10, 2), (11, 1)):
                for c in an_der_naht(k, breite): marken[c] = "r"

        def code(i, j):
            if rachen_nah(i, j): return "#"
            return marken.get(sd(i, j), ".")
        raster(pg, fl.poly, code)

    # --- unter den Klappen: Schluck Wasser (Futter des Kaktus)
    WASSER = [".OO.", "OBBO", "OBBO", ".OO."]

    def secret(self, pg, sc):
        if sc.flap.name not in ("B2", "A2"): return
        ci, cj = int(sc.incenter[0] * N) - 1, int(sc.incenter[1] * N) - 1
        for y, row in enumerate(self.WASSER):
            for x, ch in enumerate(row):
                if ch == "O": pixel(pg, ci + x, cj + y, "#")
                elif ch == "B": pixel(pg, ci + x, cj + y, "h")


if __name__ == "__main__":
    save(render(Kaktus()), "kaktus")
    print("geschrieben: kaktus.svg/.pdf/.png")
