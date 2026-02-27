# 賽道角椎 DXF 轉 XY座標

* [工具位置](../DXF_to_cone.py)

## 簡介

### 功能說明

此工具會：

1. 讀取指定 DXF 檔案
2. 搜尋所有 `CIRCLE` 圖元
3. 取得每個圓的圓心座標 (X, Y, Z)
4. 將資料輸出為 CSV 檔案
5. 自動繪製 XY 平面散佈圖供檢查

### 使用套件

* `ezdxf` — 讀取 DXF 檔案
* `csv` — 寫入 CSV 檔案
* `matplotlib` — 繪製平面圖
* `os` — 路徑管理


## 使用方式

將 DXF 檔案與 Python 腳本放在同一資料夾。

程式預設檔名：

```python
DXF_NAME = "FST_cone.dxf"
CSV_NAME = "FST_cone.csv"
```

執行：

```bash
python DXF_to_cone.py
```

執行後會產生：

```
FST_cone.csv
```

並彈出 XY 平面散佈圖。


## 輸出格式

CSV 檔案格式：

```
X, Y, Z
x1, y1, z1
x2, y2, z2
...
```

其中：

* X = 圓心 X 座標
* Y = 圓心 Y 座標
* Z = 圓心 Z 座標（通常為 0）
