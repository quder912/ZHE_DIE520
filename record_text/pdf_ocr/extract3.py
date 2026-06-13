"""Extract embedded images from key Block PDF pages."""
import sys
import os
import fitz

sys.stdout.reconfigure(encoding='utf-8')

PDF_DIR = r"D:\works\ZHE_DIE\zd_doc"
OUT_DIR = r"D:\works\ZHE_DIE\record_text\pdf_ocr"

TARGETS = [
    ("a6bm-m01-block-modbus.pdf", [12, 13, 14, 15, 16, 17, 18, 31]),
    ("a6bm-i01-block-if.pdf", [8, 14, 15, 16, 17]),
    ("a6_io-interface_modbus_block_function_v11_161221_c.pdf", [3, 4, 5, 11]),
]

for pdf_name, pages in TARGETS:
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        continue
    base = os.path.splitext(pdf_name)[0]
    doc = fitz.open(pdf_path)
    for p in pages:
        if p > len(doc): continue
        page = doc[p-1]
        # Get list of images on this page
        imgs = page.get_images(full=True)
        print(f"{base} p{p}: {len(imgs)} embedded images")
        for img_idx, img in enumerate(imgs):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                png_path = os.path.join(OUT_DIR, f"{base}_p{p:03d}_img{img_idx:02d}.png")
                pix.save(png_path)
                print(f"  -> {os.path.basename(png_path)}  size={pix.width}x{pix.height}")
            except Exception as e:
                print(f"  err img{img_idx}: {e}")
    doc.close()
print("DONE")
