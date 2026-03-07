import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 讀取
file = "fsae_A_2025_track.xlsx"
df = pd.read_excel(file)

print(df.head())

ds = 0.5  # 每 0.5 m 取樣

# 計算曲率
s_list = []
kappa_list = []

s_current = 0

for _, row in df.iterrows():

    L = row["length"]

    # 曲率
    if row["Type"] == "LINE" or pd.isna(row["Radius"]):
        kappa = 0

    else:
        R = row["Radius"]

        if row["Direction"] == "Clockwise":
            kappa = -1 / R
        else:
            kappa = 1 / R

    n = int(L / ds)

    for i in range(n):
        s_list.append(s_current)
        kappa_list.append(kappa)
        s_current += ds

s = np.array(s_list)
kappa = np.array(kappa_list)

# 繪製曲率圖
plt.figure()
plt.plot(s, kappa)
plt.xlabel("Distance (m)")
plt.ylabel("Curvature (1/m)")
plt.title("Track Curvature")
plt.show()

# 繪製曲率分佈圖
R = df["Radius"].dropna()

plt.figure()
plt.hist(R, bins=30)
plt.xlabel("Radius (m)")
plt.ylabel("Count")
plt.title("Corner Radius Distribution")
plt.show()

# 繪製曲率分佈圖（長度加權）
R_weighted = []

for _, row in df.iterrows():

    if row["Type"] == "ARC":
        n = int(row["length"] / ds)
        R_weighted += [row["Radius"]] * n

plt.figure()
plt.hist(R_weighted, bins=40)
plt.xlabel("Radius (m)")
plt.ylabel("Arc Length Weight")
plt.title("Radius Distribution (Length Weighted)")
plt.show()

# 進行 FFT 分析
N = len(kappa)

fft_val = np.fft.fft(kappa)
freq = np.fft.fftfreq(N, d=ds)

amp = np.abs(fft_val)

mask = freq > 0

freq = freq[mask]
amp = amp[mask]

# 繪製頻譜圖
plt.figure()
plt.plot(freq, amp)
plt.xlabel("Spatial Frequency (1/m)")
plt.ylabel("Amplitude")
plt.title("Curvature Spectrum (FFT)")
plt.show()

# 繪製波長圖
wavelength = 1 / freq

plt.figure()
plt.plot(wavelength, amp)
plt.xscale("log")
plt.xlabel("Spatial Wavelength (m)")
plt.ylabel("Amplitude")
plt.title("Track Curvature Spectrum")
plt.show()