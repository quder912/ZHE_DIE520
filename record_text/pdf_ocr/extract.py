"""Extract text + render keyword-hit pages from MINAS A6 PDFs."""
import sys
import os
import re
import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding='utf-8')

PDF_DIR = r"D:\works\ZHE_DIE\zd_doc"
OUT_DIR = r"D:\works\ZHE_DIE\record_text\pdf_ocr"
os.makedirs(OUT_DIR, exist_ok=True)

PDFS = [
    "a6bm-m01-block-modbus.pdf",
    "a6bm-i01-block-if.pdf",
    "a6_io-interface_modbus_block_function_v11_161221_c.pdf",
    "sx-zsv00015_r6_1c (2).pdf",
    "sx-zsv00014_r6_1c (2).pdf",
    "ime88_minas-a6_manu_c (2).pdf",
    "panaterm-for-a6_manu_c (1).pdf",
]

# Keywords (case-insensitive contains)
KEYWORDS = [
    'bit', 'command', '指令字', '迁移条件', '动作選択', '动作选择',
    '相対位置', '相对定位', '絶対位置', '绝对定位', 'JOG',
    '位 0', '位 1', 'B_B_STB', 'Err 55', 'Pr56', 'Pr60',
    '速度番号', '速度编号', '加速番号', '加速编号', '減速番号', '减速编号',
    'V0', 'A0', 'D0', 'Jump', '条件分歧', '条件分岐',
    '移行条件', 'BlockStart', 'BlkStart',
    'コマンド', '動作種別', 'b00', 'b01', 'b02', 'b03',
    'b04', 'b08', 'b16', 'b24', 'b28', 'b29', 'b30', 'b31',
    'Operation type', 'Velocity', 'Accel', 'Decel',
    '減算カウンタ', '減算计数器', '递减计数器',
    '原点復帰', '原点回归', '加減速', '加减速',
    '位置決め', '相対座標', '絶対座標',
    '32bit', '32 bit', 'Block command', 'Block data',
]

def hit_count(text, kws):
    t = text.lower()
    hits = []
    for k in kws:
        if k.lower() in t:
            hits.append(k)
    return hits

def main():
    summary = []
    for pdf_name in PDFS:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            print(f"[SKIP] not found: {pdf_path}")
            continue
        print(f"\n=== {pdf_name} ===")
        base = os.path.splitext(pdf_name)[0]
        txt_path = os.path.join(OUT_DIR, base + ".txt")
        doc = fitz.open(pdf_path)
        n = len(doc)
        print(f"pages: {n}")
        all_txt = []
        hit_pages = []
        for i in range(n):
            page = doc[i]
            try:
                blocks = page.get_text("blocks")
                page_text = "\n".join(b[4] for b in blocks if len(b) >= 5)
            except Exception as e:
                page_text = ""
                print(f"  page {i+1} text err: {e}")
            all_txt.append(f"\n===== PAGE {i+1} =====\n{page_text}")
            hits = hit_count(page_text, KEYWORDS)
            if len(hits) >= 4:
                hit_pages.append((i+1, len(hits), hits))
                # render PNG
                png_path = os.path.join(OUT_DIR, f"{base}_p{i+1:03d}.png")
                try:
                    pix = page.get_pixmap(dpi=200)
                    pix.save(png_path)
                    print(f"  HIT p{i+1} ({len(hits)} kws) -> {os.path.basename(png_path)}")
                except Exception as e:
                    print(f"  render err p{i+1}: {e}")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("".join(all_txt))
        doc.close()
        summary.append((pdf_name, n, len(hit_pages), hit_pages))
    print("\n\n========= SUMMARY =========")
    for name, n, hp_count, hp in summary:
        print(f"{name}: {n} pages, {hp_count} hit pages")
        for p, cnt, kws in hp[:40]:
            print(f"  p{p:3d} ({cnt}): {','.join(kws[:10])}")

if __name__ == "__main__":
    main()
