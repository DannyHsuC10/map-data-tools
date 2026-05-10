import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 讀取
file = "fsae_A_2025_track.xlsx"
df = pd.read_excel(file)

#print(df.head())

ds = 0.5
g = 9.81
a = 1.6*g


# 計算曲率
s_list = []
kappa_list = []

s_current = 0

Column_n= 50

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
# ==================================================================(曲率分布)
# 繪製曲率分佈圖
R = df["Radius"].dropna()

plt.figure()
plt.hist(R, bins=Column_n)
plt.xlabel("Radius (m)")
plt.ylabel("Count")
plt.title("Corner Radius Distribution")



# 繪製曲率分佈圖（長度加權）
R_weighted = []
L_tt = 0
for _, row in df.iterrows():

    if row["Type"] == "ARC":
        l = row["length"]
        L_tt+=l
        n = round(L)
        R_weighted += [row["Radius"]] * n
        
# === 長度加權的 histogram ===
counts, bin_edges = np.histogram(R_weighted, bins=Column_n)

# 排序（由大到小）前n名
n = 5
top_idx = np.argsort(counts)[-n:][::-1]

top_bins = []
print("長度權重排名========")
print("彎道總長度",L_tt)
for i in top_idx:
    r_min = bin_edges[i]
    r_max = bin_edges[i+1]
    weight = counts[i]
    r_mid = (r_max+r_min)/2
    #print(f"{r_min:.2f} ~ {r_max:.2f} m | weight = {weight}m")
    print(f"{r_mid:.2f} m | weight = {weight}m")
    top_bins.append((r_min, r_max))

plt.figure()

counts, bin_edges, patches = plt.hist(R_weighted, bins=Column_n)

# 標出前三名
for i in top_idx:
    patches[i].set_facecolor('red')

plt.xlabel("Radius (m)")
plt.ylabel("Arc Length Weight")
plt.title("Radius Distribution (Length Weighted)")
plt.show()

# 速度加權=============================================================
R_weighted = []
t_tt = 0
for _, row in df.iterrows():

    if row["Type"] == "ARC":
        r = row["Radius"]
        l = row["length"]
        v = (a*r)**0.5
        t = l/v
        t_tt+=t
        #print(t)
        R_weighted += [r] * round(t)

counts, bin_edges = np.histogram(R_weighted, bins=Column_n)

top_idx = np.argsort(counts)[-n:][::-1]

top_bins = []
print("時間權重排名========")
print("彎道時間",t_tt)
for i in top_idx:
    r_min = bin_edges[i]
    r_max = bin_edges[i+1]
    weight = counts[i]
    r_mid = (r_max+r_min)/2
    #print(f"{r_min:.2f} ~ {r_max:.2f} m | weight = {weight}s")
    print(f"{r_mid:.2f} m | weight = {weight}s")
    top_bins.append((r_min, r_max))

plt.figure()
counts, bin_edges, patches = plt.hist(R_weighted, bins=Column_n)

# 標出前三名
for i in top_idx:
    patches[i].set_facecolor('red')

plt.xlabel("Radius (m)")
plt.ylabel("Arc Length Weight (s)")
plt.title("Radius Distribution (time Weighted)")
plt.show()
# ==========================================================(頻譜特徵分析)
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
