# faltmund – Druckvorlagen für Himmel-und-Hölle-Faltmünder

Ein kleiner Generator für A4-Ausmalvorlagen von Faltmündern (Faltfrosch,
Monster, Drache, …). Die Bibliothek kennt nur die Faltgeometrie; jedes Motiv
ist ein eigenes Modul, das sagt, was in welche Zone gezeichnet wird.

```
faltmund.py          Geometrie, Zonen, Seite, Rendern (SVG → PDF/PNG via cairosvg)
motiv_frosch.py      der Faltfrosch (Zunge normal, Gruselgebiss seitlich, Fliegen unter den Klappen)
motiv_claude.py      Claude als Faltmund: Textzeilen-Haut, Sprechblase, Klammergebiss, Sternenhimmel am Gaumen
motiv_kaktus.py      der Topfkaktus aus dem Karopapier-Tierchen, Pixel-Optik: Karoraster 52×52, Kästchen einzeln ausmalen
motiv_schablone.py   Zonenschablone mit Beschriftung – zum Probefalten bei neuen Motiven
vorschau3d.py        farbige 3D-Vorschau (beide Öffnungen) aus der ausgemalten Vorlage
```

## Benutzen

```
pip install cairosvg
python3 motiv_frosch.py            # → faltfrosch.svg / .pdf / .png / _3d.png
python3 motiv_kaktus.py            # → kaktus.svg / .pdf / .png
python3 motiv_schablone.py         # → schablone.svg / .pdf / .png
```

Drucken: A4, 100 %, nicht "an Seite anpassen". Falten mit der bedruckten
Seite nach unten (steht als Anleitung auf dem Blatt).

## Ein neues Motiv

Ein Motiv ist eine Klasse mit `titel`, `anleitung` und drei Methoden.
Alle Koordinaten sind Papier-Einheiten 0..1 (Ursprung oben links), die Seite
rechnet in mm um. Innerhalb der Methoden ist bereits auf die Zone geclippt –
was über den Rand hinausragt, wird abgeschnitten.

```python
from faltmund import render, save, ANLEITUNG_STANDARD, LINE, THIN, WHITE, BLACK

class Monster:
    titel = "Faltmonster"
    anleitung = ANLEITUNG_STANDARD + ["Normal auf: Zunge. Seitlich auf: Zähne."]

    def flap(self, pg, fl):      # eines der 8 Mundinnen-Dreiecke
        if fl.oeffnung == "seitlich": ...      # A1..A4: sichtbar beim seitlichen Öffnen
        elif fl.kiefer == "oben": ...          # B1, B3: Oberkiefer beim normalen Öffnen
        else: ...                              # B2, B4: Unterkiefer

    def pocket(self, pg, pk):    # eines der 4 Eckquadrate (außen, Haut)
        h = pk.halves["oben"]    # Hälfte an der oberen Papierkante = Dach beim normalen Öffnen
        pg.circle(h.incenter, 0.05, WHITE)

    def secret(self, pg, sc):    # optional: Dreieck unter der Klappe sc.flap
        ...

save(render(Monster()), "monster")
```

### Was in 3D aus den Kanten einer Klappe wird

Jede Klappe (`Flap`) ist ein rechtwinkliges Dreieck mit den Ecken
`winkel` (Mundwinkel), `spitze` (Kieferspitze) und `rachen` (Mitte der
Papierkante, in 3D der Punkt, wo alle vier sichtbaren Dreiecke zusammenlaufen).

| Kante              | von → nach      | wird in 3D zu                                      |
|--------------------|-----------------|----------------------------------------------------|
| Papierkante        | winkel → rachen | **Scharnier** zwischen den beiden Kiefern           |
| Gitterlinie        | winkel → spitze | **Lippe** – Grenze zur Tasche, hier sitzt Zahnfleisch |
| Diagonale          | rachen → spitze | **Kiefernaht** – zwei Diagonalen legen sich aufeinander |

Deshalb: Zähne an die Lippe, Zunge/Zäpfchen mit der flachen Seite auf die
Diagonale (halbe Form je Klappe ergibt in 3D eine ganze).

Zwei lokale Koordinatensysteme pro Klappe:

* `fl.L(s, d)` – `s` entlang der Lippe (vom Mundwinkel), `d` senkrecht nach
  innen. Maximale Tiefe: `fl.lippe_max_d(s)`.
* `fl.Q(s, w)` – `s` entlang der Diagonale (vom Rachen), `w` senkrecht nach
  innen. Maximale Breite: `fl.naht_max_w(s)`.
* `fl.arc_um_rachen(r)` – Bogenpunkte um den Rachen (für Schlund, Gaumenfalten).

Taschen (`Pocket`): `pk.halves["oben"|"unten"|"links"|"rechts"]` sind die
beiden Hälften (benannt nach der Papierkante, an der sie liegen), jede mit
`incenter`, `mitte` (Punkt auf der Papierkante = vordere Dachspitze, beim
Frosch die Nasenlöcher) und `spitze`. `pk.at(x, y)` spiegelt ein Muster von
der Papierecke aus auf alle vier Ecken.

Die Zonenschablone (`motiv_schablone.py`) druckt all das beschriftet aus –
einmal falten, und man sieht, welche Zone wo landet.

## Pixel-Motive

`motiv_kaktus.py` zeigt das zweite Muster: statt Linien ein Karoraster
(`N = 52` Kästchen je Blattkante, 13 je Eckquadrat). `raster(pg, poly, code_fn)`
zeichnet jedes Kästchen, dessen Mitte in der Zone liegt – Ränder werden so zu
Treppen statt zu angeschnittenen Kästchen. `code_fn(i, j)` liefert `.` (Zonenfarbe),
`#` (schwarz) oder einen Buchstaben, der als Farbcode ins Kästchen kommt.
In den Klappen rechnet man in `(s, d)` – Kästchen entlang der Lippe und Tiefe –,
der Rachen liegt bei `(0, 13)`, Kästchen mit `s + d == 12` liegen an der Diagonale.
`faltmund.inside(p, poly)` ist der Punkt-im-Polygon-Test dafür.

## 3D-Vorschau in Farbe

`save(svg, name, motiv=motiv)` schreibt zusätzlich `<name>_3d.png`: das Motiv als
Faltmund in drei Ansichten: „zu", „normal auf", „seitlich auf". Dafür braucht
ein Motiv einen Farbmodus:

* `farben` – Palette `{schlüssel: "#rrggbb"}`; `haut` und `mund` werden auch für
  die untexturierten Füllflächen des Kopfes benutzt.
* `zonenfarbe(zone)` – Palettenschlüssel der Grundfarbe einer Zone (Tasche/Klappe).
* In den Zeichenfunktionen `pg.farbe("zunge")` statt `#fff` als Füllung: liefert
  im Farbmodus die Palettenfarbe, in der Ausmalvorlage Weiß. `pg.farbig` sagt,
  welcher Modus gerade läuft (das Pixel-Motiv füllt damit die Kästchen).

`faltmund.textur(motiv)` rendert das ausgemalte Quadrat als Bild, `vorschau3d.modell()`
ordnet die Zonen als starre Dreiecke an (Rachen hinten, Mundwinkel auf der
Scharnierachse, Kieferspitzen vorne; jeder Kiefer ein Dach aus den beiden Taschen-
hälften), `vorschau3d.vorschau()` rastert das mit Tiefenpuffer und einfacher
Schattierung. Es ist ein Anschauungsmodell – die echte Faltung mit Fingern in den
Taschen ist weicher –, aber welche Zone wo und in welcher Öffnung zu sehen ist, stimmt.
