"""Force-render specific PDF pages where keyword filter missed table-heavy content."""
import sys
import os
import fitz

sys.stdout.reconfigure(encoding='utf-8')

PDF_DIR = r"D:\works\ZHE_DIE\zd_doc"
OUT_DIR = r"D:\works\ZHE_DIE\record_text\pdf_ocr"

# (pdf_filename, [page numbers, 1-based])
TARGETS = [
    ("a6bm-m01-block-modbus.pdf", [12, 13, 14, 15, 16, 17, 18, 31]),
    ("a6bm-i01-block-if.pdf", [8, 9, 14, 15, 16, 17, 29]),
    ("a6_io-interface_modbus_block_function_v11_161221_c.pdf", [3, 4, 11, 13, 14, 19, 20, 21, 22]),
]

for pdf_name, pages in TARGETS:
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        print(f"[SKIP] {pdf_path}")
        continue
    base = os.path.splitext(pdf_name)[0]
    doc = fitz.open(pdf_path)
    total = len(doc)
    for p in pages:
        if p > total:
            print(f"  p{p} out of range ({total})")
            continue
        page = doc[p-1]
        png_path = os.path.join(OUT_DIR, f"{base}_p{p:03d}.png")
        try:
            pix = page.get_pixmap(dpi=200)
            pix.save(png_path)
            print(f"  saved {os.path.basename(png_path)}")
        except Exception as e:
            print(f"  err p{p}: {e}")
    doc.close()
print("DONE")
