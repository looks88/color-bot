# -*- coding: utf-8 -*-
"""视频加载与基础信息模块"""
import cv2
import os
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class VideoInfo:
    """视频元信息"""
    path: str
    filename: str
    width: int
    height: int
    fps: float
    total_frames: int
    duration: float  # 秒
    codec: str
    fourcc: str

    @property
    def resolution(self) -> Tuple[int, int]:
        return (self.width, self.height)

    @property
    def duration_str(self) -> str:
        h = int(self.duration // 3600)
        m = int((self.duration % 3600) // 60)
        s = int(self.duration % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


class VideoLoader:
    """视频加载器，封装 OpenCV VideoCapture"""

    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._info: Optional[VideoInfo] = None

    def open(self, path: str) -> bool:
        """打开视频文件"""
        if not os.path.exists(path):
            return False
        self._cap = cv2.VideoCapture(path)
        if not self._cap.isOpened():
            self._cap = None
            return False

        width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        total = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc_int = int(self._cap.get(cv2.CAP_PROP_FOURCC))
        fourcc = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
        codec = fourcc
        duration = total / fps if fps > 0 else 0

        self._info = VideoInfo(
            path=path,
            filename=os.path.basename(path),
            width=width,
            height=height,
            fps=fps if fps > 0 else 25.0,
            total_frames=total,
            duration=duration,
            codec=codec,
            fourcc=fourcc,
        )
        return True

    @property
    def info(self) -> Optional[VideoInfo]:
        return self._info

    @property
    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def read_frame(self, frame_idx: int) -> Optional[np.ndarray]:
        """读取指定帧（BGR格式）"""
        if not self.is_opened:
            return None
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self._cap.read()
        if ret:
            return frame
        return None

    def read_current(self) -> Optional[np.ndarray]:
        """读取当前帧"""
        if not self.is_opened:
            return None
        ret, frame = self._cap.read()
        if ret:
            return frame
        return None

    def set_pos(self, frame_idx: int):
        if self.is_opened:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

    def release(self):
        if self._cap:
            self._cap.release()
            self._cap = None
        self._info = None

    def __del__(self):
        self.release()
