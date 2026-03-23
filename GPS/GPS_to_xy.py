#GPS to xy
import pandas as pd
from pyproj import Transformer
import matplotlib.pyplot as plt
# 建立轉換器：WGS84 Web Mercator
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

# 讀取 Excel
file_path = r"C:\Danny\2_project\ongoing\Track_Simulation\GPS\GPS_filtered_latlon.xlsx"
df_FST = pd.read_excel(file_path, sheet_name="Sheet1")

def convert_coords(df):
    x_list, y_list = [], []
    for index, row in df.iterrows():
        Latitude, Longitude = row['Latitude_deg'], row['Longitude_deg']
        print("Latitude:", Latitude, "Longitude:", Longitude)
        x, y = transformer.transform(Longitude,Latitude)
        print("x:", x, "y:", y)
        x_list.append(x)
        y_list.append(y)

    x0, y0 = x_list[0], y_list[0]
    x_rel = [x - x0 for x in x_list]
    y_rel = [y - y0 for y in y_list]

    df_xy = pd.DataFrame({'x': x_rel, 'y': y_rel})
    return df_xy


# 套用轉換
df_result = convert_coords(df_FST)
# 顯示結果


output_path = "FSA_GPS.xlsx"
df_result.to_excel(output_path, index=False)

# 建立圖形
plt.figure(figsize=(8, 8))
plt.axis('equal')
plt.title('Track Geometry')
plt.xlabel('X')
plt.ylabel('Y')

plt.plot(df_result['x'], df_result['y'], marker='o')
# 顯示圖形
plt.grid(True)
plt.show()