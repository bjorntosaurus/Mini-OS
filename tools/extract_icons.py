"""Extract the pixel icons from the Figma PDF (page 5 = XP launcher, page 1 = desktop).
Usage: python tools/extract_icons.py path/to/figma.pdf   (needs pymupdf, pillow, numpy)
Icons are rendered at 4x, the flat background is flood-filled to transparent."""
import sys, numpy as np, pymupdf
from PIL import Image
from collections import deque
K = 1440 / 1316          # screenshot px -> pdf points
S = 4                    # render scale
NAMES = ["cpu", "bankers", "paging", "pagerep", "segmentation", "fragmentation", "disk", "multiprogramming"]
CENTERS = [(532, 413), (737, 413), (941, 413), (1146, 413), (532, 553), (737, 553), (941, 553), (1146, 553)]

def flood_transparent(img, tol=14):
    a = np.array(img.convert("RGBA")); h, w = a.shape[:2]
    bg = a[0, 0, :3].astype(int)
    seen = np.zeros((h, w), bool); dq = deque([(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)])
    while dq:
        y, x = dq.popleft()
        if y < 0 or x < 0 or y >= h or x >= w or seen[y, x]: continue
        if np.abs(a[y, x, :3].astype(int) - bg).max() > tol: continue
        seen[y, x] = True; a[y, x, 3] = 0
        dq.extend(((y+1, x), (y-1, x), (y, x+1), (y, x-1)))
    return Image.fromarray(a)

def crop(page, cx, cy, half, out, size):
    r = pymupdf.Rect((cx-half)*K, (cy-half)*K, (cx+half)*K, (cy+half)*K)
    pm = page.get_pixmap(matrix=pymupdf.Matrix(S, S), clip=r)
    img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    img = flood_transparent(img)
    bbox = img.getbbox(); img = img.crop(bbox)
    img.thumbnail((size, size), Image.LANCZOS); img.save(out)

if __name__ == "__main__":
    doc = pymupdf.open(sys.argv[1]); out = sys.argv[2] if len(sys.argv) > 2 else "assets/icons"
    for n, (cx, cy) in zip(NAMES, CENTERS):
        crop(doc[4], cx, cy, 34, f"{out}/{n}.png", 128)
    # settings gear from the 98 desktop (teal background)
    crop(doc[11], 58, 772, 24, f"{out}/settings.png", 128)
