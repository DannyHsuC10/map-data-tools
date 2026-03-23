# 經緯度轉換為平面座標 (XY)
* [GPS轉換工具](../GPS/GPS_to_xy.py)
* [後處理](../GPS/R.py)

地球表面是球面，經緯度 ($\lambda$, $\phi$) 雖然能精確描述位置，但在地圖繪製或計算距離時，常需要將其轉換為平面座標系統 ($x$, $y$)。

## 常見投影方法
### 1. 墨卡托投影 (Mercator Projection)
墨卡托投影常用於航海地圖，公式如下：

$$
x = R \cdot \lambda
$$

$$
y = R \cdot \ln \left( \tan \left( \frac{\pi}{4} + \frac{\phi}{2} \right) \right)
$$

其中：
- $R$：地球半徑
- $\lambda$：經度 (以弧度表示)
- $\phi$：緯度 (以弧度表示)

### 2. 高斯-克呂格投影 (Transverse Mercator)
常用於國家座標系統。基本公式為：

$$
x = k_0 \cdot N \cdot \left( A + \frac{(1 - T + C)}{6} A^3 + \frac{(5 - 18T + T^2 + 72C - 58e'^2)}{120} A^5 \right)
$$

$$
y = k_0 \cdot \left( M + N \cdot \tan(\phi) \cdot \left( \frac{A^2}{2} + \frac{(5 - T + 9C + 4C^2)}{24} A^4 + \frac{(61 - 58T + T^2 + 600C - 330e'^2)}{720} A^6 \right) \right)
$$

其中：
- $k_0$：投影比例因子
- $N = \frac{a}{\sqrt{1 - e^2 \sin^2(\phi)}}$
- $T = \tan^2(\phi)$
- $C = \frac{e'^2 \cos^2(\phi)}{1 - e^2}$
- $A = (\lambda - \lambda_0) \cos(\phi)$
- $M$：子午線弧長
- $a$：地球長半軸
- $e$：離心率
- $e'$：第二離心率
- $\lambda_0$：中央經線

## 投影後處理
投影後的結果可能與我們想要的位置不同，所以必須進行後處理，第一步先進行旋轉。
$$\theta = \frac{\vec v_1\cdot\vec v_2}{|v_1||v_2|}$$

$$\begin{bmatrix} y'\\
x'
\end{bmatrix} 
= 
\begin{bmatrix} y\\
x
\end{bmatrix} 

\begin{bmatrix}
\cos\theta & -\sin\theta \\
\sin\theta & \cos\theta 
\end{bmatrix}$$

然後進行平移
$$\begin{bmatrix} y\\
x
\end{bmatrix} = 
\begin{bmatrix} y+dy\\
x+dx
\end{bmatrix} 
$$

最後進行縮放
$$\begin{bmatrix} y\\
x
\end{bmatrix} = 
n\begin{bmatrix} y\\
x
\end{bmatrix} 
$$