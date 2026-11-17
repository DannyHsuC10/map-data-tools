import math
import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ezdxf import DXFError
from matplotlib import patheffects
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from DXF_to_lapdata import arc_sweep
from cone_to_ini import MODEL_FILE, MODEL_PHYSICAL, MODEL_ROTATION, n_set, name_set, y_set
from lapdata_to_xy import DEFAULT_XY_POINTS, DEFAULT_XY_SPACING, sample_arc
from track_pipeline import (
    analyze_track, circle_centers, export_circle_centers, export_track, order_from_start,
    prepare_route, read_dxf,
)


ALL_LAYERS = "（所有圖層）"
BACKGROUND = "#edf2f6"
INK = "#182a3a"
MUTED = "#4d6579"
ACCENT = "#087780"
STEPS = (
    ("原始排序", "先查看 DXF 依端點接起來的原始順序。", "下一步：選擇起點"),
    ("選擇起點", "點選圖上的接點，或輸入該接點的原始編號。", "確認起點並重新排序"),
    ("重新排序與方向", "確認新起點已編為 1，再選擇行駛方向。", "確認方向"),
    ("確認輸出", "核對順序、比例與加速度，再完成並檢視分析。", "完成並檢視分析"),
)
EXPORT_BUTTONS = (
    ("excel", "匯出 Excel"),
    ("csv", "匯出 CSV"),
    ("ini", "匯出 INI"),
    ("analysis", "儲存分析圖"),
)
XY_BY_DISTANCE = "每 N 公尺取一點"
XY_BY_SEGMENT = "每段取 N 點"


def segment_coordinates(seg):
    if seg.type == "LINE":
        return (seg.start[0], seg.end[0]), (seg.start[1], seg.end[1])
    return sample_arc(seg.center, seg.radius, seg.start_angle, arc_sweep(seg), 60)


class TrackApp:
    def __init__(self, root):
        self.root = root
        self.path = None
        self.entities = []
        self.circles = []
        self.centers = []
        self.route = []
        self.step = 0
        self.applied_tolerance = None
        self.busy = False
        self.result_folder = None
        self.analysis_canvas = None
        self.ini_options = {
            "model_offset": n_set, "height": y_set, "name": name_set, "model_file": MODEL_FILE,
            "rotation": MODEL_ROTATION, "physical": MODEL_PHYSICAL,
        }

        root.title("賽道資料工具")
        root.geometry("1180x780")
        root.minsize(940, 700)
        root.configure(background=BACKGROUND)

        self.filename = tk.StringVar(value="尚未選取檔案")
        self.layer = tk.StringVar(value=ALL_LAYERS)
        self.circle_layer = tk.StringVar(value=ALL_LAYERS)
        self.scale = tk.StringVar(value="1")
        self.scale_source = tk.StringVar()
        self.tolerance = tk.StringVar(value="1e-8")
        self.lateral_g = tk.StringVar(value="1.6")
        self.xy_mode = tk.StringVar(value=XY_BY_DISTANCE)
        self.xy_spacing = tk.StringVar(value=f"{DEFAULT_XY_SPACING:g}")
        self.xy_points = tk.StringVar(value=str(DEFAULT_XY_POINTS))
        self.start = tk.StringVar()
        self.direction = tk.StringVar()
        self.step_title = tk.StringVar()
        self.step_help = tk.StringVar()
        self.preview_title = tk.StringVar()
        self.preview_help = tk.StringVar()
        self.status = tk.StringVar(value="請選取包含賽道路徑的 DXF。")
        self.circle_status = tk.StringVar(value="請選取以圓形標記位置的 DXF。")

        self.build()
        self.show_step(0)
        self.refresh_circle_centers()

    def build(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        self.root.option_add("*Font", ("Microsoft JhengHei UI", 10))
        style.configure("TFrame", background=BACKGROUND)
        style.configure("TLabel", background=BACKGROUND, foreground=INK)
        style.configure("Field.TLabel", background="white", foreground=INK, font=("Microsoft JhengHei UI", 10, "bold"))
        style.configure("Card.TFrame", background="white")
        style.configure("Hint.TLabel", background="white", foreground=MUTED)
        style.configure("Card.TRadiobutton", background="white", foreground=INK)
        style.configure("Step.TLabel", background="white", foreground=INK,
                        font=("Microsoft JhengHei UI", 13, "bold"))
        style.configure("Primary.TButton", background=ACCENT, foreground="white", padding=(12, 8))
        style.map("Primary.TButton", background=[("disabled", "#dce5e9"), ("active", "#09646d")],
                  foreground=[("disabled", MUTED), ("!disabled", "white")])
        style.configure("TNotebook.Tab", padding=(16, 7))

        header = tk.Frame(self.root, background="#172b3b", padx=22, pady=12)
        header.pack(fill="x")
        brand = tk.Frame(header, background="#172b3b")
        brand.pack(side="left")
        tk.Label(brand, text="賽道資料工具", background="#172b3b", foreground="white",
                 font=("Microsoft JhengHei UI", 19, "bold")).pack(anchor="w")
        tk.Label(brand, text="DXF 匯入、路徑預覽與賽道分析", background="#172b3b",
                 foreground="#cbe0e9").pack(anchor="w")
        self.file_button = ttk.Button(header, text="選取 DXF…", command=self.choose_file)
        self.file_button.pack(side="right")
        tk.Label(header, textvariable=self.filename, background="#172b3b", foreground="#cbe0e9",
                 width=30, anchor="e").pack(side="right", padx=(0, 10))

        body = ttk.Frame(self.root, padding=(16, 14))
        body.pack(fill="both", expand=True)
        sidebar = ttk.Frame(body, style="Card.TFrame", padding=14)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.columnconfigure(0, minsize=238, weight=1)
        panel = self.route_panel = ttk.Frame(sidebar, style="Card.TFrame")
        panel.grid(row=0, sticky="ew")
        panel.columnconfigure(0, minsize=238, weight=1)
        ttk.Label(panel, textvariable=self.step_title, style="Step.TLabel").grid(
            row=0, sticky="w", pady=(0, 6))
        ttk.Label(panel, textvariable=self.step_help, style="Hint.TLabel", wraplength=238).grid(
            row=1, sticky="w")
        self.pages = [ttk.Frame(panel, style="Card.TFrame") for _ in STEPS]
        for page in self.pages:
            page.columnconfigure(0, weight=1)
        original, start_page, direction_page, output = self.pages

        self.field_label(original, "賽道路徑圖層", 1)
        self.layer_combo = ttk.Combobox(original, textvariable=self.layer, state="readonly", width=22)
        self.layer_combo.grid(row=2, sticky="ew")
        self.layer_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_route())
        self.field_label(original, "端點容差（DXF 單位）", 3)
        tolerance_entry = ttk.Entry(original, textvariable=self.tolerance, width=12)
        tolerance_entry.grid(row=4, sticky="ew")
        tolerance_entry.bind("<Return>", lambda _event: self.refresh_route())
        ttk.Button(original, text="套用容差", command=self.refresh_route).grid(
            row=5, sticky="ew", pady=(5, 0))

        self.field_label(start_page, "起點的原始編號", 0)
        self.start_box = ttk.Spinbox(start_page, from_=1, to=1, textvariable=self.start, width=8)
        self.start_box.grid(row=1, sticky="w")

        for row, (value, label) in enumerate((("forward", "保留原行駛方向"), ("reverse", "反轉行駛方向"))):
            ttk.Radiobutton(direction_page, text=label, value=value, variable=self.direction,
                            style="Card.TRadiobutton").grid(row=row, sticky="w", pady=3)

        self.field_label(output, "每 DXF 單位的公尺數", 0)
        scale_entry = ttk.Entry(output, textvariable=self.scale)
        scale_entry.grid(row=1, sticky="ew")
        ttk.Label(output, textvariable=self.scale_source, style="Hint.TLabel", wraplength=238).grid(
            row=2, sticky="w", pady=(3, 0))
        self.field_label(output, "分析用橫向加速度（g）", 3)
        lateral_entry = ttk.Entry(output, textvariable=self.lateral_g)
        lateral_entry.grid(row=4, sticky="ew")
        self.analysis_inputs = (scale_entry, lateral_entry)
        downloads = self.downloads = ttk.Frame(output, style="Card.TFrame")
        downloads.grid(row=5, sticky="ew")
        downloads.columnconfigure(0, weight=1)
        self.field_label(downloads, "XY 取樣方式", 0)
        xy_mode_box = ttk.Combobox(downloads, textvariable=self.xy_mode,
                                   values=(XY_BY_DISTANCE, XY_BY_SEGMENT), state="readonly", width=20)
        xy_mode_box.grid(row=1, sticky="ew")
        self.xy_value_label = ttk.Label(downloads, style="Field.TLabel")
        self.xy_value_label.grid(row=2, sticky="w", pady=(9, 2))
        self.xy_value = ttk.Entry(downloads)
        self.xy_value.grid(row=3, sticky="ew")
        self.update_xy_mode()
        self.xy_mode.trace_add("write", self.update_xy_mode)
        self.ini_button = ttk.Button(downloads, text="INI 設定…", command=self.edit_ini_options)
        self.ini_button.grid(row=4, sticky="ew", pady=(10, 0))

        actions = ttk.Frame(downloads, style="Card.TFrame")
        actions.grid(row=5, sticky="ew", pady=(8, 0))
        actions.columnconfigure((0, 1), weight=1, uniform="export")
        self.export_buttons = {}
        for index, (export_format, label) in enumerate(EXPORT_BUTTONS):
            row, column = divmod(index, 2)
            button = ttk.Button(actions, text=label, style="Primary.TButton",
                                command=lambda selected=export_format: self.start_export(selected))
            button.grid(row=row, column=column, sticky="ew", padx=(0, 4) if column == 0 else (4, 0),
                        pady=(0 if row == 0 else 5, 0))
            self.export_buttons[export_format] = button

        self.next_button = ttk.Button(panel, style="Primary.TButton", command=self.advance)
        self.next_button.grid(row=4, sticky="ew", pady=(12, 5))
        self.back_button = ttk.Button(panel, text="上一步", command=self.go_back)
        self.back_button.grid(row=5, sticky="ew")
        self.build_circle_panel(sidebar)
        self.open_button = ttk.Button(sidebar, text="開啟上次儲存位置", command=self.open_output, state="disabled")
        self.open_button.grid(row=1, sticky="ew", pady=(5, 0))

        self.tabs = ttk.Notebook(body)
        self.tabs.pack(side="left", fill="both", expand=True)
        preview = ttk.Frame(self.tabs, style="Card.TFrame", padding=8)
        self.tabs.add(preview, text="路徑預覽")
        self.analysis_tab = ttk.Frame(self.tabs, style="Card.TFrame", padding=8)
        self.tabs.add(self.analysis_tab, text="賽道分析", state="disabled")
        ttk.Label(preview, textvariable=self.preview_title, style="Step.TLabel").pack(
            anchor="w", padx=10, pady=(5, 2))
        ttk.Label(preview, textvariable=self.preview_help, style="Hint.TLabel").pack(
            anchor="w", padx=10)
        self.preview_figure = Figure(figsize=(7, 5), layout="constrained")
        self.preview_ax = self.preview_figure.add_subplot()
        self.preview_canvas = FigureCanvasTkAgg(self.preview_figure, master=preview)
        self.preview_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self.toolbar = NavigationToolbar2Tk(self.preview_canvas, preview, pack_toolbar=False)
        self.toolbar.pack(side="bottom", fill="x")
        self.preview_canvas.mpl_connect("button_press_event", self.pick_start)
        self.circle_tab = ttk.Frame(self.tabs, style="Card.TFrame", padding=8)
        self.tabs.add(self.circle_tab, text="圓心匯出")
        circle_figure = Figure(figsize=(7, 5), layout="constrained")
        self.circle_ax = circle_figure.add_subplot()
        self.circle_canvas = FigureCanvasTkAgg(circle_figure, master=self.circle_tab)
        self.circle_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        self.circle_toolbar = NavigationToolbar2Tk(self.circle_canvas, self.circle_tab, pack_toolbar=False)
        self.circle_toolbar.pack(side="bottom", fill="x")
        self.tabs.bind("<<NotebookTabChanged>>", self.change_tab)
        self.start.trace_add("write", self.change_start)
        self.direction.trace_add("write", self.change_direction)
        self.tolerance.trace_add("write", lambda *_: self.update_buttons())
        self.scale.trace_add("write", lambda *_: self.invalidate_result())
        self.lateral_g.trace_add("write", lambda *_: self.invalidate_result())
        self.status_label = ttk.Label(self.root, textvariable=self.status, wraplength=880, padding=(18, 0, 18, 12))
        self.status_label.pack(fill="x")

    def build_circle_panel(self, sidebar):
        panel = self.circle_panel = ttk.Frame(sidebar, style="Card.TFrame")
        panel.grid(row=0, sticky="ew")
        panel.grid_remove()
        panel.columnconfigure(0, weight=1)
        self.field_label(panel, "圓形圖層", 0)
        self.circle_layer_combo = ttk.Combobox(panel, textvariable=self.circle_layer, state="disabled", width=22)
        self.circle_layer_combo.grid(row=1, sticky="ew")
        self.circle_layer_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_circle_centers())
        self.field_label(panel, "每 DXF 單位的公尺數", 2)
        self.circle_scale_entry = ttk.Entry(panel, textvariable=self.scale)
        self.circle_scale_entry.grid(row=3, sticky="ew")
        ttk.Label(panel, textvariable=self.scale_source, style="Hint.TLabel", wraplength=238).grid(
            row=4, sticky="w", pady=(3, 0))
        self.circle_ini_button = ttk.Button(panel, text="INI 設定…", command=self.edit_ini_options)
        self.circle_ini_button.grid(row=5, sticky="ew", pady=(10, 0))
        actions = ttk.Frame(panel, style="Card.TFrame")
        actions.grid(row=6, sticky="ew", pady=(8, 0))
        actions.columnconfigure((0, 1), weight=1, uniform="export")
        self.circle_export_buttons = {}
        for column, export_format in enumerate(("csv", "ini")):
            button = ttk.Button(actions, text=f"匯出 {export_format.upper()}", style="Primary.TButton",
                                command=lambda selected=export_format: self.start_circle_export(selected))
            button.grid(row=0, column=column, sticky="ew", padx=(0, 4) if column == 0 else (4, 0))
            self.circle_export_buttons[export_format] = button

    def change_tab(self, _event):
        if self.tabs.select() == str(self.circle_tab):
            self.route_panel.grid_remove()
            self.circle_panel.grid()
            self.status_label.configure(textvariable=self.circle_status)
        else:
            self.circle_panel.grid_remove()
            self.route_panel.grid()
            self.status_label.configure(textvariable=self.status)

    @staticmethod
    def field_label(parent, text, row):
        ttk.Label(parent, text=text, style="Field.TLabel").grid(row=row, sticky="w", pady=(9, 2))

    def choose_file(self):
        selected = filedialog.askopenfilename(title="選取 DXF", filetypes=[("DXF", "*.dxf")], parent=self.root)
        if selected:
            self.load_file(Path(selected))

    def load_file(self, path):
        try:
            entities, layers, scale, source = read_dxf(path)
        except (DXFError, ValueError, OSError) as exc:
            messagebox.showerror("無法讀取 DXF", str(exc), parent=self.root)
            return
        was_circle_tab = self.tabs.select() == str(self.circle_tab)
        self.path, self.entities = path, entities
        self.circles = [entity for entity in entities if entity.dxftype() == "CIRCLE"]
        self.filename.set(path.name)
        self.scale.set(f"{scale:.12g}")
        self.scale_source.set(source)
        self.layer_combo.configure(values=(ALL_LAYERS, *layers))
        preferred = next((layer for layer in layers if layer.casefold() == "track"), None)
        self.layer.set(preferred or (layers[0] if len(layers) == 1 else ALL_LAYERS))
        circle_layers = sorted({circle.dxf.layer for circle in self.circles}, key=str.casefold)
        self.circle_layer_combo.configure(values=(ALL_LAYERS, *circle_layers))
        self.circle_layer.set(ALL_LAYERS)
        self.refresh_route()
        self.refresh_circle_centers()
        if self.circles and (was_circle_tab or not self.route):
            self.tabs.select(self.circle_tab)

    def refresh_circle_centers(self):
        layer = self.circle_layer.get()
        try:
            self.centers = circle_centers(self.circles, None if layer == ALL_LAYERS else layer)
        except ValueError as exc:
            self.centers = []
            hint = str(exc)
        else:
            if self.centers:
                hint = f"找到 {len(self.centers):,} 個圓心。可選取圖層並匯出 CSV 或 INI。"
            elif self.path is not None:
                hint = "所選圖層沒有圓形（CIRCLE）。"
            else:
                hint = "請選取以圓形標記位置的 DXF。"
        self.circle_status.set(hint)
        ax = self.circle_ax
        ax.clear()
        if self.centers:
            ax.set(aspect="equal", xlabel="X (DXF units)", ylabel="Y (DXF units)")
            ax.set_axisbelow(True)
            ax.grid(True, color="#e1e9ee", linewidth=0.7)
            ax.scatter(*zip(*self.centers), s=18, color=ACCENT)
        else:
            ax.set_axis_off()
        self.circle_toolbar.update()
        self.circle_canvas.draw_idle()
        self.update_buttons()

    def refresh_route(self):
        if not self.entities:
            return
        self.invalidate_result()
        layer = self.layer.get()
        self.applied_tolerance = self.tolerance.get()
        try:
            self.route = prepare_route(self.entities, None if layer == ALL_LAYERS else layer,
                                       self.number(self.tolerance, "端點容差"))
        except ValueError as exc:
            self.route = []
            self.status.set(str(exc))
        else:
            lines = sum(seg.type == "LINE" for seg in self.route)
            self.status.set(f"已讀取 {len(self.route)} 段閉合路徑 · {lines} 段直線 · {len(self.route) - lines} 段圓弧")
        self.start_box.configure(to=max(1, len(self.route)))
        self.show_step(0)
        self.start.set("")
        self.direction.set("")

    def show_step(self, step):
        self.pages[self.step].grid_remove()
        self.step = step
        self.pages[step].grid(row=3, sticky="ew", pady=(12, 0))
        title, help_text, next_label = STEPS[step]
        self.step_title.set(f"{step + 1} / {len(STEPS)}　{title}")
        self.step_help.set(help_text)
        self.next_button.configure(text=next_label)
        self.tabs.select(self.analysis_tab if step == 3 and self.analysis_canvas is not None else 0)
        if self.toolbar.mode:
            if self.toolbar.mode == "zoom rect":
                self.toolbar.zoom()
            else:
                self.toolbar.pan()
        self.toolbar.update()
        self.update_buttons()
        self.draw_route()

    def update_buttons(self):
        ready = bool(self.route) and self.tolerance.get() == self.applied_tolerance
        if self.step >= 1:
            ready = ready and self.start_index() is not None
        if self.step >= 2:
            ready = ready and self.direction.get() in ("forward", "reverse")
        can_download = self.step == 3 and self.analysis_canvas is not None
        if can_download:
            self.next_button.grid_remove()
            self.downloads.grid()
            self.step_help.set("分析已完成。選擇要儲存的格式，再選擇資料夾。")
        else:
            self.next_button.grid()
            self.downloads.grid_remove()
            if self.step == 3:
                self.step_help.set(STEPS[3][1])
        self.next_button.configure(state="normal" if ready and not self.busy and not can_download else "disabled")
        for field in self.analysis_inputs:
            field.configure(state="disabled" if self.busy else "normal")
        download_state = "normal" if can_download and ready and not self.busy else "disabled"
        for button in self.export_buttons.values():
            button.configure(state=download_state)
        self.ini_button.configure(state=download_state)
        self.back_button.configure(state="normal" if self.step > 0 and not self.busy else "disabled")
        self.file_button.configure(state="disabled" if self.busy else "normal")
        circle_state = "normal" if self.centers and not self.busy else "disabled"
        for button in self.circle_export_buttons.values():
            button.configure(state=circle_state)
        self.circle_ini_button.configure(state=circle_state)
        self.circle_layer_combo.configure(state="readonly" if self.circles and not self.busy else "disabled")
        self.circle_scale_entry.configure(state="normal" if self.circles and not self.busy else "disabled")
        if self.result_folder is not None and not self.busy:
            self.open_button.grid()
            self.open_button.configure(state="normal")
        else:
            self.open_button.grid_remove()

    def advance(self):
        if self.next_button.instate(("disabled",)):
            return
        if self.step == 3:
            self.start_analysis()
        else:
            self.show_step(self.step + 1)

    def go_back(self):
        if self.step > 0 and not self.busy:
            self.show_step(self.step - 1)

    def change_start(self, *_):
        if self.step == 1:
            self.invalidate_result()
            self.direction.set("")
            self.update_buttons()
            self.draw_route(preserve_view=True)

    def change_direction(self, *_):
        if self.step == 2:
            self.invalidate_result()
            self.update_buttons()
            self.draw_route(preserve_view=True)

    def invalidate_result(self):
        if self.analysis_canvas is not None:
            if self.tabs.select() == str(self.analysis_tab):
                self.tabs.select(0)
            self.tabs.tab(self.analysis_tab, state="disabled")
            self.analysis_canvas.get_tk_widget().destroy()
            self.analysis_canvas = None
            self.status.set("設定已更新，請重新完成分析。")
            self.update_buttons()

    def draw_route(self, preserve_view=False):
        ax = self.preview_ax
        limits = (ax.get_xlim(), ax.get_ylim()) if preserve_view else None
        ax.clear()
        index = self.start_index()
        ordered = self.route
        selected = 0 if self.step == 0 else index
        if self.step >= 2 and index is not None:
            ordered = order_from_start(self.route, index + 1, self.direction.get() == "reverse")
            selected = 0
        self.preview_title.set(("原始路段順序", "在原始排序上選起點", "從新起點重新排序", "最終輸出順序")[self.step])
        if not ordered:
            self.preview_help.set("請選取 DXF 並確認賽道路徑圖層。")
        elif self.step == 0:
            self.preview_help.set("編號依原始順序遞增，箭頭從第 1 段出發。")
        elif self.step == 1:
            self.preview_help.set(f"已選起點：原始第 {index + 1} 段" if index is not None else
                                  "點選一個編號接點，選中的起點會以橘色標示。")
        elif index is not None:
            direction = {"forward": "保留原方向", "reverse": "反轉方向"}.get(self.direction.get(), "原方向預覽")
            self.preview_help.set(f"起點：原始第 {index + 1} 段 → 新第 1 段　｜　{direction}")
        if not self.route:
            ax.set_axis_off()
        else:
            ax.set(aspect="equal", xlabel="X (DXF units)", ylabel="Y (DXF units)")
            ax.grid(True, color="#e1e9ee", linewidth=0.7)
            ax.set_axisbelow(True)
            for segment_number, seg in enumerate(ordered, start=1):
                ax.plot(*segment_coordinates(seg), color=ACCENT if seg.type == "ARC" else "#405a71", linewidth=1.6)
                if segment_number - 1 != selected:
                    ax.annotate(str(segment_number), xy=seg.start, xytext=(3, 3), textcoords="offset points",
                                fontsize=8, color=INK, clip_on=True, annotation_clip=True,
                                path_effects=[patheffects.withStroke(linewidth=2, foreground="white")])
            ax.scatter(*zip(*(seg.start for seg in ordered)), s=11, color="#405a71", zorder=3)
            if selected is not None:
                seg = ordered[selected]
                x, y = segment_coordinates(seg)
                step = max(1, len(x) // 4)
                ax.scatter(*seg.start, s=50, color="#c2410c", zorder=4)
                ax.annotate("", xy=(x[step], y[step]), xytext=seg.start,
                            arrowprops={"arrowstyle": "->", "color": "#c2410c", "lw": 1.8})
                ax.annotate(str(selected + 1), xy=seg.start, xytext=(7, 8), textcoords="offset points",
                            color="#a02c07", weight="bold", zorder=5,
                            path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])
            if limits:
                ax.set_xlim(limits[0])
                ax.set_ylim(limits[1])
        self.preview_canvas.draw_idle()

    def start_index(self):
        try:
            index = int(self.start.get()) - 1
        except ValueError:
            return None
        return index if 0 <= index < len(self.route) else None

    def pick_start(self, event):
        if self.step != 1 or event.button != 1 or self.toolbar.mode or event.inaxes is not self.preview_ax:
            return
        screen_points = self.preview_ax.transData.transform([seg.start for seg in self.route])
        distances = [math.dist(point, (event.x, event.y)) for point in screen_points]
        index = min(range(len(distances)), key=distances.__getitem__)
        if distances[index] <= 14:
            self.start.set(str(index + 1))

    @staticmethod
    def number(variable, label):
        try:
            value = float(variable.get())
        except ValueError:
            value = 0
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label}必須是大於零的數字。")
        return value

    def update_xy_mode(self, *_):
        if self.xy_mode.get() == XY_BY_SEGMENT:
            self.xy_value_label.configure(text="每段點數（含兩端）")
            self.xy_value.configure(textvariable=self.xy_points)
        else:
            self.xy_value_label.configure(text="取樣間距（公尺）")
            self.xy_value.configure(textvariable=self.xy_spacing)

    def xy_options(self):
        if self.xy_mode.get() == XY_BY_DISTANCE:
            return {"xy_spacing": self.number(self.xy_spacing, "XY 取樣間距")}
        try:
            points = int(self.xy_points.get())
        except ValueError:
            points = 0
        if points < 2:
            raise ValueError("每段點數必須是至少 2 的整數，以保留兩端。")
        return {"xy_points_per_segment": points}

    def edit_ini_options(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("INI 設定")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        body = ttk.Frame(dialog, padding=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        settings = self.ini_options
        fields = (
            ("高度 Z（模擬器 Y 軸）", "height", settings["height"]),
            ("起始物件編號", "first_model", settings["model_offset"] + 1),
            ("模型檔名", "model_file", settings["model_file"]),
            ("物件名稱", "name", settings["name"]),
            ("旋轉 X, Y, Z（度）", "rotation", ", ".join(map(str, settings["rotation"]))),
        )
        values = {}
        entries = []
        for row, (label, key, value) in enumerate(fields):
            values[key] = tk.StringVar(dialog, value=str(value))
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            entry = ttk.Entry(body, textvariable=values[key], width=25)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            entries.append(entry)
        physical = tk.BooleanVar(dialog, value=settings["physical"])
        ttk.Checkbutton(body, text="啟用物理屬性（PHYSICAL）", variable=physical).grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(6, 0))

        def apply_settings():
            try:
                height = float(values["height"].get())
                first_model = int(values["first_model"].get())
                rotation = tuple(float(angle) for angle in values["rotation"].get().split(","))
                if not math.isfinite(height) or first_model < 0 or len(rotation) != 3:
                    raise ValueError
                if not all(math.isfinite(angle) for angle in rotation):
                    raise ValueError
            except ValueError:
                messagebox.showerror("INI 設定有誤",
                                     "高度需為數字，起始物件編號需為非負整數，旋轉需填入三個以逗號分隔的數字。",
                                     parent=dialog)
                return
            model_file = values["model_file"].get().strip()
            name = values["name"].get().strip()
            if not model_file or not name or any(character in model_file + name for character in "\r\n"):
                messagebox.showerror("INI 設定有誤", "模型檔名與物件名稱需各填一行文字。", parent=dialog)
                return
            self.ini_options = {
                "model_offset": first_model - 1, "height": height, "name": name, "model_file": model_file,
                "rotation": rotation, "physical": physical.get(),
            }
            dialog.destroy()

        buttons = ttk.Frame(body)
        buttons.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="取消", command=dialog.destroy).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="套用", style="Primary.TButton", command=apply_settings).pack(side="left")
        dialog.bind("<Return>", lambda _event: apply_settings())
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.grab_set()
        entries[0].focus_set()

    def start_analysis(self):
        try:
            scale = self.number(self.scale, "每單位公尺數")
            lateral_g = self.number(self.lateral_g, "橫向加速度")
        except ValueError as exc:
            messagebox.showerror("設定有誤", str(exc), parent=self.root)
            return
        self.busy = True
        self.update_buttons()
        self.status.set("正在分析賽道…")
        self.root.after(20, self.finish_analysis, self.route, self.start_index() + 1,
                        self.direction.get() == "reverse", scale, lateral_g)

    def finish_analysis(self, route, start, reverse, scale, lateral_g):
        try:
            figure, total = analyze_track(route, start, reverse, scale, lateral_g)
        except (ValueError, OSError) as exc:
            self.status.set("賽道分析失敗。")
            messagebox.showerror("無法完成分析", str(exc), parent=self.root)
        else:
            self.analysis_canvas = FigureCanvasTkAgg(figure, master=self.analysis_tab)
            self.analysis_canvas.get_tk_widget().pack(fill="both", expand=True)
            self.tabs.tab(self.analysis_tab, state="normal")
            self.tabs.select(self.analysis_tab)
            self.analysis_canvas.draw_idle()
            self.status.set(f"賽道分析完成 · 全長 {total:,.2f} 公尺")
        finally:
            self.busy = False
            self.update_buttons()

    def start_export(self, export_format):
        if self.step != 3 or self.export_buttons[export_format].instate(("disabled",)):
            return
        try:
            index = self.start_index()
            if index is None:
                raise ValueError(f"起跑段必須介於 1 和 {len(self.route)} 之間。")
            scale = self.number(self.scale, "每單位公尺數")
            if export_format == "analysis":
                options = {"lateral_g": self.number(self.lateral_g, "橫向加速度")}
            else:
                options = self.xy_options()
                if export_format == "ini":
                    options["ini_options"] = self.ini_options.copy()
        except ValueError as exc:
            messagebox.showerror("設定有誤", str(exc), parent=self.root)
            return
        label = self.export_buttons[export_format].cget("text")
        folder = self.choose_output_folder(label)
        if not folder:
            return
        self.busy = True
        self.update_buttons()
        self.status.set(f"正在處理「{label}」…")
        self.root.after(20, self.finish_export, self.route, index + 1, self.direction.get() == "reverse",
                        scale, folder, self.path.stem, export_format, options)

    def choose_output_folder(self, label):
        folder = filedialog.askdirectory(
            title=f"{label}：選擇儲存資料夾", parent=self.root, mustexist=True,
            initialdir=str(self.result_folder or self.path.resolve().parent),
        )
        return Path(folder) if folder else None

    def finish_export(self, route, start, reverse, scale, folder, stem, export_format, options):
        try:
            files, _, total = export_track(route, start, reverse, scale, folder, stem, export_format, **options)
        except (ValueError, OSError) as exc:
            self.status.set("輸出失敗。")
            messagebox.showerror("無法輸出", str(exc), parent=self.root)
        else:
            self.result_folder = folder
            label = self.export_buttons[export_format].cget("text")
            self.status.set(f"{label}完成 · {len(files)} 個檔案已儲存至 {folder} · 全長 {total:,.2f} 公尺")
        finally:
            self.busy = False
            self.update_buttons()

    def start_circle_export(self, export_format):
        if self.circle_export_buttons[export_format].instate(("disabled",)):
            return
        try:
            scale = self.number(self.scale, "每單位公尺數")
        except ValueError as exc:
            messagebox.showerror("設定有誤", str(exc), parent=self.root)
            return
        label = self.circle_export_buttons[export_format].cget("text")
        folder = self.choose_output_folder(label)
        if folder is None:
            return
        self.busy = True
        self.update_buttons()
        self.circle_status.set(f"正在處理「{label}」…")
        self.root.after(20, self.finish_circle_export, self.centers, scale, folder, self.path.stem,
                        export_format, self.ini_options.copy())

    def finish_circle_export(self, centers, scale, folder, stem, export_format, ini_options):
        try:
            target = export_circle_centers(centers, scale, folder, stem, export_format, ini_options=ini_options)
        except (ValueError, OSError) as exc:
            self.circle_status.set("圓心匯出失敗。")
            messagebox.showerror("無法匯出圓心", str(exc), parent=self.root)
        else:
            self.result_folder = folder
            self.circle_status.set(f"已匯出 {len(centers):,} 個圓心至 {target.name}")
        finally:
            self.busy = False
            self.update_buttons()

    def open_output(self):
        try:
            os.startfile(self.result_folder)
        except OSError as exc:
            messagebox.showerror("無法開啟資料夾", str(exc), parent=self.root)


def main():
    root = tk.Tk()
    app = TrackApp(root)
    if len(sys.argv) > 1:
        root.after_idle(app.load_file, Path(sys.argv[1]))
    root.mainloop()


if __name__ == "__main__":
    main()
