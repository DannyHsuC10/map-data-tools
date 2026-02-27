import csv
import os

# 檔案設定
CSV_NAME = "circle_centers.csv"# CSV檔案名稱，需與程式同資料夾
INI_NAME = "output.ini"        # 輸出INI檔案名稱，將會在程式同資料夾生成
n_set = 0        # 模型編號
y_set = -0.419   # 物件高度 (Y軸)
name_set = "AC_POBJECT_999_3" # 專案名稱

# 取得目前程式所在的資料夾路徑
current_dir = os.path.dirname(os.path.abspath(__file__))

# 使用相對路徑讀取同資料夾中的 CSV 檔案
csv_path = os.path.join(current_dir, CSV_NAME)
ini_path = os.path.join(current_dir, INI_NAME)

with open(csv_path, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    rows = list(reader)

with open(ini_path, "w") as ini_file:
    for idx, row in enumerate(rows, start=1):
        # 讀取 CSV 的 X 與 Y
        x = float(row["X"])
        y = float(row["Y"])
        # Z 可以忽略或保留，這裡用 Y 當 z
        ini_file.write(f"[MODEL_{idx+n_set}]\n")
        ini_file.write("FILE=cone.kn5\n")
        ini_file.write(f"NAME={name_set}\n")
        ini_file.write(f"POSITION={-x}, {y_set}, {y}\n")
        ini_file.write("ROTATION=0, 0, 0\n")
        ini_file.write("PHYSICAL=1\n\n")

print("已將 CSV 轉換成 output.ini")