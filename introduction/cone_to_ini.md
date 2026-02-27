# 賽道角椎 CSV → INI 生成工具

* [工具位置](../cone_to_ini.py)
## 簡介
此工具會：

1. 讀取 `circle_centers.csv`
2. 解析每筆 X、Y 座標
3. 依指定規則轉換座標系
4. 生成 `output.ini`

### 可調整參數

```python
CSV_NAME = "circle_centers.csv"## CSV檔案名稱，需與程式同資料夾
INI_NAME = "output.ini"        ## 輸出INI檔案名稱，將會在程式同資料夾生成
n_set = 0        ## 模型編號
y_set = -0.419   ## 物件高度 (Y軸)
name_set = "AC_POBJECT_999_3" ## 專案名稱
```

### 座標轉換邏輯

CSV：

```
X, Y
```

轉換為：

```
POSITION = -X, y_set, Y
```

## 使用方式

將 CSV 與腳本放在同一資料夾：

```bash
python your_script.py
```

輸出：

```
output.ini
```

### 輸入 CSV 格式

```csv
X,Y,Z
1.25,3.80,0
2.10,4.15,0
...
```

實際使用欄位：

* X
* Y

Z 欄位可存在但不使用。
***
### 生成的 INI 格式

範例輸出：

```ini
[MODEL_1]
FILE=cone.kn5
NAME=AC_POBJECT_999_3
POSITION=-1.25, -0.419, 3.80
ROTATION=0, 0, 0
PHYSICAL=1
```

每個角椎對應一個 `[MODEL_xxx]` 區段。

## 建議完整自動化流程

```
DXF
 ↓
(DXF 轉 CSV 工具)
 ↓
circle_centers.csv
 ↓
(CSV 轉 INI 工具)
 ↓
output.ini
 ↓
匯入模擬器
```
