import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 設定檔案資料
file_path = "fsae_A_2025_track.xlsx"
output_path = "fsae_A_2025_track_xy.xlsx"
df = pd.read_excel(file_path)

list_x, list_y, list_p = [], [], []

# 逐列處理，依照表單順序
for index, row in df.iterrows():
    if row['Type'] == 'LINE':
        x1, y1 = row['Start_X'], row['Start_Y']
        x2, y2 = row['End_X'], row['End_Y']
        list_x.append(x1)
        list_y.append(y1)
        list_p.append(len(list_x))
        list_x.append(x2)
        list_y.append(y2)
        list_p.append(len(list_x))
        print(f"LINE segment {index}:")
        print(f"  Point 1: X = {x1:.3f}, Y = {y1:.3f}")
        print(f"  Point 2: X = {x2:.3f}, Y = {y2:.3f}")

    elif row['Type'] == 'ARC':
        cx, cy = row['Center_X'], row['Center_Y']
        r = row['Radius']
        start_deg = row['Start_Angle (deg)'] % 360
        end_deg = row['End_Angle (deg)'] % 360

        delta = (end_deg - start_deg) % 360
        if row['Direction'] == 'Counterclockwise':
            direction = 'Counterclockwise'
            angles_deg = np.linspace(start_deg, start_deg + delta, 5) % 360
        else:
            direction = 'Clockwise'
            angles_deg = np.linspace(start_deg, start_deg - (360 - delta), 5) % 360

        angles_rad = np.deg2rad(angles_deg)

        print(f"ARC segment {index}: Direction = {direction}")
        for i, theta in enumerate(angles_rad):
            x = cx + r * np.cos(theta)
            y = cy + r * np.sin(theta)
            list_x.append(x)
            list_y.append(y)
            list_p.append(len(list_x))
            print(f"  Point {i+1}: X = {x:.3f}, Y = {y:.3f}")

# 將結果存成 DataFrame
df_result = pd.DataFrame({'Point': list_p, 'X': list_x, 'Y': list_y})

# 儲存成新的 Excel 檔案

df_result.to_excel(output_path, index=False)
print(f"Coordinates saved to {output_path}")

#==============================================
# 建立圖形
plt.figure(figsize=(8, 8))
plt.axis('equal')
plt.title('Track Geometry')
plt.xlabel('X')
plt.ylabel('Y')

# 處理每一列
for index, row in df.iterrows():
    if row['Type'] == 'LINE':
        x1, y1 = row['Start_X'], row['Start_Y']
        x2, y2 = row['End_X'], row['End_Y']
        plt.plot([x1, x2], [y1, y2], 'b-')  # 藍色線段
        plt.scatter([x1, x2], [y1, y2], color='blue', s=10)
        
    elif row['Type'] == 'ARC':
        cx, cy = row['Center_X'], row['Center_Y']
        r = row['Radius']
        start_deg = row['Start_Angle (deg)'] % 360
        end_deg = row['End_Angle (deg)'] % 360

        delta = (end_deg - start_deg) % 360
        if delta == 0:
            direction = 'Full Circle'
            angles_deg = np.linspace(0, 360, 100)
        elif row['Direction'] == 'Counterclockwise':
            direction = 'Counterclockwise'
            angles_deg = np.linspace(start_deg, start_deg + delta, 100) % 360
        else:
            direction = 'Clockwise'
            angles_deg = np.linspace(start_deg, start_deg - (360 - delta), 100) % 360
            angles_deg = angles_deg[::-1]

        angles_rad = np.deg2rad(angles_deg)
        arc_x = cx + r * np.cos(angles_rad)
        arc_y = cy + r * np.sin(angles_rad)

        plt.plot(arc_x, arc_y, 'r-')  # 紅色弧線
        plt.scatter(arc_x[::25], arc_y[::25], color='red', s=10)  # 每隔幾點標示節點

# 顯示圖形
plt.grid(True)
plt.show()