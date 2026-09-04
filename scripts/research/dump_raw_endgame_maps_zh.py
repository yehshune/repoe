"""
dump_raw_endgame_maps_zh.py
- 由 GGG 官方 PoE 2 CDN 提取所有 173 筆終局地圖的完整原始資料
- 包含 WorldArea 與 EndgameMapSettings 兩大層級的原始欄位 (繁體中文)
"""
import sys
import os
import json
from collections import OrderedDict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from RePoE.parser.util import get_cdn_url, load_file_system, create_relational_reader

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_OUTPUT_PATH = os.path.join(REPO_ROOT, "output", "raw_endgame_maps_zh.json")

def clean_val(val):
    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, list):
        return [clean_val(x) for x in val]
    if hasattr(val, "keys"):
        keys = list(val.keys())
        if "Id" in keys and "Name" in keys:
            return {"Id": val["Id"], "Name": val["Name"]}
        elif "Id" in keys and len(keys) <= 3:
            return val["Id"]
        elif "Id" in keys:
            return {"Id": val["Id"]}
        return str(val)
    return str(val)

def dump_raw_data(output_path=DEFAULT_OUTPUT_PATH):
    print("[1/3] 連線 GGG 官方 CDN (PoE 2)...")
    cdn_url = get_cdn_url(2)
    fs = load_file_system(cdn_url)

    print("[2/3] 載入繁體中文關聯資料表...")
    rr = create_relational_reader(fs, language="Traditional Chinese", poe2spec=True)
    dat = rr["EndgameMaps.dat64"]

    print(f"[3/3] 正在完整解析並萃取 {len(dat.table_data)} 筆地圖原始資料...")
    maps_data = OrderedDict()

    for row in dat.table_data:
        wa = row["WorldArea"]
        if not wa:
            continue
        map_id = wa["Id"]

        wa_info = OrderedDict()
        wa_info["Id"] = wa["Id"]
        wa_info["Name"] = wa["Name"]
        wa_info["Act"] = wa["Act"]
        wa_info["AreaLevel"] = wa["AreaLevel"]
        wa_info["MaxLevel"] = wa["MaxLevel"]
        wa_info["IsMapArea"] = wa["IsMapArea"]
        wa_info["IsUniqueMapArea"] = wa["IsUniqueMapArea"]
        wa_info["IsTown"] = wa["IsTown"]
        wa_info["IsHideout"] = wa["IsHideout"]
        wa_info["HasWaypoint"] = wa["HasWaypoint"]

        wa_info["Tags"] = [t["Id"] for t in wa["Tags"]] if wa["Tags"] else []

        bosses = []
        if wa["Bosses_MonsterVarietiesKeys"]:
            for b in wa["Bosses_MonsterVarietiesKeys"]:
                if b:
                    bosses.append({
                        "Id": b["Id"],
                        "Name": b["Name"]
                    })
        wa_info["Bosses"] = bosses

        monsters = []
        if wa["Monsters_MonsterVarietiesKeys"]:
            for m in wa["Monsters_MonsterVarietiesKeys"]:
                if m:
                    monsters.append({
                        "Id": m["Id"],
                        "Name": m["Name"]
                    })
        wa_info["Monsters"] = monsters

        wa_info["AreaMods"] = [m["Id"] for m in wa["AreaMods"]] if wa["AreaMods"] else []
        wa_info["Connections"] = [c["Id"] for c in wa["Connections"]] if wa["Connections"] else []
        wa_info["Topologies"] = [clean_val(t) for t in wa["Topologies"]] if wa["Topologies"] else []
        wa_info["Environment"] = wa["Environment"]["Id"] if wa["Environment"] else None
        wa_info["ParentTown"] = wa["ParentTown"]["Id"] if wa["ParentTown"] else None

        em_info = OrderedDict()
        em_info["FlavourText"] = row["FlavourText"]
        em_info["ObjectiveDescription"] = clean_val(row["ObjectiveDescription"])
        em_info["SpecialMapText"] = row["SpecialMapText"]
        em_info["SpecialMapFlavourText"] = row["SpecialMapFlavourText"]
        em_info["SpecialMapHelpText"] = row["SpecialMapHelpText"]

        em_info["MapPin"] = row["MapPin"]["Id"] if row["MapPin"] else None
        em_info["MapPinCompleted"] = row["MapPinCompleted"]["Id"] if row["MapPinCompleted"] else None
        em_info["CorruptedPin"] = row["CorruptedPin"]["Id"] if row["CorruptedPin"] else None

        if row["Decorations"]:
            em_info["Decorations"] = {
                "Id": row["Decorations"]["Id"],
                "AnimatedObject": row["Decorations"]["AnimatedObject"]
            }
        else:
            em_info["Decorations"] = None

        em_info["MapContentSet"] = row["MapContentSet"]["Id"] if row["MapContentSet"] else None
        em_info["MapContent"] = clean_val(row["MapContent"])

        m_packs = []
        if row["MonsterPacks"]:
            for mp in row["MonsterPacks"]:
                if mp:
                    m_packs.append(mp["Id"])
        em_info["MonsterPacks"] = m_packs

        em_info["Unknowns"] = {
            "Unknown0": row["Unknown0"],
            "Unknown1": row["Unknown1"],
            "Unknown2": row["Unknown2"],
            "Unknown3": row["Unknown3"],
            "Unknown4": row["Unknown4"],
            "Unknown5": row["Unknown5"],
            "Unknown6": row["Unknown6"],
            "Unknown7": row["Unknown7"],
            "Unknown8": row["Unknown8"],
            "Unknown9": row["Unknown9"],
            "Flag0": row["Flag0"],
            "Flag1": row["Flag1"],
            "Flag2": row["Flag2"],
            "Data0": row["Data0"]
        }

        maps_data[map_id] = OrderedDict([
            ("WorldArea", wa_info),
            ("EndgameMapSettings", em_info)
        ])

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"寫入檔案: {output_path} (共 {len(maps_data)} 筆地圖)...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(maps_data, f, ensure_ascii=False, indent=2)
    print("完成！")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_PATH
    dump_raw_data(out_file)
