# -*- coding: utf-8 -*-
"""视频预览组件 - 支持原图/校色后对比显示"""
import cv2
import numpy as np
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSlider, QPushButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QFont


class PreviewWidget(QWidget):
    """视频预览组件，支持左右分屏对比"""

    frame_clicked = Signal(int)  # 点击位置对应帧号（如果有总帧数）

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pixmap: QPixmap | None = None
        self._processed_pixmap: QPixmap | None = None
        self._split_ratio: float = 0.5  # 分屏位置 0~1
        self._show_split: bool = True
        self._frame_text: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setMinimumSize(640, 360)
        self._label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        self._label.setText("拖拽视频文件到此处\n或点击「导入视频」开始")
        self._label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px dashed #444;
                border-radius: 8px;
                color: #888;
                font-size: 16px;
            }
        """)

        layout.addWidget(self._label)

        # 分屏控制条
        ctrl_layout = QHBoxLayout()
        self._split_slider = QSlider(Qt.Horizontal)
        self._split_slider.setRange(0, 100)
        self._split_slider.setValue(50)
        self._split_slider.valueChanged.connect(self._on_split_changed)
        ctrl_layout.addWidget(QLabel("原图"))
        ctrl_layout.addWidget(self._split_slider, 1)
        ctrl_layout.addWidget(QLabel("校色后"))

        self._toggle_btn = QPushButton("分屏对比")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(True)
        self._toggle_btn.toggled.connect(self._on_toggle_split)
        ctrl_layout.addWidget(self._toggle_btn)

        layout.addLayout(ctrl_layout)

    def set_frames(self, original: np.ndarray | None, processed: np.ndarray | None,
                   frame_text: str = ""):
        """设置预览帧（BGR格式numpy数组）"""
        self._original_pixmap = self._numpy_to_pixmap(original) if original is not None else None
        self._processed_pixmap = self._numpy_to_pixmap(processed) if processed is not None else None
        self._frame_text = frame_text
        self._update_display()

    def set_placeholder(self, text: str):
        self._label.setText(text)
        self._original_pixmap = None
        self._processed_pixmap = None

    def _numpy_to_pixmap(self, frame: np.ndarray) -> QPixmap:
        """BGR numpy -> QPixmap"""
        if frame is None or frame.size == 0:
            return QPixmap()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())

    def _update_display(self):
        if self._original_pixmap is None and self._processed_pixmap is None:
            return

        # 目标尺寸
        target_size = self._label.size()
        target_w = target_size.width()
        target_h = target_size.height()

        if self._show_split and self._original_pixmap and self._processed_pixmap:
            # 分屏合成
            result = QPixmap(target_w, target_h)
            result.fill(QColor("#1a1a1a"))
            painter = QPainter(result)

            # 缩放两张图到相同尺寸
            scaled_orig = self._original_pixmap.scaled(
                target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scaled_proc = self._processed_pixmap.scaled(
                target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            x_offset = (target_w - scaled_orig.width()) // 2
            y_offset = (target_h - scaled_orig.height()) // 2
            split_x = int(scaled_orig.width() * self._split_ratio)

            # 左半：原图
            painter.drawPixmap(x_offset, y_offset, split_x, scaled_orig.height(),
                               scaled_orig, 0, 0, split_x, scaled_orig.height())
            # 右半：校色后
            painter.drawPixmap(x_offset + split_x, y_offset,
                               scaled_proc.width() - split_x, scaled_proc.height(),
                               scaled_proc, split_x, 0,
                               scaled_proc.width() - split_x, scaled_proc.height())

            # 分割线
            painter.setPen(QColor("#00d4ff"))
            painter.drawLine(x_offset + split_x, y_offset,
                             x_offset + split_x, y_offset + scaled_orig.height())

            # 标签
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
            painter.drawText(x_offset + 10, y_offset + 25, "原图")
            painter.drawText(x_offset + scaled_proc.width() - 60, y_offset + 25, "校色后")

            # 帧信息
            if self._frame_text:
                painter.drawText(x_offset + 10, y_offset + scaled_orig.height() - 10,
                                 self._frame_text)

            painter.end()
            self._label.setPixmap(result)
        else:
            # 单图显示
            pix = self._processed_pixmap or self._original_pixmap
            if pix:
                scaled = pix.scaled(target_w, target_h, Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation)
                self._label.setPixmap(scaled)

    def _on_split_changed(self, value: int):
        self._split_ratio = value / 100.0
        self._update_display()

    def _on_toggle_split(self, checked: bool):
        self._show_split = checked
        self._split_slider.setEnabled(checked)
        self._update_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()
