"""Make QR PNGs for the pitch deck's links and verify each decodes back to its URL."""
import os

import cv2
import segno
import zxingcpp

HERE = os.path.dirname(os.path.abspath(__file__))
LINKS = {
    "qr-dashboard": "https://suki-pulse.vercel.app/",
    "qr-live-race": "https://suki-pulse.vercel.app/race/",
    "qr-benchmark": "https://suki-pulse.vercel.app/benchmark/",
    "qr-code": "https://github.com/riecodes/Camp-Run-with-Hermes-Agent",
}
for name, url in LINKS.items():
    path = os.path.join(HERE, f"{name}.png")
    # High error correction, 2-module quiet zone, dark ink on white for reliable phone scanning.
    segno.make(url, error="h").save(path, scale=12, border=2, dark="#111315", light="#ffffff")
    found = [b.text for b in zxingcpp.read_barcodes(cv2.imread(path))]
    assert found == [url], f"{name}: decoded {found!r}"
    print(f"{name}.png ok -> {url}")

