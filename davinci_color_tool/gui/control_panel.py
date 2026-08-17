# -*- coding: utf-8 -*-
"""控制面板 - 校色参数、滤镜选择、场景检测"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSlider, QLabel,
    QComboBox, QPushButton, QCheckBox, QSpinBox, QDoubleSpinBox,
    QScrollArea, QFrame, QProgressBar, QListWidget, QListWidgetItem,
    QTabWidget, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QSize
from ..core.color_correction import ColorParams
from ..core.filters import FILTER_PRESETS


class ColorControlPanel(QWidget):
    """校色参数控制面板"""

    params_changed = Signal(object)  # ColorParams
    reset_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._params = ColorParams()
        self._building = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 光影修复组
        light_group = QGroupBox("光影修复")
        light_layout = QGridLayout(light_group)

        self._auto_exp = QCheckBox("自动曝光修复")
        self._auto_exp.setChecked(True)
        self._auto_exp.toggled.connect(self._emit_changed)
        light_layout.addWidget(self._auto_exp, 0, 0, 1, 2)

        self._auto_wb = QCheckBox("自动白平衡")
        self._auto_wb.setChecked(True)
        self._auto_wb.toggled.connect(self._emit_changed)
        light_layout.addWidget(self._auto_wb, 0, 2, 1, 2)

        self._shadow_slider, self._shadow_label = self._make_slider("暗部提亮", 0, 100, 30)
        light_layout.addWidget(self._shadow_label, 1, 0)
        light_layout.addWidget(self._shadow_slider, 1, 1, 1, 3)

        self._highlight_slider, self._highlight_label = self._make_slider("高光压制", 0, 100, 30)
        light_layout.addWidget(self._highlight_label, 2, 0)
        light_layout.addWidget(self._highlight_slider, 2, 1, 1, 3)

        self._denoise_slider, self._denoise_label = self._make_slider("降噪强度", 0, 50, 0)
        light_layout.addWidget(self._denoise_label, 3, 0)
        light_layout.addWidget(self._denoise_slider, 3, 1, 1, 3)

        layout.addWidget(light_group)

        # 基础调整组
        basic_group = QGroupBox("基础调整")
        basic_layout = QGridLayout(basic_group)

        self._bright_slider, self._bright_label = self._make_slider("亮度", -100, 100, 0)
        basic_layout.addWidget(self._bright_label, 0, 0)
        basic_layout.addWidget(self._bright_slider, 0, 1)

        self._contrast_slider, self._contrast_label = self._make_slider("对比度", -100, 100, 0)
        basic_layout.addWidget(self._contrast_label, 1, 0)
        basic_layout.addWidget(self._contrast_slider, 1, 1)

        self._sat_slider, self._sat_label = self._make_slider("饱和度", -100, 100, 0)
        basic_layout.addWidget(self._sat_label, 2, 0)
        basic_layout.addWidget(self._sat_slider, 2, 1)

        self._temp_slider, self._temp_label = self._make_slider("色温", -100, 100, 0)
        basic_layout.addWidget(self._temp_label, 3, 0)
        basic_layout.addWidget(self._temp_slider, 3, 1)

        self._tint_slider, self._tint_label = self._make_slider("色调", -100, 100, 0)
        basic_layout.addWidget(self._tint_label, 4, 0)
        basic_layout.addWidget(self._tint_slider, 4, 1)

        self._gamma_spin = QDoubleSpinBox()
        self._gamma_spin.setRange(0.5, 2.5)
        self._gamma_spin.setSingleStep(0.05)
        self._gamma_spin.setValue(1.0)
        self._gamma_spin.valueChanged.connect(self._emit_changed)
        basic_layout.addWidget(QLabel("Gamma"), 5, 0)
        basic_layout.addWidget(self._gamma_spin, 5, 1)

        layout.addWidget(basic_group)

        # 重置按钮
        reset_btn = QPushButton("重置所有参数")
        reset_btn.clicked.connect(self._on_reset)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #ddd;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def _make_slider(self, name: str, min_val: int, max_val: int, default: int):
        label = QLabel(f"{name}: {default}")
        label.setMinimumWidth(70)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.valueChanged.connect(lambda v, l=label, n=name: l.setText(f"{n}: {v}"))
        slider.valueChanged.connect(self._emit_changed)
        return slider, label

    def _emit_changed(self):
        if self._building:
            return
        self._collect_params()
        self.params_changed.emit(self._params)

    def _collect_params(self):
        self._params.auto_exposure = self._auto_exp.isChecked()
        self._params.auto_white_balance = self._auto_wb.isChecked()
        self._params.shadow_lift = self._shadow_slider.value()
        self._params.highlight_recover = self._highlight_slider.value()
        self._params.denoise = self._denoise_slider.value()
        self._params.brightness = self._bright_slider.value()
        self._params.contrast = self._contrast_slider.value()
        self._params.saturation = self._sat_slider.value()
        self._params.temperature = self._temp_slider.value()
        self._params.tint = self._tint_slider.value()
        self._params.gamma = self._gamma_spin.value()

    def _on_reset(self):
        self._building = True
        self._auto_exp.setChecked(True)
        self._auto_wb.setChecked(True)
        self._shadow_slider.setValue(30)
        self._highlight_slider.setValue(30)
        self._denoise_slider.setValue(0)
        self._bright_slider.setValue(0)
        self._contrast_slider.setValue(0)
        self._sat_slider.setValue(0)
        self._temp_slider.setValue(0)
        self._tint_slider.setValue(0)
        self._gamma_spin.setValue(1.0)
        self._building = False
        self._collect_params()
        self.reset_clicked.emit()
        self.params_changed.emit(self._params)

    def get_params(self) -> ColorParams:
        self._collect_params()
        return self._params


class FilterPanel(QWidget):
    """风格化滤镜面板"""

    filter_changed = Signal(str, float)  # preset_name, intensity

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 分类选择
        self._category_combo = QComboBox()
        self._category_combo.addItems(["全部", "电影", "复古", "清新", "黑白", "创意"])
        self._category_combo.currentTextChanged.connect(self._update_filter_list)
        layout.addWidget(QLabel("滤镜分类"))
        layout.addWidget(self._category_combo)

        # 滤镜列表
        layout.addWidget(QLabel("选择滤镜"))
        self._filter_list = QListWidget()
        self._filter_list.setIconSize(QSize(80, 45))
        self._filter_list.currentItemChanged.connect(self._on_filter_selected)
        self._filter_list.setMaximumHeight(200)
        layout.addWidget(self._filter_list)

        # 强度
        self._intensity_slider = QSlider(Qt.Horizontal)
        self._intensity_slider.setRange(0, 100)
        self._intensity_slider.setValue(100)
        self._intensity_label = QLabel("强度: 100%")
        self._intensity_slider.valueChanged.connect(
            lambda v: self._intensity_label.setText(f"强度: {v}%"))
        self._intensity_slider.valueChanged.connect(self._emit_filter)
        layout.addWidget(self._intensity_label)
        layout.addWidget(self._intensity_slider)

        self._update_filter_list("全部")

        layout.addStretch()

    def _update_filter_list(self, category: str):
        self._filter_list.clear()
        for name, preset in FILTER_PRESETS.items():
            if category == "全部" or preset.category == category:
                item = QListWidgetItem(f"{preset.display_name}  -  {preset.description}")
                item.setData(Qt.UserRole, name)
                self._filter_list.addItem(item)
        # 默认选中第一个
        if self._filter_list.count() > 0:
            self._filter_list.setCurrentRow(0)

    def _on_filter_selected(self, current, previous):
        if current:
            self._emit_filter()

    def _emit_filter(self):
        item = self._filter_list.currentItem()
        if item:
            name = item.data(Qt.UserRole)
            intensity = self._intensity_slider.value() / 100.0
            self.filter_changed.emit(name, intensity)

    def get_current(self) -> tuple[str, float]:
        item = self._filter_list.currentItem()
        if item:
            return item.data(Qt.UserRole), self._intensity_slider.value() / 100.0
        return "none", 1.0


class ScenePanel(QWidget):
    """场景检测面板"""

    detect_clicked = Signal(float, float)  # threshold, min_scene_len
    scene_selected = Signal(int)  # scene index
    export_scene_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 检测参数
        param_group = QGroupBox("场景检测参数")
        param_layout = QGridLayout(param_group)

        param_layout.addWidget(QLabel("敏感度阈值"), 0, 0)
        self._threshold_spin = QDoubleSpinBox()
        self._threshold_spin.setRange(5.0, 80.0)
        self._threshold_spin.setValue(27.0)
        self._threshold_spin.setSingleStep(1.0)
        param_layout.addWidget(self._threshold_spin, 0, 1)

        param_layout.addWidget(QLabel("最短场景(秒)"), 1, 0)
        self._min_len_spin = QDoubleSpinBox()
        self._min_len_spin.setRange(0.1, 10.0)
        self._min_len_spin.setValue(0.5)
        self._min_len_spin.setSingleStep(0.1)
        param_layout.addWidget(self._min_len_spin, 1, 1)

        layout.addWidget(param_group)

        # 检测按钮
        self._detect_btn = QPushButton("自动检测场景剪切")
        self._detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d6cdf;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3d7cef; }
            QPushButton:disabled { background-color: #555; }
        """)
        self._detect_btn.clicked.connect(self._on_detect)
        layout.addWidget(self._detect_btn)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # 场景列表
        layout.addWidget(QLabel("检测到的场景"))
        self._scene_list = QListWidget()
        self._scene_list.currentRowChanged.connect(self.scene_selected.emit)
        self._scene_list.setMaximumHeight(180)
        layout.addWidget(self._scene_list)

        # 导出选中场景
        self._export_scene_btn = QPushButton("仅导出选中场景")
        self._export_scene_btn.clicked.connect(self.export_scene_clicked.emit)
        self._export_scene_btn.setEnabled(False)
        layout.addWidget(self._export_scene_btn)

        layout.addStretch()

    def _on_detect(self):
        self.detect_clicked.emit(self._threshold_spin.value(),
                                 self._min_len_spin.value())

    def set_scenes(self, scenes: list):
        self._scene_list.clear()
        for s in scenes:
            item = QListWidgetItem(
                f"场景 {s.index + 1}: {s.start_time:.2f}s - {s.end_time:.2f}s "
                f"({s.duration:.2f}s, {s.frame_count}帧)"
            )
            self._scene_list.addItem(item)
        self._export_scene_btn.setEnabled(len(scenes) > 0)

    def show_progress(self, visible: bool):
        self._progress.setVisible(visible)
        self._detect_btn.setEnabled(not visible)

    def set_progress(self, percent: float):
        self._progress.setValue(int(percent))

    def get_selected_scene_index(self) -> int:
        return self._scene_list.currentRow()
