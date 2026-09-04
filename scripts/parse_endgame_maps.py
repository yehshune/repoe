"""
parse_endgame_maps.py
- 由 GGG 官方 CDN 直接下載並解析 PoE 2 最新 EndgameMaps.dat64 的示範腳本
"""
import sys
import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from RePoE.parser.util import get_cdn_url, load_file_system, create_relational_reader

sys.stdout.reconfigure(encoding="utf-8")

def parse_endgame_maps(language="Traditional Chinese", poe2=True):
    print(f"[1/3] 取得 GGG 官方 CDN 位址 (PoE {2 if poe2 else 1})...")
    cdn_url = get_cdn_url(2 if poe2 else 1)
    
    print(f"[2/3] 連線至 CDN 載入檔案系統索引: {cdn_url}")
    fs = load_file_system(cdn_url)
    
    print(f"[3/3] 正在解析 EndgameMaps.dat64 (語言: {language})...")
    rr = create_relational_reader(fs, language=language, poe2spec=poe2)
    
    dat = rr["EndgameMaps.dat64"]
    print(f"解析完成！共取得 {len(dat.table_data)} 筆地圖資料。\n")
    
    results = []
    for row in dat.table_data:
        world_area = row["WorldArea"]
        map_pin = row["MapPin"]
        item = {
            "AreaId": world_area["Id"] if world_area else None,
            "Name": world_area["Name"] if world_area else None,
            "FlavourText": row["FlavourText"],
            "MapPin": map_pin["Id"] if map_pin else None,
        }
        results.append(item)
    return results

if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 else "Traditional Chinese"
    maps = parse_endgame_maps(language=lang)
    
    out_dir = os.path.join(REPO_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    output_filename = os.path.join(out_dir, f"endgame_maps_{lang.replace(' ', '_')}.json")
    
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(maps, f, ensure_ascii=False, indent=2)
    
    print("前 3 筆資料示範：")
    print(json.dumps(maps[:3], ensure_ascii=False, indent=2))
    print(f"\n完整 JSON 資料已儲存至: {output_filename}")
