import csv
from pathlib import Path

# 檔案設定
CSV_NAME = "circle_centers.csv"# CSV檔案名稱，需與程式同資料夾
INI_NAME = "output.ini"        # 輸出INI檔案名稱，將會在程式同資料夾生成
n_set = 0        # 模型編號
y_set = -0.419   # 物件高度 (Y軸)
name_set = "AC_POBJECT_999_3" # 專案名稱
MODEL_FILE = "cone.kn5"
MODEL_ROTATION = (0, 0, 0)
MODEL_PHYSICAL = True


def write_cone_ini(filename, points, *, model_offset=n_set, height=y_set, name=name_set,
                   model_file=MODEL_FILE, rotation=MODEL_ROTATION, physical=MODEL_PHYSICAL):
    rotation_value = ", ".join(f"{angle:.15g}" for angle in rotation)
    with open(filename, "w", encoding="utf-8") as ini_file:
        for index, (x, y) in enumerate(points, start=1 + model_offset):
            ini_file.write(f"[MODEL_{index}]\n")
            ini_file.write(f"FILE={model_file}\n")
            ini_file.write(f"NAME={name}\n")
            ini_file.write(f"POSITION={-x}, {height}, {y}\n")
            ini_file.write(f"ROTATION={rotation_value}\n")
            ini_file.write(f"PHYSICAL={int(physical)}\n\n")


def main():
    directory = Path(__file__).resolve().parent
    with (directory / CSV_NAME).open(encoding="utf-8-sig", newline="") as stream:
        centers = [(float(row["X"]), float(row["Y"])) for row in csv.DictReader(stream)]
    write_cone_ini(directory / INI_NAME, centers)
    print(f"已將 CSV 轉換成 {INI_NAME}")


if __name__ == "__main__":
    main()
