"""
Schablone: beschriftet jede Zone mit Name und 3D-Rolle – zum Ausdrucken und
Probefalten, wenn man ein neues Motiv entwirft.
"""
from faltmund import Page, render, save, add, ANLEITUNG_STANDARD, THIN

GRAU = 'fill="#666"'


class Schablone:
    titel = "Faltmund – Zonenschablone"
    anleitung = ANLEITUNG_STANDARD + ["Probefalten und schauen, welche Beschriftung wo landet."]

    def flap(self, pg, fl):
        import math
        deg = lambda v: math.degrees(math.atan2(v[1], v[0]))
        pg.line(fl.L(0, 0.012), fl.L(fl.lippe_len - 0.012, 0.012), THIN)                 # Lippe
        pg.polyline(fl.arc_um_rachen(0.03), THIN)                                          # Rachen
        # Zonenname parallel zur Lippe, etwas nach innen
        pg.text(fl.L(0.11, 0.045), f"{fl.name} – {fl.oeffnung}, Kiefer {fl.kiefer}, {fl.seite}", size=2.4, style=GRAU,
                anchor="middle", rot=deg(fl.e))
        pg.text(fl.L(0.10, 0.022), "Lippe (zur Tasche)", size=2.0, style=GRAU, anchor="middle", rot=deg(fl.e))
        pg.text(fl.Q(0.16, 0.010), "Naht = Diagonale", size=2.0, style=GRAU, anchor="middle", rot=deg(fl.a))
        pg.text(add(add(fl.winkel, fl.n, 0.12), fl.e, 0.010), "Scharnier = Papierkante", size=2.0, style=GRAU,
                anchor="middle", rot=deg(fl.n))
        pg.text(add(fl.rachen, add(fl.a, fl.b), 0.05), "Rachen", size=2.0, style=GRAU, anchor="middle", rot=deg(fl.a))

    def pocket(self, pg, pk):
        for name, h in pk.halves.items():
            pg.text(h.incenter, f"Tasche {pk.name} – Hälfte {name}", size=2.4, style=GRAU, anchor="middle")
        pg.text(add(pk.hinterkopf, (0.01 * pk._sx, 0.012 * pk._sy)), "Hinterkopf", size=2.0, style=GRAU,
                anchor="start" if pk._sx > 0 else "end")

    def secret(self, pg, sc):
        pg.text(sc.incenter, f"unter {sc.flap.name}", size=2.4, style=GRAU, anchor="middle")


if __name__ == "__main__":
    save(render(Schablone()), "schablone")
    print("geschrieben: schablone.svg/.pdf/.png")
