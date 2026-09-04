# Scripts 說明

此目錄存放資料處理與解析相關腳本：

## 1. 主要生產工具 (Production)
* **generate_atlas_maps.py**
  * **用途**：自 GGG 官方 PoE 2 CDN 下載並解析最新 EndgameMaps.dat64 與 WorldAreas.dat64，生成專案所需的終局地圖資料庫。
  * **產出檔案**：預設為 output/atlas_maps.json。
  * **執行方式**：
    `ash
    python scripts/generate_atlas_maps.py
    `

---

## 2. 探索與研究工具 (Research / Experimental)
存放於 **esearch/** 目錄下，供反向工程與欄位分析使用：

* **esearch/parse_endgame_maps.py**
  * 基礎範例腳本，用於示範連線 CDN、讀取並印出單筆地圖的原始關聯資料。
* **esearch/dump_raw_endgame_maps_zh.py**
  * 提取所有 173 筆地圖的 WorldArea 與 EndgameMapSettings 完整原始欄位（繁體中文），匯出為 output/raw_endgame_maps_zh.json。