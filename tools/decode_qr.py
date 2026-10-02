"""Decode every QR code in the hackathon slide photos, with position so each maps to its label."""
import glob, os
import cv2, zxingcpp

found = {}
for path in sorted(glob.glob(r"C:\dev\devcon\hermes-hackathon\assets\*.jpg")):
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variants = [gray, cv2.equalizeHist(gray), cv2.GaussianBlur(gray, (3, 3), 0),
                cv2.resize(gray, None, fx=0.5, fy=0.5), cv2.resize(gray, None, fx=0.35, fy=0.35)]
    hits = {}
    for i, v in enumerate(variants):
        scale = gray.shape[1] / v.shape[1]
        for b in zxingcpp.read_barcodes(v, formats=zxingcpp.BarcodeFormat.QRCode):
            x = int(min(p.x for p in (b.position.top_left, b.position.bottom_left)) * scale)
            hits.setdefault(b.text, x)
    # OpenCV as a second opinion for anything zxing missed
    ok, texts, pts, _ = cv2.QRCodeDetectorAruco().detectAndDecodeMulti(gray)
    if ok:
        for t, p in zip(texts, pts):
            if t:
                hits.setdefault(t, int(p[:, 0].min()))
    found[os.path.basename(path)] = sorted(hits.items(), key=lambda kv: kv[1])

for name, hits in found.items():
    print(f"== {name}: {len(hits)} QR")
    for text, x in hits:
        print(f"   x={x:5d}  {text}")
