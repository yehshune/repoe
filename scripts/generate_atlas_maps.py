"""
generate_atlas_maps.py
- 由 GGG 官方 PoE 2 CDN 下載最新 EndgameMaps.dat64 與 WorldAreas.dat64
- 純粹根據遊戲原始資料拼湊 atlas_maps.json
- 規則包含：
  - 灰燼仲裁者: arbiter_of_ash + arbiter (青銅/鋼鐵/岩石城塞)
  - 神聖仲裁者: arbiter_of_divinity + arbiter (聖母殿/聖祖殿)
  - traverse: MapContentSet == QuestAreaOnly
  - quest: AreaMods 包含 MapIsQuestArea
  - pinnacle_boss: AreaMods 包含 MapPinnacleNoExperienceGainOrLoss
  - GrandExpedition: MapPin 包含 Logbook
  - lineage: MapPin 為 Hidden 開頭
  - hideout: IsHideout 或 名稱含 hideout
  - tower: 高塔類釘選
  - unique: IsUniqueMapArea
  - 雙語名稱 (英文 + 繁體中文)
"""
import sys
import os
import json
import re
from collections import OrderedDict

# 確保上一層 repoe 根目錄在 sys.path 中
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from RePoE.parser.util import get_cdn_url, load_file_system, create_relational_reader

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_OUTPUT_JSON = os.path.join(REPO_ROOT, "output", "atlas_maps.json")

# 灰燼仲裁者地圖 (嚴格限定這 3 個城塞)
ARBITER_OF_ASH_MAPS = {
    "MapUberBoss_CopperCitadel",  # 青銅城塞
    "MapUberBoss_IronCitadel",    # 鋼鐵城塞
    "MapUberBoss_StoneCitadel",   # 岩石城塞
}

# 神聖仲裁者地圖 (聖母殿、聖祖殿)
ARBITER_OF_DIVINITY_MAPS = {
    "MapMothersoul_Male",
    "MapMothersoul_Female",
    "MapMothersoul_Male_Quest",
    "MapMothersoul_Female_Quest",
}

def prettify_id(code: str) -> str:
    s = code
    if s.startswith("Map"):
        s = s[3:]
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", s).strip()

def build_atlas_maps_from_data(output_path=DEFAULT_OUTPUT_JSON):
    print("[1/3] 連線 GGG 官方 CDN (PoE 2)...")
    cdn_url = get_cdn_url(2)
    fs = load_file_system(cdn_url)

    print("[2/3] 載入資料表 (英文 & 繁體中文)...")
    rr_en = create_relational_reader(fs, language="English", poe2spec=True)
    rr_zh = create_relational_reader(fs, language="Traditional Chinese", poe2spec=True)

    dat_maps_en = rr_en["EndgameMaps.dat64"]
    dat_maps_zh = rr_zh["EndgameMaps.dat64"]

    zh_map_by_id = {}
    for row in dat_maps_zh.table_data:
        wa = row["WorldArea"]
        if wa:
            zh_map_by_id[wa["Id"]] = row

    print(f"[3/3] 依指定規則拼裝資料 (共 {len(dat_maps_en.table_data)} 筆地圖)...")
    result = OrderedDict()

    for row_en in dat_maps_en.table_data:
        wa_en = row_en["WorldArea"]
        if not wa_en:
            continue
        map_id = wa_en["Id"]
        map_id_lower = map_id.lower()

        row_zh = zh_map_by_id.get(map_id)
        wa_zh = row_zh["WorldArea"] if row_zh else None

        fallback_name = prettify_id(map_id)
        name_en = wa_en["Name"] or fallback_name
        name_zh = (wa_zh["Name"] if wa_zh else None) or name_en

        is_unique_map_area = bool(wa_en["IsUniqueMapArea"]) or ("unique" in map_id_lower)
        is_hideout = bool(wa_en["IsHideout"]) or ("hideout" in map_id_lower)

        pin_obj = row_en["MapPin"]
        pin_id = pin_obj["Id"] if pin_obj else ""

        area_mods = [m["Id"] for m in wa_en["AreaMods"]] if wa_en["AreaMods"] else []

        tags_set = set()

        # (a) 灰燼仲裁者
        if map_id in ARBITER_OF_ASH_MAPS:
            tags_set.add("arbiter_of_ash")
            tags_set.add("arbiter")

        # (b) 神聖仲裁者
        if map_id in ARBITER_OF_DIVINITY_MAPS:
            tags_set.add("arbiter_of_divinity")
            tags_set.add("arbiter")

        # (c) MapContentSet == "QuestAreaOnly" -> traverse
        content_set_obj = row_en["MapContentSet"]
        content_set_id = content_set_obj["Id"] if content_set_obj else ""
        if content_set_id == "QuestAreaOnly":
            tags_set.add("traverse")

        # (d) AreaMods 有 "MapIsQuestArea" -> quest
        if "MapIsQuestArea" in area_mods:
            tags_set.add("quest")

        # (e) AreaMods 有 "MapPinnacleNoExperienceGainOrLoss" -> pinnacle_boss
        if "MapPinnacleNoExperienceGainOrLoss" in area_mods:
            tags_set.add("pinnacle_boss")

        # (f) MapPin 包含 "Logbook" -> GrandExpedition
        if "Logbook" in pin_id:
            tags_set.add("GrandExpedition")

        # (g) Lineage 血脈
        if pin_id.startswith("Hidden"):
            tags_set.add("lineage")

        # (h) Hideout 藏身處
        if is_hideout:
            tags_set.add("hideout")

        # (i) 高塔
        if pin_id in ["DefaultTower", "WallTower", "PrecursorTower"] or "tower" in map_id_lower:
            tags_set.add("tower")

        # (j) 傳奇地圖
        if is_unique_map_area:
            tags_set.add("unique")

        boss_list = []
        if wa_en["Bosses_MonsterVarietiesKeys"]:
            for idx, b_en in enumerate(wa_en["Bosses_MonsterVarietiesKeys"]):
                if not b_en:
                    continue
                b_zh = (
                    wa_zh["Bosses_MonsterVarietiesKeys"][idx]
                    if (wa_zh and wa_zh["Bosses_MonsterVarietiesKeys"] and idx < len(wa_zh["Bosses_MonsterVarietiesKeys"]))
                    else None
                )
                b_id = b_en["Id"].split("/")[-1].replace("BossMap_", "").replace("Boss_", "").replace("Boss", "")
                b_name_en = b_en["Name"] or b_id
                b_name_zh = (b_zh["Name"] if b_zh else None) or b_name_en
                boss_list.append({
                    "id": b_id,
                    "name": b_name_zh,
                    "name_en": b_name_en
                })

        entry = OrderedDict()
        entry["name"] = name_en
        entry["group"] = "map"
        entry["IsUniqueMapArea"] = is_unique_map_area
        entry["IsHideout"] = is_hideout
        entry["tags"] = sorted(list(tags_set))
        if boss_list:
            entry["bosses"] = boss_list
        entry["translates"] = OrderedDict([
            ("english", name_en),
            ("traditional chinese", name_zh)
        ])

        result[map_id] = entry

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"       共生成 {len(result)} 筆地圖資料")
    print(f"寫入檔案: {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=3)
    print("完成！")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_JSON
    build_atlas_maps_from_data(out_file)
