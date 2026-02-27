# FSAE Track XY 展開與繪圖工具
* [工具位置](../lapdata_to_xy.py)
## 簡介
此工具將賽道 Excel 幾何檔案 (`fsae_A_2025_track.xlsx`) 中的 **LINE / ARC 段落**轉換為 **離散 XY 座標點**，方便進行：

### 功能概覽

1. 讀取 Excel 賽道幾何表格
2. 將每個 LINE / ARC 轉換為一組 XY 點
3. 記錄節點編號
4. 儲存為新的 Excel (`fsae_A_2025_track_xy.xlsx`)
5. 使用 Matplotlib 畫出賽道圖形

   * LINE: 藍線
   * ARC: 紅線
   * 節點以散點標示

## 主要數學邏輯

### 1️⃣ 直線段

對每個 LINE 段落，生成兩個端點：

$$
\text{Point}_1 = (x_1, y_1),\quad \text{Point}_2 = (x_2, y_2)
$$

並將端點加入結果列表。
線段長度可計算為：

$$
L = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}
$$


### 2️⃣ 圓弧段

對 ARC 段落，使用中心、半徑與起訖角生成多個離散點。

#### 計算步驟

1. **角度轉換**：

$$\text{start deg} = \text{Start Angle} \mod 360$$

$$\text{end deg} = \text{End Angle} \mod 360$$

2. **角度差計算**：

$$\delta = (\text{end deg} - \text{start deg}) \mod 360$$

3. **方向判定**：

* Counterclockwise (逆時針): 生成角度 `start_deg → start_deg + delta`
* Clockwise (順時針): 生成角度 `start_deg → start_deg - (360 - delta)`

4. **離散點生成**：

將角度轉為弧度：

$$
\theta = \text{deg2rad}(angles_deg)
$$

計算每個點坐標：

$$
x = cx + r \cos(\theta), \quad y = cy + r \sin(\theta)
$$

### 3️⃣ 節點編號

每個生成點都會對應一個 `Point` 編號，方便後續資料對照與模擬使用。

## Excel 輸出

* **檔名**: `fsae_A_2025_track_xy.xlsx`
* **欄位**:

| Point | X   | Y   |
| ----- | --- | --- |
| 1     | 0.0 | 0.0 |
| 2     | 1.2 | 0.0 |
| ...   | ... | ... |

可直接用於：

* MATLAB / Python 模擬
* 車輛軌跡分析
* Lap Time 計算


## 視覺化

* **LINE**: 藍線 + 藍色端點
* **ARC**: 紅線 + 紅色離散點(5個)
* 每隔若干點用散點標示，便於檢查節點對齊

示例圖：

```
  Y
  ^
  |
  |      ARC segment
  |   o o o o o
  |  
  |          
  | LINE segment
  | o---------o
  +----------------> X
```


## 使用範例

```python
# 設定檔案資料
file_path = "fsae_A_2025_track.xlsx"
output_path = "fsae_A_2025_track_xy.xlsx"
```