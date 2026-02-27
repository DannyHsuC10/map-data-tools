# Map data tools
目前先製作了4個地圖資料處理工具，可以用於進行lapsim或方便製作車手有模擬器需要的ACC地圖。
## [角錐定位工具](/introduction/DXF_to_cone.md)
1. 先用繪圖軟體畫出角錐位置，用畫圓定位角椎座標(半徑隨便定都可以)
1. 下載成DXF
1. 點連結使用角錐定位工具
1. 產生所有角椎的xy座標csv檔，用excel就可以開啟檢查
## [ini產生器](/introduction/cone_to_ini.md)
1. 準備好**角錐定位工具**產生的csv
1. 點連結使用ini產生器
1. 產生ini
1. 放到ACC需要的資料夾使用
## [賽道數據產生工具](/introduction/DXF_to_lapdata.md)
1. 用繪圖軟體用直線、圓弧畫出賽道輪廓(如果要輔助的線條記得轉建構線條)
1. 下載成DXF
1. 點連結啟動賽道數據產生工具
1. 設定好起跑點與賽道方向
1. 生成excel賽道數據
## [賽道xy座標工具](/introduction/lapdata_to_xy.md)
1. 準備好**賽道數據產生工具**的excel
1. 點連結啟動賽道xy座標工具
1. 輸出xy座標excel
## 現成資料
* output ACC : 之前產生FST的檔案包
* output lapsim : 之前製作的賽道
