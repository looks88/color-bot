# -*- coding: utf-8 -*-
"""风格化滤镜模块 - 提供多种电影级LUT风格"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, Callable, Optional


@dataclass
class FilterPreset:
    """滤镜预设"""
    name: str
    display_name: str
    category: str  # 电影/复古/清新/黑白/创意
    description: str


# 滤镜预设列表
FILTER_PRESETS: Dict[str, FilterPreset] = {
    "none": FilterPreset("none", "原图", "基础", "不应用任何滤镜"),
    "cinematic_teal_orange": FilterPreset("cinematic_teal_orange", "电影·青橙", "电影", "经典好莱坞青橙对比色调"),
    "cinematic_warm": FilterPreset("cinematic_warm", "电影·暖调", "电影", "温暖厚重的电影感"),
    "cinematic_cool": FilterPreset("cinematic_cool", "电影·冷调", "电影", "冷峻压抑的电影感"),
    "vintage_film": FilterPreset("vintage_film", "复古胶片", "复古", "老胶片颗粒与褪色感"),
    "vintage_sepia": FilterPreset("vintage_sepia", "复古棕褐", "复古", "经典棕褐色调"),
    "vintage_70s": FilterPreset("vintage_70s", "复古70年代", "复古", "70年代褪色暖黄"),
    "fresh_clean": FilterPreset("fresh_clean", "清新通透", "清新", "明亮干净的清新感"),
    "fresh_japanese": FilterPreset("fresh_japanese", "日系清新", "清新", "日系低饱和淡雅"),
    "bw_high_contrast": FilterPreset("bw_high_contrast", "黑白高对比", "黑白", "高对比黑白"),
    "bw_silver": FilterPreset("bw_silver", "黑白银盐", "黑白", "银盐胶片黑白"),
    "bw_soft": FilterPreset("bw_soft", "黑白柔和", "黑白", "低对比柔和黑白"),
    "dreamy_glow": FilterPreset("dreamy_glow", "梦幻柔光", "创意", "柔光梦幻效果"),
    "noir": FilterPreset("noir", "黑色电影", "创意", "黑色电影高反差"),
    "vivid": FilterPreset("vivid", "鲜艳浓郁", "创意", "高饱和浓郁色彩"),
    "fade_matte": FilterPreset("fade_matte", "褪色哑光", "创意", "哑光褪色电影感"),
}


class StyleFilter:
    """风格化滤镜应用器"""

    def __init__(self, preset_name: str = "none", intensity: float = 1.0):
        """
        Args:
            preset_name: 滤镜名称
            intensity: 强度 0~1，0为原图
        """
        self.preset_name = preset_name
        self.intensity = intensity

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """应用滤镜"""
        if self.preset_name == "none" or self.intensity <= 0.01:
            return frame

        filter_fn = self._get_filter_fn(self.preset_name)
        if filter_fn is None:
            return frame

        filtered = filter_fn(frame)
        # 按强度混合
        if self.intensity >= 0.99:
            return filtered
        return cv2.addWeighted(frame, 1 - self.intensity, filtered, self.intensity, 0)

    def _get_filter_fn(self, name: str) -> Optional[Callable]:
        fns = {
            "cinematic_teal_orange": self._cinematic_teal_orange,
            "cinematic_warm": self._cinematic_warm,
            "cinematic_cool": self._cinematic_cool,
            "vintage_film": self._vintage_film,
            "vintage_sepia": self._vintage_sepia,
            "vintage_70s": self._vintage_70s,
            "fresh_clean": self._fresh_clean,
            "fresh_japanese": self._fresh_japanese,
            "bw_high_contrast": self._bw_high_contrast,
            "bw_silver": self._bw_silver,
            "bw_soft": self._bw_soft,
            "dreamy_glow": self._dreamy_glow,
            "noir": self._noir,
            "vivid": self._vivid,
            "fade_matte": self._fade_matte,
        }
        return fns.get(name)

    # ========== 电影类 ==========

    def _cinematic_teal_orange(self, img: np.ndarray) -> np.ndarray:
        """青橙电影色调：阴影偏青，高光偏橙"""
        f = img.astype(np.float32) / 255.0
        # 阴影偏青蓝
        shadow_mask = np.power(1 - f.mean(axis=2, keepdims=True), 1.5)
        f[:, :, 0] = np.clip(f[:, :, 0] + shadow_mask[:, :, 0] * 0.15, 0, 1)  # B
        f[:, :, 1] = np.clip(f[:, :, 1] + shadow_mask[:, :, 0] * 0.08, 0, 1)  # G
        # 高光偏橙
        hi_mask = np.power(f.mean(axis=2, keepdims=True), 1.5)
        f[:, :, 2] = np.clip(f[:, :, 2] + hi_mask[:, :, 0] * 0.12, 0, 1)  # R
        f[:, :, 1] = np.clip(f[:, :, 1] + hi_mask[:, :, 0] * 0.04, 0, 1)  # G
        # 整体S曲线增加对比
        f = np.clip(1.1 * (f - 0.5) + 0.5, 0, 1)
        return (f * 255).astype(np.uint8)

    def _cinematic_warm(self, img: np.ndarray) -> np.ndarray:
        f = img.astype(np.float32)
        f[:, :, 2] = np.clip(f[:, :, 2] * 1.1 + 10, 0, 255)  # R
        f[:, :, 1] = np.clip(f[:, :, 1] * 1.03 + 3, 0, 255)  # G
        f[:, :, 0] = np.clip(f[:, :, 0] * 0.92, 0, 255)      # B
        # 暗角
        f = self._apply_vignette(f, 0.15)
        return f.astype(np.uint8)

    def _cinematic_cool(self, img: np.ndarray) -> np.ndarray:
        f = img.astype(np.float32)
        f[:, :, 0] = np.clip(f[:, :, 0] * 1.12 + 8, 0, 255)  # B
        f[:, :, 1] = np.clip(f[:, :, 1] * 1.02, 0, 255)      # G
        f[:, :, 2] = np.clip(f[:, :, 2] * 0.93, 0, 255)      # R
        f = self._apply_vignette(f, 0.2)
        return f.astype(np.uint8)

    # ========== 复古类 ==========

    def _vintage_film(self, img: np.ndarray) -> np.ndarray:
        f = img.astype(np.float32)
        # 褪色
        f = f * 0.85 + 30
        # 偏黄
        f[:, :, 2] = np.clip(f[:, :, 2] * 1.08, 0, 255)
        f[:, :, 1] = np.clip(f[:, :, 1] * 1.02, 0, 255)
        f[:, :, 0] = np.clip(f[:, :, 0] * 0.88, 0, 255)
        # 颗粒
        noise = np.random.normal(0, 8, f.shape).astype(np.float32)
        f = np.clip(f + noise, 0, 255)
        # 暗角
        f = self._apply_vignette(f, 0.25)
        return f.astype(np.uint8)

    def _vintage_sepia(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sepia = np.zeros_like(img)
        sepia[:, :, 0] = np.clip(gray * 0.55, 0, 255)   # B
        sepia[:, :, 1] = np.clip(gray * 0.78, 0, 255)   # G
        sepia[:, :, 2] = np.clip(gray * 1.0, 0, 255)    # R
        return sepia

    def _vintage_70s(self, img: np.ndarray) -> np.ndarray:
        f = img.astype(np.float32)
        f[:, :, 2] = np.clip(f[:, :, 2] * 1.15 + 15, 0, 255)  # R
        f[:, :, 1] = np.clip(f[:, :, 1] * 0.95 + 5, 0, 255)   # G
        f[:, :, 0] = np.clip(f[:, :, 0] * 0.8, 0, 255)        # B
        # 降低对比
        f = f * 0.8 + 25
        return np.clip(f, 0, 255).astype(np.uint8)

    # ========== 清新类 ==========

    def _fresh_clean(self, img: np.ndarray) -> np.ndarray:
        f = img.astype(np.float32)
        # 提亮
        f = np.clip(f * 1.08 + 8, 0, 255)
        # 轻微提饱和
        hsv = cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.15, 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        return np.clip(result, 0, 255).astype(np.uint8)

    def _fresh_japanese(self, img: np.ndarray) -> np.ndarray:
        f = img.astype(np.float32)
        # 低饱和、高亮、偏冷
        hsv = cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 0.6, 0, 255)  # 低饱和
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        result = np.clip(result * 1.1 + 15, 0, 255)  # 高亮
        result[:, :, 0] = np.clip(result[:, :, 0] * 1.05, 0, 255)  # 偏蓝
        return result.astype(np.uint8)

    # ========== 黑白类 ==========

    def _bw_high_contrast(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 高对比曲线
        f = gray.astype(np.float32) / 255.0
        f = np.clip(1.4 * (f - 0.5) + 0.5, 0, 1)
        result = (f * 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    def _bw_silver(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        # 银盐感：中间调偏亮，暗部不死黑
        f = gray / 255.0
        f = np.power(f, 0.85) * 0.95 + 0.03
        result = np.clip(f * 255, 0, 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    def _bw_soft(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        f = gray / 255.0
        f = np.clip(0.8 * (f - 0.5) + 0.5, 0, 1)  # 低对比
        result = (f * 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    # ========== 创意类 ==========

    def _dreamy_glow(self, img: np.ndarray) -> np.ndarray:
        # 高斯模糊叠加（柔光效果）
        blur = cv2.GaussianBlur(img, (0, 0), 15)
        result = cv2.addWeighted(img, 0.6, blur, 0.4, 10)
        # 提亮
        result = np.clip(result.astype(np.float32) * 1.05 + 5, 0, 255).astype(np.uint8)
        return result

    def _noir(self, img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        f = gray / 255.0
        # 极端高对比
        f = np.clip(1.8 * (f - 0.45) + 0.45, 0, 1)
        # 暗角
        h, w = f.shape
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        vignette = 1 - 0.5 * (dist / max_dist) ** 2
        f = f * vignette
        result = (f * 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    def _vivid(self, img: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255)  # 高饱和
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        result = np.clip(result * 1.05, 0, 255).astype(np.uint8)
        return result

    def _fade_matte(self, img: np.ndarray) -> np.ndarray:
        f = img.astype(np.float32)
        # 哑光褪色：提升黑场，降低白场
        f = f * 0.82 + 22
        # 轻微偏青
        f[:, :, 0] = np.clip(f[:, :, 0] * 1.05, 0, 255)
        f[:, :, 2] = np.clip(f[:, :, 2] * 0.97, 0, 255)
        return np.clip(f, 0, 255).astype(np.uint8)

    # ========== 工具函数 ==========

    def _apply_vignette(self, img_float: np.ndarray, strength: float = 0.2) -> np.ndarray:
        """添加暗角"""
        h, w = img_float.shape[:2]
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        mask = 1 - strength * (dist / max_dist) ** 2
        mask = mask[:, :, np.newaxis]
        return img_float * mask
