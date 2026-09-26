"""
faltung – physikalisch plausible Faltbewegung eines Faltmunds.

Das Papier wird als starre Dreiecke behandelt, die nur an den Falzlinien knicken:
alle Kantenlängen der sichtbaren 16 Dreiecke (8 Taschenhälften, 8 Klappen) bleiben
exakt so lang wie auf dem Blatt. Die Zielformen der drei Zustände kommen aus
vorschau3d.lage(); pro Zustand und pro Animationsbild wird eine Lage gesucht, die
der Zielform so nah wie möglich kommt, ohne dass sich Papier dehnt oder staucht.

Einheiten: Meter. Blattkante = BLATT (19 cm).
"""
import sys, os
import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from vorschau3d import lage, netz, Q4

BLATT = 0.19

# ---------------------------------------------------------------- Netz
def _ist_aussen(tri):
    """Taschenhälften und Klappen: Dreiecke mit einer Kante auf dem Blattrand"""
    for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
        if (a[0] == b[0] and a[0] in (0, 1)) or (a[1] == b[1] and a[1] in (0, 1)):
            return True
    return False


DREIECKE = [t for t in netz() if _ist_aussen(t)]                     # 16 sichtbare Dreiecke
PUNKTE = sorted({p for t in DREIECKE for p in t})                     # 20 Papierpunkte
IDX = {p: i for i, p in enumerate(PUNKTE)}
KANTEN = sorted({tuple(sorted((IDX[a], IDX[b]))) for t in DREIECKE for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0]))})
L0 = np.array([np.hypot(PUNKTE[a][0] - PUNKTE[b][0], PUNKTE[a][1] - PUNKTE[b][1]) * BLATT for a, b in KANTEN])
TRI_IDX = np.array([[IDX[p] for p in t] for t in DREIECKE])
UV = np.array(PUNKTE)


# ---------------------------------------------------------------- Zustände über Bedingungen
# Statt einer geratenen Zielform wird jeder Zustand durch das beschrieben, was am echten
# Faltmund passiert: welche Papierpunkte aufeinanderliegen, Spiegelsymmetrie, wie weit
# der Mund offen ist und wie stark die Taschen um den Finger geknickt sind. Die Form
# ergibt sich dann aus den starren Dreiecken.
def P(u, v): return IDX[(u, v)]
TIPS = {"ol": P(.25, .25), "or": P(.75, .25), "ul": P(.25, .75), "ur": P(.75, .75)}
ECKE = {"ol": P(0, 0), "or": P(1, 0), "ul": P(0, 1), "ur": P(1, 1)}
KANTE_OBEN = {"l": P(.25, 0), "r": P(.75, 0)}; KANTE_UNTEN = {"l": P(.25, 1), "r": P(.75, 1)}
KANTE_LINKS = {"o": P(0, .25), "u": P(0, .75)}; KANTE_RECHTS = {"o": P(1, .25), "u": P(1, .75)}
MITTE = {"o": P(.5, 0), "u": P(.5, 1), "l": P(0, .5), "r": P(1, .5)}

SPIEGEL_X = np.array([IDX[(1 - u, v)] for u, v in PUNKTE])      # Partner bei Spiegelung links/rechts
SPIEGEL_Y = np.array([IDX[(u, 1 - v)] for u, v in PUNKTE])      # Partner bei Spiegelung oben/unten


def bedingungen(oeffnung, auf=0.0):
    """(gleich, abstand): Punktpaare, die aufeinanderliegen, und weiche Sollabstände (Papiereinheiten)"""
    gleich, abst = [], []
    # Alle vier Kantenmitten treffen sich in jedem Zustand in der Nabe (Rachen): die gerade
    # nicht benutzten Klappen liegen dann flach gefaltet innen im Kiefer.
    gleich += [(MITTE["o"], MITTE["u"]), (MITTE["o"], MITTE["l"]), (MITTE["o"], MITTE["r"])]
    if oeffnung == "geschlossen":
        gleich += [(TIPS["ol"], TIPS["or"]), (TIPS["ol"], TIPS["ul"]), (TIPS["ol"], TIPS["ur"]),
                   (KANTE_OBEN["l"], KANTE_OBEN["r"]), (KANTE_UNTEN["l"], KANTE_UNTEN["r"]),
                   (KANTE_LINKS["o"], KANTE_LINKS["u"]), (KANTE_RECHTS["o"], KANTE_RECHTS["u"])]
    elif oeffnung == "normal":
        gleich += [(TIPS["ol"], TIPS["or"]), (TIPS["ul"], TIPS["ur"]), (MITTE["l"], MITTE["r"]),
                   (KANTE_OBEN["l"], KANTE_OBEN["r"]), (KANTE_UNTEN["l"], KANTE_UNTEN["r"])]
        abst += [(TIPS["ol"], TIPS["ul"], auf)]
    else:
        gleich += [(TIPS["ol"], TIPS["ul"]), (TIPS["or"], TIPS["ur"]), (MITTE["o"], MITTE["u"]),
                   (KANTE_LINKS["o"], KANTE_LINKS["u"]), (KANTE_RECHTS["o"], KANTE_RECHTS["u"])]
        abst += [(TIPS["ol"], TIPS["or"], auf)]
    # Taschen um den Finger geknickt (beim geschlossenen Mund ergibt sich das von selbst:
    # dann sind die Taschen flache Quadrate, die zusammen eine vierseitige Pyramide bilden)
    for e, k1, k2 in (("ol", KANTE_OBEN["l"], KANTE_LINKS["o"]), ("or", KANTE_OBEN["r"], KANTE_RECHTS["o"]),
                      ("ul", KANTE_UNTEN["l"], KANTE_LINKS["u"]), ("ur", KANTE_UNTEN["r"], KANTE_RECHTS["u"])):
        if oeffnung != "geschlossen":
            abst.append((k1, k2, 0.31))
    return gleich, abst


def _res_zustand(x, gleich, abst):
    X = x.reshape(-1, 3)
    d = np.linalg.norm(X[[a for a, b in KANTEN]] - X[[b for a, b in KANTEN]], axis=1)
    r = [(d - L0) / BLATT * 60.0]
    r += [(X[a] - X[b]) / BLATT * 20.0 for a, b in gleich]
    r += [np.array([(np.linalg.norm(X[a] - X[b]) / BLATT - s) * 4.0]) for a, b, s in abst]
    # Spiegelsymmetrie links/rechts (x) und oben/unten (y)
    mx = X[SPIEGEL_X] * np.array([-1, 1, 1]); my = X[SPIEGEL_Y] * np.array([1, -1, 1])
    r += [((X - mx) / BLATT * 5.0).ravel(), ((X - my) / BLATT * 5.0).ravel()]
    # Nabe (Rachen) im Ursprung, Spitzen nach vorn (+z), Papierecken hinten
    r.append(X[MITTE["l"]] / BLATT * 10.0 if 1 else 0)
    r.append(np.array([max(0.0, 0.05 - X[TIPS[k]][2] / BLATT) * 20 for k in TIPS]))
    r.append(np.array([max(0.0, (X[ECKE[k]][2] - X[TIPS[k]][2]) / BLATT + 0.1) * 20 for k in ECKE]))
    # Außen bleibt außen: Kantenpunkte und Papierecken liegen weiter außen als ihre Spitze –
    # sonst klappt ein Dreieck spiegelverkehrt in den Mund (Papierrückseite nach außen)
    r.append(np.array([max(0.0, 0.03 - np.dot(X[k] - X[t], o) / BLATT) * 30 for k, t, o in AUSSEN]))
    return np.concatenate(r)


AUSSEN = []
for (u, v) in [(.25, 0), (.75, 0), (.25, 1), (.75, 1), (0, .25), (0, .75), (1, .25), (1, .75), (0, 0), (1, 0), (0, 1), (1, 1)]:
    t = (0.25 if u < 0.5 else 0.75, 0.25 if v < 0.5 else 0.75)
    o = np.array([(-1 if u == 0 else 1 if u == 1 else 0), (1 if v == 0 else -1 if v == 1 else 0), 0.0])
    AUSSEN.append((IDX[(u, v)], IDX[t], o / np.linalg.norm(o)))


def zu_exakt():
    """Geschlossener Mund, exakt konstruiert: Nabe hinten, alle Spitzen vorn auf der Achse,
    die vier Kantenpunkte auf einem Ring dazwischen, Klappen paarweise flach als Kreuzwände
    innen, jede Tasche entlang Ecke–Spitze geknickt."""
    r = 0.25 / np.sqrt(2)
    X = np.zeros((len(PUNKTE), 3))
    for k in TIPS: X[TIPS[k]] = (0, 0, 2 * r)
    for k in MITTE: X[MITTE[k]] = (0, 0, 0)
    for k in KANTE_OBEN: X[KANTE_OBEN[k]] = (0, r, r)
    for k in KANTE_UNTEN: X[KANTE_UNTEN[k]] = (0, -r, r)
    X[KANTE_LINKS["o"]] = X[KANTE_LINKS["u"]] = (-r, 0, r)
    X[KANTE_RECHTS["o"]] = X[KANTE_RECHTS["u"]] = (r, 0, r)
    # Papierecke: 0,25 von beiden Kantenpunkten, 0,354 von der Spitze
    for k, (sx, sy) in {"ol": (-1, 1), "or": (1, 1), "ul": (-1, -1), "ur": (1, -1)}.items():
        f = lambda h: [np.linalg.norm(h - X[KANTE_OBEN["l" if sx < 0 else "r"] if sy > 0 else KANTE_UNTEN["l" if sx < 0 else "r"]]) - .25,
                       np.linalg.norm(h - X[KANTE_LINKS["o" if sy > 0 else "u"] if sx < 0 else KANTE_RECHTS["o" if sy > 0 else "u"]]) - .25,
                       np.linalg.norm(h - X[TIPS[k]]) - 2 * r]
        X[ECKE[k]] = least_squares(f, np.array([sx * .25, sy * .25, .2])).x
    return X * BLATT


def zustand(oeffnung, auf=0.33, start=None):
    """isometrische Lage eines Zustands"""
    if oeffnung == "geschlossen":
        return zu_exakt()
    g, a = bedingungen(oeffnung, auf)
    if start is None:
        pos = lage(oeffnung)
        start = np.array([pos[p] for p in PUNKTE], dtype=float) * 0.35 * BLATT
        start -= start[MITTE["l"]]
    res = least_squares(_res_zustand, start.ravel(), args=(g, a), method="lm", max_nfev=20000)
    return res.x.reshape(-1, 3)


def ziel(oeffnung):
    return zustand(oeffnung)


def _residuen(x, Z, w_ziel, X_vor, w_vor):
    X = x.reshape(-1, 3)
    d = np.linalg.norm(X[[a for a, b in KANTEN]] - X[[b for a, b in KANTEN]], axis=1)
    r = [(d - L0) / BLATT * 60.0]
    r.append((X - Z).ravel() / BLATT * w_ziel)
    if X_vor is not None:
        r.append((X - X_vor).ravel() / BLATT * w_vor)
    return np.concatenate(r)


def loese(Z, start=None, w_ziel=1.0, X_vor=None, w_vor=0.0):
    x0 = (start if start is not None else Z).ravel()
    res = least_squares(_residuen, x0, args=(Z, w_ziel, X_vor, w_vor), method="lm", max_nfev=4000)
    return res.x.reshape(-1, 3)


def dehnung(X):
    d = np.linalg.norm(X[[a for a, b in KANTEN]] - X[[b for a, b in KANTEN]], axis=1)
    return float(np.max(np.abs(d - L0) / L0))


# ---------------------------------------------------------------- Ablauf
def ablauf(zustaende=("geschlossen", "normal", "geschlossen", "seitlich", "geschlossen"),
           fps=24, sek_halten=0.7, sek_wechsel=1.25):
    """Liste von Lagen (je 20×3) für alle Bilder. Zwischen zwei Zuständen wird die Zielform
    geblendet und jedes Bild isometrisch nachgelöst, warmgestartet vom vorigen."""
    fest = {z: None for z in set(zustaende)}
    for z in fest:
        fest[z] = zustand(z)
    n_h, n_w = round(sek_halten * fps), round(sek_wechsel * fps)
    frames = []
    X = fest[zustaende[0]]
    for a, b in zip(zustaende, zustaende[1:]):
        frames += [fest[a]] * n_h
        for i in range(1, n_w + 1):
            t = i / n_w
            t = t * t * (3 - 2 * t)
            Z = fest[a] * (1 - t) + fest[b] * t
            X = loese(Z, start=X, w_ziel=1.0, X_vor=X, w_vor=0.3)
            frames.append(X)
        X = fest[b]
        frames[-1] = X
    frames += [fest[zustaende[-1]]] * n_h
    return frames


if __name__ == "__main__":
    for z in ("geschlossen", "normal", "seitlich"):
        X = zustand(z)
        g, a = bedingungen(z, 0.33)
        print(z, "max. Dehnung %.3f %%" % (100 * dehnung(X)), "Bedingungen verfehlt um max. %.2f mm" % (1000 * max(np.linalg.norm(X[p] - X[q]) for p, q in g)))
    fr = ablauf()
    print(len(fr), "Bilder, max. Dehnung über alle Bilder %.3f %%" % (100 * max(dehnung(X) for X in fr)))
    np.save(os.path.join(os.path.dirname(__file__), "ablauf.npy"), np.array(fr))
