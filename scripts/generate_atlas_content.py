"""
generate_atlas_content.py
- 由 GGG 官方 PoE 2 CDN 下載最新 EndgameMapContent.dat64
- 萃取地圖內容 (機制、強化、標記)，生成 atlas_content.json
- 雙語結構: 英文 + 繁體中文
- 包含輿圖動態狀態與特殊標記 (譫妄迷霧、已淨化、流浪商人、宏偉之鏡等)
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

DEFAULT_OUTPUT_JSON = os.path.join(REPO_ROOT, "output", "atlas_content.json")

# 特殊與動態狀態項目 (非 EndgameMapContent 原生 row，或供 POE2Radar 補足輿圖特殊狀態)
SPECIAL_CONTENT = OrderedDict([
    ("1000", OrderedDict([
        ("name", "Corruption"),
        ("icon", "AtlasIconContentCorruption"),
        ("desc", "This map is Corrupted."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "腐化"),
                ("desc", "此地圖已被腐化。")
            ]))
        ]))
    ])),
    ("1001", OrderedDict([
        ("name", "Grand Expedition"),
        ("icon", "AtlasIconContentExpedition"),
        ("desc", "Area contains a Grand Expedition"),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "大型探險"),
                ("desc", "區域含有一個大型探險")
            ]))
        ]))
    ])),
    ("1002", OrderedDict([
        ("name", "Delirium Fog"),
        ("icon", "AtlasIconContentDelirium"),
        ("desc", "Players in area are Delirious."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "譫妄迷霧"),
                ("desc", "區域內的玩家受到譫妄籠罩。")
            ]))
        ]))
    ])),
    ("1003", OrderedDict([
        ("name", "Cleansed"),
        ("icon", "AtlasIconContentSanctificationBoss"),
        ("desc", "Area has been Cleansed."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "已淨化"),
                ("desc", "區域已淨化。")
            ]))
        ]))
    ])),
    ("1004", OrderedDict([
        ("name", "Wandering Trader"),
        ("icon", "AtlasIconContentTrader"),
        ("desc", "Area contains a Wandering Trader."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "流浪商人"),
                ("desc", "區域含有一位流浪商人。")
            ]))
        ]))
    ])),
    ("1005", OrderedDict([
        ("name", "Corrupted Nexus"),
        ("icon", "AtlasIconContentCorruptionNexus"),
        ("desc", "Area contains a Corrupted Boss."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "腐化樞紐"),
                ("desc", "區域含有一個腐化頭目。")
            ]))
        ]))
    ])),
    ("1006", OrderedDict([
        ("name", "Deadly Map Boss"),
        ("icon", "AtlasIconContentMapBoss"),
        ("desc", "Area contains a Deadly Map Boss."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "致命地圖頭目"),
                ("desc", "區域含有一個致命地圖頭目。")
            ]))
        ]))
    ])),
    ("1007", OrderedDict([
        ("name", "Grand Mirror"),
        ("icon", "AtlasIconContentGigaMirror"),
        ("desc", "Contains a reflection of the Map Boss. When the bosses are defeated Delirium fog spreads to nearby Maps."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "宏偉之鏡"),
                ("desc", "包含地圖頭目的倒影；擊敗頭目後，譫妄迷霧會擴散到鄰近地圖。")
            ]))
        ]))
    ])),
    ("1008", OrderedDict([
        ("name", "Unique Map"),
        ("icon", "AtlasIconContentUniqueMap"),
        ("desc", "Area is a Unique Map."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "傳奇地圖"),
                ("desc", "區域為傳奇地圖。")
            ]))
        ]))
    ])),
    ("1009", OrderedDict([
        ("name", "Hideout"),
        ("icon", "AtlasIconContentHideout"),
        ("desc", "Area contains a Hideout."),
        ("translates", OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", "藏身處"),
                ("desc", "區域含有一個藏身處。")
            ]))
        ]))
    ]))
])

def clean_markup(text: str) -> str:
    """清理 GGG 標記語法，例如 [Tag|Display] -> Display, [Display] -> Display"""
    if not text:
        return ""
    text = re.sub(r"\[[^|\]]+\|([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]", r"\1", text)
    return text.strip()

def build_atlas_content_from_data(output_path=DEFAULT_OUTPUT_JSON):
    print("[1/3] 連線 GGG 官方 CDN (PoE 2)...")
    cdn_url = get_cdn_url(2)
    fs = load_file_system(cdn_url)

    print("[2/3] 載入 EndgameMapContent.dat64 (英文 & 繁體中文)...")
    rr_en = create_relational_reader(fs, language="English", poe2spec=True)
    rr_zh = create_relational_reader(fs, language="Traditional Chinese", poe2spec=True)

    tbl_en = rr_en["EndgameMapContent.dat64"]
    tbl_zh = rr_zh["EndgameMapContent.dat64"]

    print(f"[3/3] 依規則拼裝內容資料 (共 {len(tbl_en.table_data)} 筆原生機制)...")
    result = OrderedDict()

    for idx, row_en in enumerate(tbl_en.table_data):
        row_zh = tbl_zh.table_data[idx] if idx < len(tbl_zh.table_data) else None
        key = str(100 + idx)

        name_en = row_en["Name"] or ""
        desc_en = clean_markup(row_en["Description"])

        vis = row_en["VisualIdentity"]
        icon = ""
        if vis is not None:
            raw_icon = vis["AtlasIcon"] or vis["PassiveArt"]
            if raw_icon:
                icon = os.path.basename(raw_icon).replace(".dds", "").replace(".png", "")

        # 幻像異界若無原生圖示，導向內建 Delirium 圖示
        if row_en["Id"] == "Simulacrum" and (not icon or icon == "DeliriumNotable7"):
            icon = "AtlasIconContentDelirium"

        name_zh = (row_zh["Name"] if row_zh else None) or name_en
        desc_zh = clean_markup(row_zh["Description"]) if row_zh else desc_en

        entry = OrderedDict()
        entry["name"] = name_en
        entry["icon"] = icon
        entry["desc"] = desc_en
        entry["translates"] = OrderedDict([
            ("traditional chinese", OrderedDict([
                ("name", name_zh),
                ("desc", desc_zh)
            ]))
        ])

        result[key] = entry

    # 合併特殊與動態狀態項目
    for k, v in SPECIAL_CONTENT.items():
        result[k] = v

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"       共生成 {len(result)} 筆機制與狀態項目")
    print(f"寫入檔案: {output_path} ...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=3)
    print("完成！")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_JSON
    build_atlas_content_from_data(out_file)