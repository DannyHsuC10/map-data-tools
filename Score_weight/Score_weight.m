%% 分數權重計算工具
clc; clear; close all;
addpath('data');
load_data('data.csv');

track_score = Autocross + Endurance;

%% ===== 賽道區段定義(這邊很重要改資料來這邊) =====
% s: 對應分數權重 (距離比例)
% r: 半徑

segments = [
    struct('name','R1','s',27*track_score/lap_t,'r',6.17)
    struct('name','R2','s',26*track_score/lap_t,'r',3.26)
    struct('name','R3','s',9*track_score/lap_t,'r',14.88)
    struct('name','R4','s',5*track_score/lap_t,'r',9.07)
    struct('name','R5','s',5*track_score/lap_t,'r',11.97)
    struct('name','Skidpad','s',Skidpad,'r',Skidpad_r)
];


%% ===== 計算 =====

N = length(segments);

score_list = zeros(N,1);

for i = 1:N
    score_list(i) = segments(i).s;
end

%% ===== 顯示 =====

fprintf('\n=== 分數占分 ===\n');
for i = 1:N
    fprintf('%s(%.2f): %.2f \n', segments(i).name,segments(i).r, score_list(i));
end

%% ===== 視覺化 =====
figure;
bar(score_list);
title('Score Rate');
xticklabels({segments.name});
ylabel('score');

