# DXF 賽道路徑解析與幾何重建工具
* [工具位置](../DXF_to_lapdata.py)
## 簡介
本工具用於將 **DXF 賽道檔案（LINE / ARC）** 解析為連續軌跡段，並完成：

* 幾何排序
* 方向判定
* 起點重定義
* 視覺化驗證
* 弧長 / 線長計算
* 匯出完整 Excel 幾何資料

### 功能總覽

流程圖：

```text
DXF 讀取
   ↓
LINE / ARC 擷取
   ↓
路徑連續排序
   ↓
方向判定
   ↓
起點重定義
   ↓
幾何驗證視覺化
   ↓
Excel 幾何輸出
```

### 支援圖元類型

| DXF Entity | 支援 | 說明  |
| ---------- | -- | --- |
| LINE       | ✔  | 直線段 |
| ARC        | ✔  | 圓弧段 |


## 核心模組說明

### 1️⃣ DXF 讀取與預覽

```python
run_all_read_DXF(DXF_filename, excel_filename)
```

流程包含：

* 檢查檔案存在
* 讀取 modelspace
* 統計 LINE / ARC 數量
* matplotlib 預覽原始圖形

---

### 2️⃣ PathSegment 幾何資料結構

每段包含：

* type (LINE / ARC)
* start (x, y)
* end (x, y)
* center (ARC)
* radius (ARC)
* start_angle / end_angle
* mid_angle（用於方向判定）

---

### 3️⃣ 路徑排序邏輯

排序目標：將 DXF 中不按順序的線段與圓弧重組成**連續閉合軌跡**。

1. **容差判斷**

   兩點是否相連使用歐式距離（Pythagoras theorem）：

   $$d = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2} < \text{tol}$$

   `tol` 預設為 $1\times10^{-8}$。

2. **方向反轉**

   若上一段終點匹配當前段終點，則需反轉：

   * `start` ↔ `end`
   * ARC：`start_angle` ↔ `end_angle`

3. **排序演算法**

   1. 隨機選擇第一段作為初始段。
   2. 記錄上一段終點 $P_{\text{last}}$。
   3. 從剩餘段中找到 **起點或終點距離 $P_{\text{last}}$ < tol** 的段。
   4. 若匹配的是終點，先反轉方向。
   5. 將該段加入已排序清單，從未排序清單中移除。
   6. 重複直到清單為空。

   若無匹配段：

   $$\text{"The track is not continuous!!!"}$$

   代表 DXF 存在斷裂或孤立段。


### 4️⃣ 圓弧方向判定（Clockwise / Counterclockwise）

1. 計算中點角 `mid_angle`：

$$
\theta_{\text{mid}} = \frac{\theta_{\text{start}} + \theta_{\text{end}}}{2}$$

* 處理跨越 360° 的情況：

$$
\text{if } \theta_{\text{end}} < \theta_{\text{start}},\quad \theta_{\text{mid}} = \frac{\theta_{\text{start}} + \theta_{\text{end}} + 2\pi}{2}
$$

2. 判斷方向：

* **Clockwise**：中點角在起始與結束角外
* **Counterclockwise**：中點角在起始與結束角內

3. 計算弧長：

$$L = R \cdot \Delta \theta$$

* Clockwise:

$$
\Delta \theta = | \theta_{\text{start}} - \theta_{\text{end}} | \mod 2\pi$$

* Counterclockwise:

$$
\Delta \theta = | \theta_{\text{end}} - \theta_{\text{start}} | \mod 2\pi
$$

### 5️⃣ 起點重定義

```python
rotate_segments(sorted_segments, start)
```

* 將閉合軌跡從使用者指定段開始
* 重新生成新的段落順序
* 保證車輛模擬從正確起點開始

### 6️⃣ 整體方向重設

```python
reset_direction()
```

* 反轉 segment 順序
* start ↔ end
* ARC 角度修正
* 保證整體軌跡順時針 / 逆時針一致

### 7️⃣ 視覺化驗證

* **matplotlib**：檢查排序後連續性與起點標記
* **turtle**：等比例動態路徑模擬，檢查方向正確性

### 8️⃣ Excel 輸出

| Sheet           | 內容                         |
| --------------- | -------------------------- |
| Trackdata       | 完整段落資料 (起點、終點、中心、半徑、弧長、方向) |
| GeometrySummary | 精簡幾何摘要 (段落長度、方向)           |

---

## 數學處理重點

### 直線段長度

$$
L = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}
$$

### 圓弧段長度
$$
L = R \cdot \theta
$$

* 方向正確性影響 $\theta$ 計算
* $\theta$ 單位為弧度

### 方向判定

* 使用 `mid_angle` 判斷 Clockwise / Counterclockwise
* 處理角度跨越 360° 的特殊情況


## 使用範例

```python
DXF_filename = "fsae_A_2025_track.dxf"
excel_filename = "fsae_A_2025_track.xlsx"

run_all_read_DXF(DXF_filename, excel_filename)
```

互動步驟：

1. 預覽 DXF
2. 重新排序標號
3. 輸入起點段號
4. 選擇是否重設方向
5. 產生 Excel 幾何資料
