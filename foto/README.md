# foto – fotorealistischer Clip mit Blender/Cycles

```
pip install bpy==4.5.4 scipy imageio imageio-ffmpeg
python3 faltung.py            # Faltbewegung lösen → ablauf.npy
python3 buntstift.py          # Buntstiftbemalung + Höhenkarte aus dem Frosch-Motiv
python3 szene.py test 150     # Probebild
python3 szene.py alle         # alle Bilder nach frames/ (setzt fort)
python3 nachbearbeitung.py    # Filmlook + MP4
```

* **faltung.py** – 16 starre Dreiecke (Taschenhälften, Klappen), nur Knicke an den Falzlinien.
  Zustände über Bedingungen statt Zielformen: welche Papierpunkte aufeinanderliegen
  (Spitzen, Kantenmitten = Rachen, Kantenpunkte), Spiegelsymmetrie, Mundöffnung,
  Taschenknick, „außen bleibt außen". Geschlossen exakt konstruiert. Dehnung < 0,01 %.
* **buntstift.py** – Striche in zwei Lagen, Druck, Papierzahn, verwackelte Farbgrenzen,
  Graphitkonturen, gebrochene Farbschicht an den Falzen.
* **szene.py** – feines Netz (128², exakt entlang der Falze trianguliert), Falzrundung,
  0,12 mm Papier mit Subsurface, Kinderschreibtisch, Lampe + Fenster, 70 mm f/2.4, Kreisfahrt.
* **nachbearbeitung.py** – Halation, Vignette, chromatische Aberration, Filmkorn.
