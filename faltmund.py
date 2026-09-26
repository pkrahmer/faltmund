"""
faltmund – Druckvorlagen für "Himmel und Hölle"-Faltmünder (Faltfrosch & Co.)

Die Bibliothek kennt nur die Faltgeometrie und die Seite. Was gezeichnet wird,
bestimmt ein Motiv-Modul (siehe motiv_frosch.py), das pro Zone Zeichenfunktionen
liefert.

Koordinaten
-----------
Alle Zonen rechnen in Papier-Einheiten (u, v) ∈ [0,1]², Ursprung oben links,
v nach unten. Umrechnung nach mm macht die Seite (Page.P). Die Vorlage wird mit
der bedruckten Seite nach UNTEN gefaltet (Ecken zur Mitte, umdrehen, Ecken zur
Mitte, Hälfte falten).

Zonen des ausgebreiteten Quadrats (4×4-Raster + Diagonalen + Rautenlinie)
--------------------------------------------------------------------------
* 4 Taschen  (Pocket)  – die Eckquadrate; außen sichtbar, je 2 Hälften
                          (durch die Papierdiagonale geteilt).
* 8 Klappen  (Flap)    – die rechtwinkligen Dreiecke zwischen Eckquadrat und
                          Rautenlinie; das ist das Mundinnere.
* 8 Geheime  (Secret)  – die Dreiecke des mittleren Quadrats; liegen unter je
                          einer Klappe, sichtbar nur beim Hochheben.
* 4 Verdeckte          – die Dreiecke zwischen Innenquadrat und Rautenlinie;
                          nie sichtbar.

Was aus den Klappenkanten in 3D wird
------------------------------------
Jede Klappe hat drei Kanten:
  papierkante  (winkel→rachen)  → SCHARNIER zwischen den Kiefern, Rachen = Mitte
  lippe        (winkel→spitze)  → LIPPE, Grenze zur Tasche (dort sitzt Zahnfleisch)
  diagonale    (rachen→spitze)  → KIEFERNAHT: die Diagonalen zweier Klappen
                                   liegen beim Öffnen aufeinander, eine halbe
                                   Zunge je Diagonale ergibt eine ganze Zunge.
Klappen an der oberen/unteren Papierkante zeigen sich beim SEITLICHEN Öffnen,
Klappen an der linken/rechten Papierkante beim NORMALEN Öffnen (Augen oben).
"""
import math

# ---------------------------------------------------------------- Vektoren
def add(a, b, s=1.0): return (a[0] + b[0] * s, a[1] + b[1] * s)
def sub(a, b):        return (a[0] - b[0], a[1] - b[1])
def dot(a, b):        return a[0] * b[0] + a[1] * b[1]
def unit(a):
    l = math.hypot(*a); return (a[0] / l, a[1] / l)
def perp_into(axis, ref):
    """Einheitsvektor senkrecht zu axis, in Richtung von ref."""
    d = dot(ref, axis); return unit((ref[0] - axis[0] * d, ref[1] - axis[1] * d))
def incenter(a, b, c):
    la, lb, lc = math.dist(b, c), math.dist(a, c), math.dist(a, b)
    s = la + lb + lc
    return ((la * a[0] + lb * b[0] + lc * c[0]) / s, (la * a[1] + lb * b[1] + lc * c[1]) / s)
def inside(p, poly):
    """liegt p im konvexen Polygon (Ecken im oder gegen Uhrzeigersinn)?"""
    sgn = 0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        cr = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if abs(cr) < 1e-12: continue
        s = 1 if cr > 0 else -1
        if sgn == 0: sgn = s
        elif s != sgn: return False
    return True


# ---------------------------------------------------------------- Seite
class Page:
    """A4-Seite mit einem Quadrat; sammelt SVG-Elemente."""
    W, H = 210.0, 297.0

    def __init__(self, size=190.0, x0=10.0, y0=18.0, farbig=False, palette=None):
        self.S, self.X0, self.Y0 = size, x0, y0
        self.out, self.defs = [], []
        self._clip = 0
        self.mm = lambda v: v * self.S
        self.farbig = farbig                 # True: ausgemalte Textur statt Ausmalvorlage
        self.palette = palette or {}

    def farbe(self, key, sonst="#fff"):
        """Füllfarbe im Farbmodus (aus der Motiv-Palette), sonst der Vorlagen-Wert (meist weiß)."""
        return self.palette.get(key, sonst) if self.farbig else sonst

    # Papier-Einheiten -> mm
    def P(self, u, v=None):
        if v is None: u, v = u
        return (self.X0 + u * self.S, self.Y0 + v * self.S)

    def emit(self, s): self.out.append(s)

    @staticmethod
    def f(x): return f"{x:.3f}"

    def pts(self, lst):
        return " ".join(f"{self.f(x)},{self.f(y)}" for x, y in lst)

    def clip(self, poly_uv):
        self._clip += 1
        cid = f"c{self._clip}"
        self.defs.append(f'<clipPath id="{cid}"><polygon points="{self.pts([self.P(p) for p in poly_uv])}"/></clipPath>')
        return cid

    # --- Primitive (alle in Papier-Einheiten) ------------------------------
    def line(self, a, b, style):
        a, b = self.P(a), self.P(b)
        self.emit(f'<line x1="{self.f(a[0])}" y1="{self.f(a[1])}" x2="{self.f(b[0])}" y2="{self.f(b[1])}" {style}/>')

    def polyline(self, pts_uv, style, close=False):
        tag = "polygon" if close else "polyline"
        self.emit(f'<{tag} points="{self.pts([self.P(p) for p in pts_uv])}" {style}/>')

    def path(self, segments, style, close=False):
        """segments: Liste von ('M',p) / ('L',p) / ('Q',c,p) in Papier-Einheiten."""
        parts = []
        for seg in segments:
            cmd, ps = seg[0], [self.P(p) for p in seg[1:]]
            parts.append(cmd + " " + " ".join(f"{self.f(x)} {self.f(y)}" for x, y in ps))
        d = " ".join(parts) + (" Z" if close else "")
        self.emit(f'<path d="{d}" {style}/>')

    def circle(self, c, r, style):
        x, y = self.P(c)
        self.emit(f'<circle cx="{self.f(x)}" cy="{self.f(y)}" r="{self.f(r * self.S)}" {style}/>')

    def ellipse(self, c, rx, ry, style, rot=0):
        x, y = self.P(c)
        tr = f' transform="rotate({rot} {self.f(x)} {self.f(y)})"' if rot else ""
        self.emit(f'<ellipse cx="{self.f(x)}" cy="{self.f(y)}" rx="{self.f(rx * self.S)}" ry="{self.f(ry * self.S)}" {style}{tr}/>')

    def text(self, c, s, size=3.6, style='fill="#000"', anchor="start", rot=0, mm=False):
        x, y = (c if mm else self.P(c))
        tr = f' transform="rotate({rot} {self.f(x)} {self.f(y)})"' if rot else ""
        font = '' if 'font-family' in style else 'font-family="Helvetica, Arial, sans-serif" '
        self.emit(f'<text x="{self.f(x)}" y="{self.f(y)}"{tr} {font}'
                  f'font-size="{size}" text-anchor="{anchor}" {style}>{s}</text>')

    def group(self, clip_id=None, transform=None):
        attrs = []
        if clip_id: attrs.append(f'clip-path="url(#{clip_id})"')
        if transform: attrs.append(f'transform="{transform}"')
        self.emit("<g " + " ".join(attrs) + ">")

    def end(self): self.emit("</g>")

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W}mm" height="{self.H}mm" viewBox="0 0 {self.W} {self.H}">\n'
                f'<rect x="0" y="0" width="{self.W}" height="{self.H}" fill="#fff"/>\n<defs>\n'
                + "\n".join(self.defs) + "\n</defs>\n" + "\n".join(self.out) + "\n</svg>\n")


# Standard-Strichstile (mm)
CUT  = 'stroke="#000" stroke-width="0.6" fill="none"'
LINE = 'stroke="#000" stroke-width="0.45" fill="none" stroke-linecap="round" stroke-linejoin="round"'
THIN = 'stroke="#000" stroke-width="0.3" fill="none" stroke-linecap="round" stroke-linejoin="round"'
FOLD = 'stroke="#9a9a9a" stroke-width="0.25" fill="none" stroke-dasharray="2.2,1.4"'
WHITE = 'fill="#fff" stroke="#000" stroke-width="0.45" stroke-linejoin="round"'
BLACK = 'fill="#111" stroke="#000" stroke-width="0.3"'


# ---------------------------------------------------------------- Zonen
class Flap:
    """Eines der 8 Mundinnen-Dreiecke (rechter Winkel im Mundwinkel).

    winkel  – Mundwinkel (Ecke am Eckquadrat und an der Papierkante)
    spitze  – Kieferspitze (Ecke des Eckquadrats zur Mitte hin)
    rachen  – Rachen (Mitte der Papierkante; in 3D der Punkt, wo alle
              vier sichtbaren Dreiecke zusammenlaufen)
    oeffnung – 'normal' (Augen oben) oder 'seitlich'
    kiefer   – 'oben'/'unten' (normal) bzw. 'links'/'rechts' (seitlich)
    seite    – 'links'/'rechts' bzw. 'oben'/'unten': welche Hälfte des Kiefers
    """

    def __init__(self, name, winkel, spitze, rachen, oeffnung, kiefer, seite):
        self.name, self.winkel, self.spitze, self.rachen = name, winkel, spitze, rachen
        self.oeffnung, self.kiefer, self.seite = oeffnung, kiefer, seite
        # Lippen-System: e entlang Lippe (winkel→spitze), n senkrecht ins Dreieck
        self.e = unit(sub(spitze, winkel))
        self.n = unit(sub(rachen, winkel))
        # Naht-System: a entlang Diagonale (rachen→spitze), b senkrecht ins Dreieck
        self.a = unit(sub(spitze, rachen))
        self.b = perp_into(self.a, sub(winkel, rachen))
        self.lippe_len = math.dist(winkel, spitze)       # 0.25
        self.naht_len = math.dist(rachen, spitze)        # 0.354

    @property
    def poly(self): return [self.winkel, self.spitze, self.rachen]

    def L(self, s, d):
        """Punkt: s entlang der Lippe (vom Mundwinkel), d senkrecht ins Dreieck."""
        return add(add(self.winkel, self.e, s), self.n, d)

    def Q(self, s, w):
        """Punkt: s entlang der Diagonale (vom Rachen), w senkrecht ins Dreieck."""
        return add(add(self.rachen, self.a, s), self.b, w)

    def lippe_max_d(self, s):
        """maximale Tiefe d an Lippenposition s (Hypotenuse)."""
        return self.lippe_len - s

    def naht_max_w(self, s):
        """maximale Breite w an Nahtposition s."""
        return min(s, self.naht_len - s)

    def arc_um_rachen(self, r, n=16):
        """Bogen um den Rachen, von Papierkante bis Diagonale."""
        u0 = unit(sub(self.winkel, self.rachen)); u1 = self.a
        ang = math.atan2(u1[1], u1[0]) - math.atan2(u0[1], u0[0])
        while ang > math.pi: ang -= 2 * math.pi
        while ang < -math.pi: ang += 2 * math.pi
        a0 = math.atan2(u0[1], u0[0])
        return [add(self.rachen, (math.cos(a0 + ang * i / (n - 1)), math.sin(a0 + ang * i / (n - 1))), r) for i in range(n)]


class Pocket:
    """Eines der 4 Eckquadrate (Tasche). Zwei Hälften, geteilt durch die
    Papierdiagonale: `kante_h` heißt die Papierkante, an der die Hälfte liegt
    ('oben','unten','links','rechts'). In 3D: Hälfte an der oberen/unteren
    Papierkante = Dach beim normalen Öffnen (dort sitzen beim Frosch die Augen)."""

    def __init__(self, name, ecke, size=0.25):
        self.name, self.ecke, self.size = name, ecke, size
        eu, ev = ecke
        self.origin = (eu, ev)
        self.poly = [(eu, ev), (eu + size, ev), (eu + size, ev + size), (eu, ev + size)]
        # Nachbarn: horizontale Papierkante (oben/unten) und vertikale (links/rechts)
        self.halves = {}
        top = ev == 0
        left = eu == 0
        pc = (eu if left else eu + size, ev if top else ev + size)               # Papierecke (→ Hinterkopf)
        mid_h = (eu + size if left else eu, ev if top else ev + size)            # Punkt auf horiz. Papierkante
        mid_v = (eu if left else eu + size, ev + size if top else ev)            # Punkt auf vert. Papierkante
        tip = (eu + size if left else eu, ev + size if top else ev)              # Spitze (zur Mitte hin)
        self.halves["oben" if top else "unten"] = Half(pc, mid_h, tip)
        self.halves["links" if left else "rechts"] = Half(pc, mid_v, tip)
        self.hinterkopf, self.spitze = pc, tip
        self._sx, self._sy = (1 if left else -1), (1 if top else -1)

    def at(self, x, y):
        """Taschen-Koordinaten: x, y von der Papierecke ins Papier hinein (0..0.25).
        So lässt sich ein Muster einmal definieren und auf alle vier Ecken spiegeln."""
        return (self.hinterkopf[0] + self._sx * x, self.hinterkopf[1] + self._sy * y)


class Half:
    """Hälfte eines Eckquadrats: ecke (Papierecke), mitte (Punkt auf der Papierkante,
    in 3D vordere Spitze des Dachs), spitze (Kieferspitze)."""
    def __init__(self, ecke, mitte, spitze):
        self.ecke, self.mitte, self.spitze = ecke, mitte, spitze
        self.poly = [ecke, mitte, spitze]
        self.incenter = incenter(ecke, mitte, spitze)


class Secret:
    """Dreieck des Innenquadrats unter einer Klappe."""
    def __init__(self, flap, poly):
        self.flap, self.poly = flap, poly
        self.incenter = incenter(*poly)


class Layout:
    """Alle Zonen des Faltquadrats."""

    def __init__(self):
        q = 0.25
        self.flaps = [
            # an der oberen/unteren Papierkante → seitliches Öffnen (Gebiss)
            Flap("A1", (q, 0), (q, q), (0.5, 0), "seitlich", "links", "oben"),
            Flap("A2", (3 * q, 0), (3 * q, q), (0.5, 0), "seitlich", "rechts", "oben"),
            Flap("A3", (q, 1), (q, 3 * q), (0.5, 1), "seitlich", "links", "unten"),
            Flap("A4", (3 * q, 1), (3 * q, 3 * q), (0.5, 1), "seitlich", "rechts", "unten"),
            # an der linken/rechten Papierkante → normales Öffnen (Augen oben)
            Flap("B1", (0, q), (q, q), (0, 0.5), "normal", "oben", "links"),
            Flap("B3", (1, q), (3 * q, q), (1, 0.5), "normal", "oben", "rechts"),
            Flap("B2", (0, 3 * q), (q, 3 * q), (0, 0.5), "normal", "unten", "links"),
            Flap("B4", (1, 3 * q), (3 * q, 3 * q), (1, 0.5), "normal", "unten", "rechts"),
        ]
        self.pockets = [Pocket("OL", (0, 0)), Pocket("OR", (0.75, 0)), Pocket("UL", (0, 0.75)), Pocket("UR", (0.75, 0.75))]
        # Geheimdreiecke: Klappe landet gespiegelt an Rautenlinie und Innenquadrat-Kante
        self.secrets = []
        for fl in self.flaps:
            self.secrets.append(Secret(fl, [self._land(fl, p) for p in fl.poly]))
        self.hidden = [[(0.5, 0), (q, q), (3 * q, q)], [(1, 0.5), (3 * q, q), (3 * q, 3 * q)],
                       [(0.5, 1), (q, 3 * q), (3 * q, 3 * q)], [(0, 0.5), (q, q), (q, 3 * q)]]

    @staticmethod
    def _land(fl, p):
        """Wo ein Punkt der Klappe nach beiden Faltungen liegt (Innenquadrat)."""
        u, v = p
        # Spiegel an der Ecke: Papierecke der Klappe
        cu = 0 if fl.winkel[0] < 0.5 else 1
        cv = 0 if fl.winkel[1] < 0.5 else 1
        # 1. Faltung: Spiegelung an Rautenlinie der Ecke  (u,v)→ Ecke-Diagonalspiegel
        du, dv = u - cu, v - cv               # relativ zur Papierecke
        su, sv = (1 if cu == 0 else -1), (1 if cv == 0 else -1)
        # in Eckkoordinaten (positiv ins Papier): x = su*du, y = sv*dv; Falte x+y=0.5 → (0.5-y, 0.5-x)
        x, y = su * du, sv * dv
        x, y = 0.5 - y, 0.5 - x
        u1, v1 = cu + su * x, cv + sv * y
        # 2. Faltung: Rautenecke zur Mitte, Falte bei 0.25 bzw. 0.75 (Achse senkrecht zur Papierkante der Klappe)
        if fl.winkel[1] in (0, 1):            # A-Klappen: Falte y = 0.25/0.75
            line = 0.25 if fl.winkel[1] == 0 else 0.75
            v1 = 2 * line - v1
        else:
            line = 0.25 if fl.winkel[0] == 0 else 0.75
            u1 = 2 * line - u1
        return (u1, v1)

    def fold_lines(self):
        ls = [((q, 0), (q, 1)) for q in (0.25, 0.5, 0.75)] + [((0, q), (1, q)) for q in (0.25, 0.5, 0.75)]
        ls += [((0, 0), (1, 1)), ((1, 0), (0, 1))]
        ls += [((0.5, 0), (1, 0.5)), ((1, 0.5), (0.5, 1)), ((0.5, 1), (0, 0.5)), ((0, 0.5), (0.5, 0))]
        return ls


# ---------------------------------------------------------------- Rendern
def render(motiv, page=None, farbig=False):
    """motiv: Objekt mit
         titel: str
         anleitung: Liste von Zeilen (ohne Nummer)
         pocket(page, pocket)            – Eckquadrat außen
         flap(page, flap)                – Mundinneres (wird geclippt aufgerufen)
         secret(page, secret) (optional) – unter der Klappe
         farben (optional)               – Palette {key: "#rrggbb"} für den Farbmodus
         zonenfarbe(zone) (optional)     – Palettenschlüssel der Grundfarbe einer Zone (Pocket/Flap)
       Rahmen, Falzlinien, Umrisse, Hinweistexte und Anleitung übernimmt render().
       farbig=True rendert das ausgemalte Quadrat als Textur (für die 3D-Vorschau)."""
    pg = page or Page(farbig=farbig, palette=getattr(motiv, "farben", {}))
    lay = Layout()
    if not pg.farbig:
        for a, b in lay.fold_lines():
            pg.line(a, b, FOLD)

    def grund(zone):
        if pg.farbig and hasattr(motiv, "zonenfarbe"):
            key = motiv.zonenfarbe(zone)
            if key: pg.polyline(zone.poly, f'fill="{pg.palette.get(key, "#fff")}" stroke="none"', close=True)

    # Mundinneres
    for fl in lay.flaps:
        cid = pg.clip(fl.poly)
        pg.group(cid)
        grund(fl)
        motiv.flap(pg, fl)
        pg.end()
        if not pg.farbig: pg.polyline(fl.poly, LINE, close=True)
    # Taschen
    for pk in lay.pockets:
        cid = pg.clip(pk.poly)
        pg.group(cid)
        grund(pk)
        motiv.pocket(pg, pk)
        pg.end()
        if not pg.farbig: pg.polyline(pk.poly, LINE, close=True)
    # Geheimes unter den Klappen
    if hasattr(motiv, "secret"):
        for sc in lay.secrets:
            cid = pg.clip(sc.poly)
            pg.group(cid)
            motiv.secret(pg, sc)
            pg.end()
    if pg.farbig:
        return pg.svg()
    # nie sichtbare Dreiecke
    for tri, rot in zip(lay.hidden, (0, 90, 0, -90)):
        c = ((tri[0][0] + tri[1][0] + tri[2][0]) / 3, (tri[0][1] + tri[1][1] + tri[2][1]) / 3)
        pg.text(c, "verdeckt – nicht ausmalen", size=3, style='fill="#aaa" font-style="italic"', anchor="middle", rot=rot)
    # Schnittlinie + Schere
    pg.polyline([(0, 0), (1, 0), (1, 1), (0, 1)], CUT, close=True)
    x, y = pg.P((0, 0))
    pg.emit(f'<text x="{pg.f(x - 1.5)}" y="{pg.f(y - 1.5)}" font-family="DejaVu Sans, Helvetica, Arial, sans-serif" font-size="4" fill="#000">✂</text>')
    # Titel + Anleitung
    pg.text((pg.W / 2, 12.5), motiv.titel, size=7, style='fill="#000" font-weight="bold"', anchor="middle", mm=True)
    ty = pg.Y0 + pg.S + 9
    for i, t in enumerate(motiv.anleitung):
        y = ty + i * 6.2
        pg.emit(f'<circle cx="{pg.f(pg.X0 + 3)}" cy="{pg.f(y - 1.3)}" r="2.6" fill="#000"/>')
        pg.text((pg.X0 + 3, y), str(i + 1), size=3.6, style='fill="#fff" font-weight="bold"', anchor="middle", mm=True)
        pg.text((pg.X0 + 8.5, y), t, size=3.6, mm=True)
    return pg.svg()


def textur(motiv, px=1400):
    """Das ausgemalte Quadrat als PIL-Bild (px × px) – Grundlage der 3D-Vorschau."""
    import io, cairosvg
    from PIL import Image
    pg = Page(size=100.0, x0=0.0, y0=0.0, farbig=True, palette=getattr(motiv, "farben", {}))
    pg.W = pg.H = 100.0
    svg = render(motiv, page=pg, farbig=True)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=px, output_height=px)
    return Image.open(io.BytesIO(png)).convert("RGB")


ANLEITUNG_STANDARD = [
    "Erst ausmalen, dann entlang der dicken Linie ausschneiden. Gestrichelte Linien sind Falzlinien.",
    "Bedruckte Seite nach UNTEN legen. Beide Diagonalen vorfalzen, dann alle vier Ecken zur Mitte falten.",
    "Umdrehen und noch einmal alle vier Ecken zur Mitte falten.",
    "Einmal in der Mitte zusammenfalten, Daumen und Zeigefinger in die vier Taschen stecken.",
]


def save(svg, basename, motiv=None, clip=False):
    """schreibt <basename>.svg, .pdf, eine Vorschau .png und – wenn motiv übergeben wird –
    <basename>_3d.png mit der farbigen 3D-Vorschau (zu, normal auf, seitlich auf)"""
    open(basename + ".svg", "w").write(svg)
    try:
        import cairosvg
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=basename + ".pdf")
        cairosvg.svg2png(bytestring=svg.encode(), write_to=basename + ".png", output_width=1240)
    except ImportError:
        print("cairosvg fehlt (pip install cairosvg) – nur SVG geschrieben")
        return
    if motiv is not None:
        from vorschau3d import vorschau_alle
        vorschau_alle(motiv).save(basename + "_3d.png")
        if clip:
            from vorschau3d import clip as _clip
            _clip(motiv, basename + "_clip.mp4")
