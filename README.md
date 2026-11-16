# Map data tools

## 賽道資料桌面工具

使用含 Tkinter 的 Python 3.10 以上版本，在專案目錄執行：

```powershell
python -m pip install -r requirements.txt
python track_app.py
```

已安裝 uv 時，也可執行 `uv run --with-requirements requirements.txt python track_app.py`。

1. **原始排序**。選取 DXF 後，先查看依端點串接的路段編號。程式讀取模型空間中的平面直線（`LINE`）與圓弧（`ARC`），路段必須能接成一圈。有輔助線時可指定實際路徑的圖層。
2. **選擇起點**。點選圖上的接點，或輸入接點的原始編號，再按「確認起點並重新排序」。可用圖下方的工具列縮放或平移。
3. **重新排序與方向**。預覽會從新起點重新以 1 編號。選擇保留或反轉行駛方向，圖上的編號與出發箭頭會更新，再按「確認方向」。
4. **確認輸出**。核對最終排序、比例與橫向加速度，按「完成並檢視分析」，即可直接在視窗查看分析圖。分析完成後可選擇 Excel、CSV、角錐 INI 或分析圖，各自指定儲存資料夾。內附的根目錄 FSAE A 2025 範例沿用舊工具的 0.1 公尺／DXF 單位，其他未設定單位的 DXF 預設為 1，可依圖面調整。XY 輸出保留 CAD 原點。

檔案會直接儲存在選定的資料夾，並以 DXF 檔名作為前綴。重複輸出會加上編號，例如 `fsae_A_2025_geometry_2.xlsx`。

| 按鈕 | 檔案 | 內容 |
| --- | --- | --- |
| 匯出 Excel | `*_geometry.xlsx`、`*_coordinates_xy.xlsx` | 幾何 Excel 僅含 `Trackdata` 工作表，XY 座標另存一份 Excel |
| 匯出 CSV | `*_geometry.csv`、`*_coordinates_xy.csv` | `Trackdata` 路段明細、XY 座標 |
| 匯出 INI | `*_cones.ini` | 按 XY 取樣點的順序放置模擬器物件，每筆座標對應一個 `[MODEL_n]` |
| 儲存分析圖 | `*_track_analysis.png` | 曲率、彎道半徑分布、長度與估算時間加權、曲率頻譜及波長圖，也可在介面內查看 |

INI 使用與 Excel、CSV 相同的 XY 取樣點，依原本的模擬器座標軸格式寫入 `POSITION=-X, 高度, Y`。高度是平面上的 Z，在模擬器的 `POSITION` 裡對應第二軸。按「INI 設定」可調整高度、起始物件編號、模型檔名、物件名稱、旋轉與物理屬性。預設值取自 `cone_to_ini.py`，使用 `cone.kn5`、`AC_POBJECT_999_3`、高度 `-0.419`、第一個物件 `MODEL_1`、旋轉 `0, 0, 0` 和 `PHYSICAL=1`。INI 引用的模型檔須由模擬器端提供。

XY 檔案按行駛順序排列 `Point`、`X`、`Y`。完成分析後可選擇「XY 取樣方式」，Excel、CSV 和 INI 採用相同規則。

- **每段取 N 點**。每段直線或圓弧等分取樣，包含兩端，預設 5 點，至少 2 點。相鄰路段共用的接點只寫一次。
- **每 N 公尺取一點**。從起點開始，沿整圈累積的線長與弧長按固定間距取樣，預設 1 公尺。路段接點在落於取樣位置時寫出，整圈終點會補上，最後一段間距可能較短。

時間加權以指定的橫向加速度估算各彎道通過時間，預設使用 1.6 g。

## 車手訓練模擬器圖資建立
### [角錐定位工具](introduction/DXF_to_cone.md)
1. 先用繪圖軟體畫出角錐位置，用畫圓定位角椎座標(半徑隨便定都可以)
1. 下載成DXF
1. 點連結使用角錐定位工具
1. 產生所有角椎的xy座標csv檔，用excel就可以開啟檢查
### [ini產生器](introduction/cone_to_ini.md)
1. 準備好**角錐定位工具**產生的csv
1. 點連結使用ini產生器 (如果多個ini檔案請更改模型編號，上面連結點進去有說明)
1. 產生ini
1. 放到ACC需要的資料夾使用

## 賽道模擬與分析資料建立
### [賽道數據產生工具](introduction/DXF_to_lapdata.md)
1. 用繪圖軟體用直線、圓弧畫出賽道輪廓(如果要輔助的線條記得轉建構線條)
1. 下載成DXF
1. 點連結啟動賽道數據產生工具
1. 設定好起跑點與賽道方向
1. 生成excel賽道數據
### [賽道xy座標工具](introduction/lapdata_to_xy.md)
1. 準備好**賽道數據產生工具**的excel
1. 點連結啟動賽道xy座標工具
1. 輸出xy座標excel
## 分析與校正
### [賽道分析工具](introduction/track_characterization.md)
1. 準備好**賽道數據產生工具**的excel
1. 啟動工具執行繪製分析圖
1. 開始解讀圖表
### [GPS 校正](introduction/GPS.md)
透過地圖與實際尺寸符合，我們會透過收集實際GPS資料進行地圖校正
## 現成資料
* output ACC : 之前產生FST的檔案包
* output lapsim : 之前製作的賽道
