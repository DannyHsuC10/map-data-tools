import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# 讀取 Excel
file_path = r"C:\Danny\2_project\ongoing\Track_Simulation\GPS\FST_GPS_xy.xlsx"
df_xy_in = pd.read_excel(file_path, sheet_name="Sheet1")
theta = -23.47101884

def rotate_point(P,theta_deg):# 旋轉點 P，角度 theta_deg
    theta = np.deg2rad(theta_deg)
    R = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])
    P_rotated = R @ P
    return P_rotated

def shift_point(P,shift_x,shift_y):# 平移點 P，平移量 shift_x, shift_y
    shift = np.array([shift_x, shift_y])
    P_shifted = P + shift
    return P_shifted

x_list_rotated, y_list_rotated = [], []
x_shift_list, y_shift_list = [], []

for index, row in df_xy_in.iterrows():
    x, y = row['x'], row['y']
    P = np.array([x,y])
    x_rot, y_rot = rotate_point(P, theta)
    P_rot = np.array([x_rot, y_rot])
    x_shifted, y_shifted = shift_point(P_rot,32.75562807, 0)
    
    x_list_rotated.append(x_rot)
    y_list_rotated.append(y_rot)
    x_shift_list.append(x_shifted)
    y_shift_list.append(y_shifted)
    
df_xy_rotated = pd.DataFrame({'x': x_list_rotated, 'y': y_list_rotated})
df_xy_shifted = pd.DataFrame({'x': x_shift_list, 'y': y_shift_list})
output_path_rotated = "FST_GPS_xy_rotated.xlsx"
output_path_shifted = "FST_GPS_xy_shifted.xlsx"
df_xy_rotated.to_excel(output_path_rotated, index=False)
df_xy_shifted.to_excel(output_path_shifted, index=False)

plt.figure(figsize=(8, 8))
plt.axis('equal')
plt.title('Track Geometry')
plt.xlabel('X')
plt.ylabel('Y')

plt.plot(df_xy_rotated['x'], df_xy_rotated['y'], marker='o')
plt.plot(df_xy_shifted['x'], df_xy_shifted['y'], marker='x')
# 顯示圖形
plt.grid(True)
plt.show()

# 顯示結果
print(df_xy_shifted)