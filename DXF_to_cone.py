import ezdxf
import csv
import os
import matplotlib.pyplot as plt
## 檔案名稱設定
DXF_NAME = "FST_cone.dxf"
CSV_NAME = "circle_centers.csv"

# 取得目前程式所在的資料夾路徑
current_dir = os.path.dirname(os.path.abspath(__file__))

# 讀取 DXF 檔案
dxf_path = os.path.join(current_dir, DXF_NAME)
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# 建立一個清單存放圓心座標
circle_centers = []

# 遍歷所有圖元，找出圓形
for entity in msp.query("CIRCLE"):
    center = entity.dxf.center  # 取得圓心座標 (x, y)
    circle_centers.append([center.x, center.y, center.z])

csv_path = os.path.join(current_dir, CSV_NAME)
# 將圓心座標寫入 CSV
with open(csv_path, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["X", "Y", "Z"])  # 標題列
    writer.writerows(circle_centers)

print("已將所有圓心座標輸出到 FST_cone.csv")

# -------- 新增繪圖部分 --------
# 取出 X, Y 座標
x_coords = [pt[0] for pt in circle_centers]
y_coords = [pt[1] for pt in circle_centers]

plt.figure(figsize=(6, 6))
plt.scatter(x_coords, y_coords, c="blue", marker="o")
plt.title("Circle Centers XY Plot")
plt.xlabel("X")
plt.ylabel("Y")
plt.axis("equal")  # 保持比例一致
plt.grid(True)
plt.show()
