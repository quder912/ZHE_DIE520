"""提取 sx-zsv00015 P83~P95 的完整文本流（UTF-8 输出），用于查 Block 字段定义"""
import fitz, sys, os
pdf = r"D:\works\ZHE_DIE\zd_doc\sx-zsv00015_r6_1c (2).pdf"
doc = fitz.open(pdf)
out = r"D:\works\ZHE_DIE\record_text\pdf_ocr\zsv15_p83_p100_full.txt"
with open(out, 'w', encoding='utf-8') as f:
    for pg_num in range(82, 100):  # P83 到 P100 索引82~99
        if pg_num >= len(doc):
            break
        page = doc[pg_num]
        f.write(f"\n\n============ PAGE {pg_num+1} ============\n")
        # 用 dict 模式拿到带位置的文字
        d = page.get_text("dict")
        # 遍历 blocks > lines > spans
        for block in d.get("blocks", []):
            if block.get("type", 0) != 0:  # 不是 text block 就跳过
                continue
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                if line_text.strip():
                    # 把 bbox 也带上，便于人工对齐表格
                    bbox = line.get("bbox", [0,0,0,0])
                    f.write(f"[x={bbox[0]:.0f},y={bbox[1]:.0f}] {line_text}\n")
print(f"已写: {out}")
print(f"文件大小: {os.path.getsize(out)} 字节")
