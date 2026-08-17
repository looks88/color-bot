# -*- coding: utf-8 -*-
"""主窗口 - 整合所有功能模块"""
import os
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QStatusBar, QToolBar, QLabel,
    QPushButton, QComboBox, QProgressBar, QSlider, QDockWidget,
    QTabWidget, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence, QDragEnterEvent, QDropEvent

from ..core import (
    VideoLoader, SceneDetector, ColorCorrector, ColorParams,
    StyleFilter, VideoExporter, Scene
)
from .preview_widget import PreviewWidget
from .control_panel import ColorControlPanel, FilterPanel, ScenePanel


class ExportWorker(QThread):
    """导出工作线程"""
    progress = Signal(float, int, int)
    finished = Signal(bool, str)

    def __init__(self, exporter: VideoExporter, output_path: str,
                 codec: str, scenes: list = None):
        super().__init__()
        self.exporter = exporter
        self.output_path = output_path
        self.codec = codec
        self.scenes = scenes
        self._cancel = False

    def run(self):
        try:
            success = self.exporter.export(
                self.output_path, self.codec,
                scenes=self.scenes,
                show_progress=lambda p, c, t: self.progress.emit(p, c, t),
                cancel_check=lambda: self._cancel
            )
            self.finished.emit(success, self.output_path)
        except Exception as e:
            self.finished.emit(False, str(e))

    def cancel(self):
        self._cancel = True


class DetectWorker(QThread):
    """场景检测工作线程"""
    progress = Signal(float)
    finished = Signal(list)

    def __init__(self, detector: SceneDetector, loader: VideoLoader):
        super().__init__()
        self.detector = detector
        self.loader = loader

    def run(self):
        scenes = self.detector.detect(self.loader)
        self.finished.emit(scenes)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("达芬奇校色工具 - DaVinci Color Studio")
        self.setMinimumSize(1280, 720)
        self.resize(1440, 850)

        # 核心组件
        self.loader = VideoLoader()
        self.corrector = ColorCorrector()
        self.style_filter = StyleFilter()
        self.exporter = VideoExporter(self.loader, self.corrector, self.style_filter)
        self.detector: SceneDetector | None = None
        self.scenes: list[Scene] = []

        # 当前状态
        self._current_frame_idx = 0
        self._current_frame: np.ndarray | None = None
        self._is_playing = False
        self._play_timer = QTimer()
        self._play_timer.timeout.connect(self._next_frame)

        # 工作线程
        self._export_worker: ExportWorker | None = None
        self._detect_worker: DetectWorker | None = None

        self._setup_ui()
        self._setup_menu_toolbar()
        self._setup_style()
        self._update_ui_state()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Horizontal)

        # 左侧：预览区
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.preview = PreviewWidget()
        left_layout.addWidget(self.preview, 1)

        # 播放控制条
        play_bar = QHBoxLayout()
        self._play_btn = QPushButton("▶ 播放")
        self._play_btn.setFixedWidth(80)
        self._play_btn.clicked.connect(self._toggle_play)
        play_bar.addWidget(self._play_btn)

        self._frame_slider = QSlider(Qt.Horizontal)
        self._frame_slider.setRange(0, 0)
        self._frame_slider.valueChanged.connect(self._on_frame_slider)
        play_bar.addWidget(self._frame_slider, 1)

        self._frame_label = QLabel("0 / 0")
        self._frame_label.setFixedWidth(100)
        self._frame_label.setAlignment(Qt.AlignCenter)
        play_bar.addWidget(self._frame_label)

        left_layout.addLayout(play_bar)

        splitter.addWidget(left_widget)

        # 右侧：控制面板（标签页）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        self.color_panel = ColorControlPanel()
        self.filter_panel = FilterPanel()
        self.scene_panel = ScenePanel()

        self._tabs.addTab(self.color_panel, "校色调整")
        self._tabs.addTab(self.filter_panel, "风格滤镜")
        self._tabs.addTab(self.scene_panel, "场景剪切")

        # 导出面板
        export_widget = QWidget()
        export_layout = QVBoxLayout(export_widget)
        export_layout.setContentsMargins(8, 8, 8, 8)

        export_group = QGroupBox("导出设置")
        eg_layout = QVBoxLayout(export_group)

        eg_layout.addWidget(QLabel("输出格式"))
        self._codec_combo = QComboBox()
        self._codec_combo.addItems(list(VideoExporter.SUPPORTED_CODECS.keys()))
        eg_layout.addWidget(self._codec_combo)

        self._apply_all_scenes = QCheckBox("应用到全部场景（默认全片导出）")
        self._apply_all_scenes.setChecked(True)
        eg_layout.addWidget(self._apply_all_scenes)

        self._export_btn = QPushButton("导出校色后视频")
        self._export_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 12px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f39c12; }
            QPushButton:disabled { background-color: #555; }
        """)
        self._export_btn.clicked.connect(self._on_export)
        eg_layout.addWidget(self._export_btn)

        self._export_frame_btn = QPushButton("导出当前帧为图片")
        self._export_frame_btn.clicked.connect(self._on_export_frame)
        eg_layout.addWidget(self._export_frame_btn)

        self._export_progress = QProgressBar()
        self._export_progress.setVisible(False)
        eg_layout.addWidget(self._export_progress)

        export_layout.addWidget(export_group)
        export_layout.addStretch()

        self._tabs.addTab(export_widget, "导出")

        right_layout.addWidget(self._tabs)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([900, 400])

        main_layout.addWidget(splitter)

        # 信号连接
        self.color_panel.params_changed.connect(self._on_params_changed)
        self.color_panel.reset_clicked.connect(self._refresh_preview)
        self.filter_panel.filter_changed.connect(self._on_filter_changed)
        self.scene_panel.detect_clicked.connect(self._on_detect_scenes)
        self.scene_panel.scene_selected.connect(self._on_scene_selected)
        self.scene_panel.export_scene_clicked.connect(self._on_export_selected_scene)

        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("就绪 - 请导入视频")
        self._status_bar.addWidget(self._status_label)

        # 支持拖放
        self.setAcceptDrops(True)

    def _setup_menu_toolbar(self):
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        import_action = QAction("导入视频...", self)
        import_action.setShortcut(QKeySequence.Open)
        import_action.triggered.connect(self._on_import)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        export_action = QAction("导出视频...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        split_action = QAction("切换分屏对比", self)
        split_action.setShortcut("Ctrl+D")
        split_action.triggered.connect(
            lambda: self.preview._toggle_btn.toggle())
        view_menu.addAction(split_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # 工具栏
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        import_btn = QPushButton("📁 导入视频")
        import_btn.clicked.connect(self._on_import)
        toolbar.addWidget(import_btn)

        toolbar.addSeparator()

        self._video_info_label = QLabel("  未加载视频  ")
        self._video_info_label.setStyleSheet("color: #aaa; padding: 0 10px;")
        toolbar.addWidget(self._video_info_label)

        toolbar.addSeparator()

        prev_btn = QPushButton("⏮ 上一帧")
        prev_btn.clicked.connect(self._prev_frame)
        toolbar.addWidget(prev_btn)

        next_btn = QPushButton("下一帧 ⏭")
        next_btn.clicked.connect(self._next_frame)
        toolbar.addWidget(next_btn)

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #ddd;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
                font-weight: bold;
                color: #ccc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 4px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #333;
                color: #aaa;
                padding: 8px 16px;
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2d6cdf;
                color: white;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #444;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2d6cdf;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #333;
                border: 1px solid #555;
                padding: 4px;
                border-radius: 3px;
                color: #ddd;
            }
            QComboBox::drop-down { border: none; }
            QListWidget {
                background-color: #222;
                border: 1px solid #444;
                border-radius: 4px;
                color: #ccc;
            }
            QListWidget::item:selected {
                background-color: #2d6cdf;
                color: white;
            }
            QProgressBar {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2d6cdf;
                border-radius: 2px;
            }
            QToolBar {
                background-color: #252525;
                border-bottom: 1px solid #444;
                spacing: 6px;
                padding: 4px;
            }
            QToolBar QPushButton {
                background-color: #3a3a3a;
                color: #ddd;
                border: 1px solid #555;
                padding: 5px 12px;
                border-radius: 3px;
            }
            QToolBar QPushButton:hover {
                background-color: #4a4a4a;
            }
            QMenuBar {
                background-color: #252525;
                color: #ddd;
            }
            QMenuBar::item:selected {
                background-color: #2d6cdf;
            }
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #2d6cdf;
            }
            QStatusBar {
                background-color: #252525;
                color: #aaa;
            }
            QCheckBox { spacing: 6px; }
            QCheckBox::indicator {
                width: 14px; height: 14px;
                border: 1px solid #666;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #2d6cdf;
                border-color: #2d6cdf;
            }
        """)

    # ========== 文件操作 ==========

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.m4v);;所有文件 (*.*)"
        )
        if path:
            self._load_video(path)

    def _load_video(self, path: str):
        if not self.loader.open(path):
            QMessageBox.critical(self, "错误", f"无法打开视频文件:\n{path}")
            return

        info = self.loader.info
        self._current_frame_idx = 0
        self._frame_slider.setRange(0, max(0, info.total_frames - 1))
        self._video_info_label.setText(
            f"  {info.filename}  |  {info.width}x{info.height}  |  "
            f"{info.fps:.2f}fps  |  {info.duration_str}  |  {info.total_frames}帧  "
        )
        self._status_label.setText(f"已加载: {info.filename}")
        self._refresh_preview()
        self._update_ui_state()

    # ========== 预览控制 ==========

    def _refresh_preview(self):
        if not self.loader.is_opened:
            return
        frame = self.loader.read_frame(self._current_frame_idx)
        if frame is None:
            return
        self._current_frame = frame
        processed = self.corrector.process(frame)
        processed = self.style_filter.apply(processed)

        info = self.loader.info
        time_str = f"{self._current_frame_idx / info.fps:.2f}s"
        frame_text = f"帧 {self._current_frame_idx} / {info.total_frames - 1}  |  {time_str}"
        self.preview.set_frames(frame, processed, frame_text)
        self._frame_label.setText(f"{self._current_frame_idx} / {info.total_frames - 1}")

    def _on_frame_slider(self, value: int):
        if self._current_frame_idx != value:
            self._current_frame_idx = value
            self._refresh_preview()

    def _next_frame(self):
        if not self.loader.is_opened:
            return
        info = self.loader.info
        if self._current_frame_idx < info.total_frames - 1:
            self._current_frame_idx += 1
            self._frame_slider.blockSignals(True)
            self._frame_slider.setValue(self._current_frame_idx)
            self._frame_slider.blockSignals(False)
            self._refresh_preview()
        else:
            self._stop_play()

    def _prev_frame(self):
        if not self.loader.is_opened:
            return
        if self._current_frame_idx > 0:
            self._current_frame_idx -= 1
            self._frame_slider.blockSignals(True)
            self._frame_slider.setValue(self._current_frame_idx)
            self._frame_slider.blockSignals(False)
            self._refresh_preview()

    def _toggle_play(self):
        if self._is_playing:
            self._stop_play()
        else:
            self._start_play()

    def _start_play(self):
        if not self.loader.is_opened:
            return
        self._is_playing = True
        self._play_btn.setText("⏸ 暂停")
        info = self.loader.info
        interval = int(1000 / info.fps) if info.fps > 0 else 40
        self._play_timer.start(interval)

    def _stop_play(self):
        self._is_playing = False
        self._play_btn.setText("▶ 播放")
        self._play_timer.stop()

    # ========== 校色/滤镜回调 ==========

    def _on_params_changed(self, params: ColorParams):
        self.corrector.params = params
        self._refresh_preview()

    def _on_filter_changed(self, name: str, intensity: float):
        self.style_filter.preset_name = name
        self.style_filter.intensity = intensity
        self._refresh_preview()

    # ========== 场景检测 ==========

    def _on_detect_scenes(self, threshold: float, min_len: float):
        if not self.loader.is_opened:
            QMessageBox.warning(self, "提示", "请先导入视频")
            return

        self._stop_play()
        self.detector = SceneDetector(
            method="content",
            threshold=threshold,
            min_scene_len=min_len,
            show_progress=lambda p: self.scene_panel.set_progress(p)
        )
        self.scene_panel.show_progress(True)
        self.scene_panel.set_progress(0)

        self._detect_worker = DetectWorker(self.detector, self.loader)
        self._detect_worker.progress.connect(self.scene_panel.set_progress)
        self._detect_worker.finished.connect(self._on_detect_finished)
        self._detect_worker.start()

    def _on_detect_finished(self, scenes: list):
        self.scenes = scenes
        self.scene_panel.set_scenes(scenes)
        self.scene_panel.show_progress(False)
        self._status_label.setText(f"场景检测完成，共检测到 {len(scenes)} 个场景")

    def _on_scene_selected(self, index: int):
        if 0 <= index < len(self.scenes):
            scene = self.scenes[index]
            self._current_frame_idx = scene.start_frame
            self._frame_slider.blockSignals(True)
            self._frame_slider.setValue(self._current_frame_idx)
            self._frame_slider.blockSignals(False)
            self._refresh_preview()

    def _on_export_selected_scene(self):
        idx = self.scene_panel.get_selected_scene_index()
        if idx < 0:
            return
        self._apply_all_scenes.setChecked(False)
        self._tabs.setCurrentIndex(3)  # 切换到导出标签
        self._on_export(selected_scenes=[self.scenes[idx]])

    # ========== 导出 ==========

    def _on_export(self, selected_scenes: list = None):
        if not self.loader.is_opened:
            QMessageBox.warning(self, "提示", "请先导入视频")
            return

        self._stop_play()

        # 确定导出范围
        scenes_to_export = None
        if selected_scenes:
            scenes_to_export = selected_scenes
        elif not self._apply_all_scenes.isChecked() and self.scenes:
            idx = self.scene_panel.get_selected_scene_index()
            if idx >= 0:
                scenes_to_export = [self.scenes[idx]]

        default_name = os.path.splitext(self.loader.info.filename)[0] + "_校色"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出视频", default_name,
            "MP4视频 (*.mp4);;AVI视频 (*.avi);;MOV视频 (*.mov);;WebM (*.webm)"
        )
        if not path:
            return

        codec = self._codec_combo.currentText()
        self._export_progress.setVisible(True)
        self._export_progress.setValue(0)
        self._export_btn.setEnabled(False)
        self._status_label.setText("正在导出视频...")

        self._export_worker = ExportWorker(
            self.exporter, path, codec, scenes_to_export)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.start()

    def _on_export_progress(self, percent: float, current: int, total: int):
        self._export_progress.setValue(int(percent))
        self._status_label.setText(f"导出中... {current}/{total} 帧 ({percent:.1f}%)")

    def _on_export_finished(self, success: bool, path: str):
        self._export_progress.setVisible(False)
        self._export_btn.setEnabled(True)
        if success:
            self._status_label.setText(f"导出完成: {path}")
            QMessageBox.information(self, "导出成功", f"视频已导出到:\n{path}")
        else:
            self._status_label.setText("导出失败")
            QMessageBox.critical(self, "导出失败", f"导出过程中出现错误:\n{path}")

    def _on_export_frame(self):
        if self._current_frame is None:
            QMessageBox.warning(self, "提示", "没有可导出的帧")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出当前帧", "frame.png",
            "PNG图片 (*.png);;JPEG图片 (*.jpg *.jpeg)"
        )
        if path:
            if self.exporter.export_frame(self._current_frame, path):
                self._status_label.setText(f"帧已导出: {path}")
            else:
                QMessageBox.critical(self, "错误", "导出帧失败")

    # ========== UI状态 ==========

    def _update_ui_state(self):
        has_video = self.loader.is_opened
        self._play_btn.setEnabled(has_video)
        self._frame_slider.setEnabled(has_video)
        self._export_btn.setEnabled(has_video)
        self._export_frame_btn.setEnabled(has_video)
        self.scene_panel._detect_btn.setEnabled(has_video)

    def _show_about(self):
        QMessageBox.about(self, "关于",
            "<h3>达芬奇校色工具 DaVinci Color Studio</h3>"
            "<p>专业视频校色与风格化处理工具</p>"
            "<ul>"
            "<li>自动场景剪切检测</li>"
            "<li>智能光影修复（自动曝光/白平衡/暗部高光）</li>"
            "<li>16种电影级风格化滤镜</li>"
            "<li>实时分屏对比预览</li>"
            "<li>多格式视频导出</li>"
            "</ul>"
            "<p>版本 1.0.0</p>"
        )

    # ========== 拖放支持 ==========

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path and os.path.isfile(path):
                self._load_video(path)

    def closeEvent(self, event):
        self._stop_play()
        if self._export_worker and self._export_worker.isRunning():
            self._export_worker.cancel()
            self._export_worker.wait()
        if self._detect_worker and self._detect_worker.isRunning():
            self._detect_worker.wait()
        self.loader.release()
        event.accept()
