# -*- coding: utf-8 -*-
"""视频导出模块"""
import cv2
import os
import numpy as np
from typing import Optional, Callable, List
from .video_loader import VideoLoader, VideoInfo
from .color_correction import ColorCorrector, ColorParams
from .filters import StyleFilter
from .scene_detector import Scene


class VideoExporter:
    """视频导出器，逐帧处理并写入"""

    SUPPORTED_CODECS = {
        "MP4 (H.264)": ("mp4", "mp4v"),
        "MP4 (H.264 high)": ("mp4", "avc1"),
        "AVI (无损)": ("avi", "FMP4"),
        "MOV": ("mov", "mp4v"),
        "WebM": ("webm", "VP80"),
    }

    def __init__(self, loader: VideoLoader, corrector: ColorCorrector,
                 style_filter: StyleFilter):
        self.loader = loader
        self.corrector = corrector
        self.style_filter = style_filter

    def export(self, output_path: str, codec_name: str = "MP4 (H.264)",
               target_fps: Optional[float] = None,
               scenes: Optional[List[Scene]] = None,
               show_progress: Optional[Callable] = None,
               cancel_check: Optional[Callable] = None) -> bool:
        """
        导出视频
        Args:
            output_path: 输出路径
            codec_name: 编码格式名
            target_fps: 目标帧率，None则使用原视频
            scenes: 仅导出指定场景列表，None则全片
            show_progress: 进度回调 callback(percent, current_frame, total)
            cancel_check: 取消检查 callback() -> bool
        """
        if not self.loader.is_opened:
            return False

        info = self.loader.info
        fps = target_fps or info.fps
        ext, fourcc_str = self.SUPPORTED_CODECS.get(codec_name, ("mp4", "mp4v"))

        # 确保扩展名
        if not output_path.lower().endswith(f".{ext}"):
            output_path = os.path.splitext(output_path)[0] + f".{ext}"

        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        writer = cv2.VideoWriter(output_path, fourcc, fps,
                                 (info.width, info.height))
        if not writer.isOpened():
            # 回退到mp4v
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps,
                                     (info.width, info.height))
            if not writer.isOpened():
                return False

        # 确定要导出的帧范围
        if scenes:
            frame_ranges = [(s.start_frame, s.end_frame) for s in scenes]
        else:
            frame_ranges = [(0, info.total_frames)]

        total_to_export = sum(end - start for start, end in frame_ranges)
        processed = 0

        try:
            for start, end in frame_ranges:
                self.loader.set_pos(start)
                for _ in range(start, end):
                    if cancel_check and cancel_check():
                        writer.release()
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        return False

                    frame = self.loader.read_current()
                    if frame is None:
                        break

                    # 校色
                    processed_frame = self.corrector.process(frame)
                    # 风格滤镜
                    processed_frame = self.style_filter.apply(processed_frame)

                    writer.write(processed_frame)
                    processed += 1

                    if show_progress and processed % 10 == 0:
                        percent = processed / total_to_export * 100
                        show_progress(percent, processed, total_to_export)

            if show_progress:
                show_progress(100.0, processed, total_to_export)

        finally:
            writer.release()

        return os.path.exists(output_path) and os.path.getsize(output_path) > 0

    def export_frame(self, frame: np.ndarray, output_path: str) -> bool:
        """导出单帧为图片"""
        processed = self.corrector.process(frame)
        processed = self.style_filter.apply(processed)
        return cv2.imwrite(output_path, processed)
