"""
download_atlas_icons.py
- 自 GGG 官方 PoE 2 CDN 下載所有 AtlasIconContent 原生圖示
- 自動解析貼圖集座標，裁切去背並儲存為透明 PNG
- 輸出路徑: output/icons/
"""
import sys
import os
from io import BytesIO
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from RePoE.parser.util import get_cdn_url, load_file_system
from PyPoE.poe.file.idl import IDLFile

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR = os.path.join(REPO_ROOT, "output", "icons")

def download_icons(output_dir=OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)

    print("[1/3] 連線 GGG 官方 CDN (PoE 2)...")
    cdn_url = get_cdn_url(2)
    fs = load_file_system(cdn_url)

    print("[2/3] 讀取 UIImages 貼圖集定義...")
    idl = IDLFile()
    idl.read(fs.get_file("Art/UIImages1.txt"))

    icon_records = {}
    for r in idl:
        dest = r.destination
        if "AtlasIconContent" in dest:
            name = os.path.basename(dest)
            if name not in icon_records:
                icon_records[name] = r

    print(f"[3/3] 找到 {len(icon_records)} 個輿圖內容圖示，開始下載並轉檔至 {output_dir}...")
    saved_count = 0

    for name, r in icon_records.items():
        out_path = os.path.join(output_dir, f"{name}.png")
        try:
            dds_bytes = fs.extract_dds(fs.get_file(r.source))
            if not dds_bytes or dds_bytes[:4] != b"DDS ":
                continue
            with Image.open(BytesIO(dds_bytes)) as img:
                cropped = img.crop((r.x1, r.y1, r.x2 + 1, r.y2 + 1))
                cropped.save(out_path)
                print(f"  [OK] {name}.png ({cropped.size[0]}x{cropped.size[1]})")
                saved_count += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")

    print(f"\n全部下載完成！共儲存 {saved_count} 個圖示至 {output_dir}")

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_DIR
    download_icons(out_dir)