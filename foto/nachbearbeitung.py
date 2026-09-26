"""
nachbearbeitung – Filmlook für die gerenderten Einzelbilder und Zusammenbau zum MP4.

  python3 nachbearbeitung.py            # frames/*.png → faltfrosch_film.mp4

Pro Bild: leichte Halation (Glühen um helle Stellen), sanfte Vignette, Filmkorn
(helligkeitsabhängig, jedes Bild neu, leicht farbig), minimale chromatische Aberration am Rand.
"""
import os, glob
import numpy as np
from PIL import Image, ImageFilter

HIER = os.path.dirname(os.path.abspath(__file__))


def filmlook(img, i):
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    h, w, _ = a.shape
    # Halation: helle Bereiche weich überstrahlen, leicht warm
    hell = np.clip((a - 0.78) / 0.22, 0, 1)
    glow = np.asarray(Image.fromarray((hell * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), dtype=np.float32) / 255
    a = a + glow * np.array([0.10, 0.06, 0.04])
    # chromatische Aberration: Rot minimal nach außen, Blau nach innen
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    def schieb(kanal, s):
        xs = np.clip(cx + (xx - cx) * s, 0, w - 1).astype(np.int32); ys = np.clip(cy + (yy - cy) * s, 0, h - 1).astype(np.int32)
        return kanal[ys, xs]
    a[..., 0] = schieb(a[..., 0], 0.9985); a[..., 2] = schieb(a[..., 2], 1.0015)
    # Vignette
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    a *= (1 - 0.22 * np.clip(r - 0.35, 0, None) ** 1.6)[..., None]
    # Filmkorn: stärker in den Mitten, leicht farbig, jedes Bild neu
    rng = np.random.default_rng(1000 + i)
    korn = rng.normal(0, 1, (h, w)).astype(np.float32)
    korn = np.asarray(Image.fromarray(((korn * 40 + 128).clip(0, 255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float32)
    korn = (korn - 128) / 40
    lum = a.mean(axis=2, keepdims=True)
    staerke = 0.032 * (1.2 - np.abs(lum - 0.5) * 1.4)
    farbe = rng.normal(0, 0.25, (1, 1, 3)).astype(np.float32)
    a = a + korn[..., None] * staerke * (1 + farbe)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def film(pfad=None, fps=24):
    import imageio
    pfad = pfad or os.path.join(HIER, "faltfrosch_film.mp4")
    bilder = sorted(glob.glob(os.path.join(HIER, "frames", "*.png")))
    with imageio.get_writer(pfad, fps=fps, codec="libx264", quality=None, macro_block_size=8,
                            ffmpeg_params=["-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "16"]) as w:
        for i, b in enumerate(bilder):
            w.append_data(np.asarray(filmlook(Image.open(b), i)))
    return pfad, len(bilder)


if __name__ == "__main__":
    print(film())
