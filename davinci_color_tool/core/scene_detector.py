# -*- coding: utf-8 -*-
"""自动场景剪切检测模块"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Callable
from .video_loader import VideoLoader


@dataclass
class SceneCut:
    """场景切点"""
    frame_idx: int
    time_sec: float
    score: float  # 差异分数
    method: str


@dataclass
class Scene:
    """场景片段"""
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    index: int

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame


class SceneDetector:
    """
    自动场景检测
    支持三种算法：
    - content: 基于内容的直方图差异（PySceneDetect风格）
    - adaptive: 自适应阈值
    - threshold: 固定阈值
    """

    def __init__(self, method: str = "content", threshold: float = 27.0,
                 min_scene_len: float = 0.5, show_progress: Optional[Callable] = None):
        """
        Args:
            method: content / adaptive / threshold
            threshold: 差异阈值（content模式下推荐20-40）
            min_scene_len: 最短场景长度（秒）
            show_progress: 进度回调 callback(percent: float)
        """
        self.method = method
        self.threshold = threshold
        self.min_scene_len = min_scene_len
        self.show_progress = show_progress
        self._cuts: List[SceneCut] = []
        self._scenes: List[Scene] = []

    @property
    def cuts(self) -> List[SceneCut]:
        return self._cuts

    @property
    def scenes(self) -> List[Scene]:
        return self._scenes

    def detect(self, loader: VideoLoader) -> List[Scene]:
        """对已加载的视频执行场景检测"""
        if not loader.is_opened:
            return []

        info = loader.info
        fps = info.fps
        total = info.total_frames
        min_frames = max(1, int(fps * self.min_scene_len))

        # 重置到开头
        loader.set_pos(0)
        prev_frame = loader.read_current()
        if prev_frame is None:
            return []

        prev_hist = self._calc_hist(prev_frame)
        cuts = []
        last_cut_frame = 0

        frame_idx = 1
        while True:
            frame = loader.read_current()
            if frame is None:
                break

            curr_hist = self._calc_hist(frame)
            score = self._calc_diff(prev_hist, curr_hist)

            if score >= self.threshold and (frame_idx - last_cut_frame) >= min_frames:
                cuts.append(SceneCut(
                    frame_idx=frame_idx,
                    time_sec=frame_idx / fps,
                    score=score,
                    method=self.method,
                ))
                last_cut_frame = frame_idx

            prev_hist = curr_hist
            frame_idx += 1

            if self.show_progress and frame_idx % 30 == 0:
                self.show_progress(min(100.0, frame_idx / total * 100))

        # 构建场景列表
        self._cuts = cuts
        self._scenes = self._build_scenes(cuts, total, fps)

        if self.show_progress:
            self.show_progress(100.0)

        return self._scenes

    def _calc_hist(self, frame: np.ndarray) -> np.ndarray:
        """计算HSV直方图（H,S各32bin，V忽略以降低亮度影响）"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
        cv2.normalize(hist_h, hist_h)
        cv2.normalize(hist_s, hist_s)
        return np.concatenate([hist_h.flatten(), hist_s.flatten()])

    def _calc_diff(self, hist_a: np.ndarray, hist_b: np.ndarray) -> float:
        """计算直方图差异（相关系数距离）"""
        if self.method == "content":
            # 相关系数 -> 距离
            corr = cv2.compareHist(hist_a.astype(np.float32),
                                   hist_b.astype(np.float32),
                                   cv2.HISTCMP_CORREL)
            return max(0.0, (1.0 - corr) * 100.0)
        elif self.method == "threshold":
            # 卡方距离
            chi = cv2.compareHist(hist_a.astype(np.float32),
                                  hist_b.astype(np.float32),
                                  cv2.HISTCMP_CHISQR)
            return chi
        else:  # adaptive
            # 交集距离
            inter = cv2.compareHist(hist_a.astype(np.float32),
                                    hist_b.astype(np.float32),
                                    cv2.HISTCMP_INTERSECT)
            return max(0.0, (1.0 - inter / max(hist_a.sum(), 1e-6)) * 100.0)

    def _build_scenes(self, cuts: List[SceneCut], total_frames: int,
                      fps: float) -> List[Scene]:
        scenes = []
        boundaries = [0] + [c.frame_idx for c in cuts] + [total_frames]
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            scenes.append(Scene(
                start_frame=start,
                end_frame=end,
                start_time=start / fps,
                end_time=end / fps,
                index=i,
            ))
        return scenes
