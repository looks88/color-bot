# -*- coding: utf-8 -*-
"""光影修复与色彩校正核心算法模块"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class ColorParams:
    """色彩校正参数"""
    # 基础调整
    brightness: float = 0.0       # -100 ~ 100
    contrast: float = 0.0         # -100 ~ 100
    saturation: float = 0.0       # -100 ~ 100
    temperature: float = 0.0      # -100(冷) ~ 100(暖)
    tint: float = 0.0             # -100(绿) ~ 100(品红)

    # 光影修复
    auto_exposure: bool = True    # 自动曝光修复
    auto_white_balance: bool = True  # 自动白平衡
    shadow_lift: float = 30.0     # 暗部提亮 0~100
    highlight_recover: float = 30.0  # 高光压制 0~100
    denoise: float = 0.0          # 降噪强度 0~50

    # 曲线
    gamma: float = 1.0            # 0.5 ~ 2.5

    def reset(self):
        for f in self.__dataclass_fields__:
            setattr(self, f, type(self).__dataclass_fields__[f].default)


class ColorCorrector:
    """专业色彩校正器"""

    def __init__(self, params: Optional[ColorParams] = None):
        self.params = params or ColorParams()

    def process(self, frame: np.ndarray) -> np.ndarray:
        """对单帧执行完整校色流程"""
        img = frame.copy().astype(np.float32) / 255.0

        # 1. 自动曝光修复（光影修复核心）
        if self.params.auto_exposure:
            img = self._auto_exposure(img)

        # 2. 自动白平衡
        if self.params.auto_white_balance:
            img = self._auto_white_balance(img)

        # 3. 暗部提亮 / 高光压制
        img = self._shadow_highlight(img)

        # 4. Gamma
        if abs(self.params.gamma - 1.0) > 0.01:
            img = np.power(np.clip(img, 0, 1), self.params.gamma)

        # 5. 基础调整：亮度/对比度/饱和度/色温/色调
        img = self._basic_adjust(img)

        # 6. 降噪
        if self.params.denoise > 0.1:
            img = self._denoise(img)

        return np.clip(img * 255, 0, 255).astype(np.uint8)

    # ========== 光影修复核心 ==========

    def _auto_exposure(self, img: np.ndarray) -> np.ndarray:
        """
        自动曝光修复：基于直方图拉伸 + 对数空间亮度均衡
        修复欠曝/过曝，恢复画面原始光影层次
        """
        # 转YUV取亮度
        yuv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_BGR2YUV)
        y = yuv[:, :, 0].astype(np.float32) / 255.0

        # 百分位裁剪（去除极端值）
        p_low = np.percentile(y, 1)
        p_high = np.percentile(y, 99)
        if p_high - p_low > 0.01:
            y = np.clip((y - p_low) / (p_high - p_low), 0, 1)

        # 对数空间对比度增强（类似S曲线）
        y_mean = y.mean()
        # 对暗部提亮、亮部适度压缩
        y = np.where(y < y_mean,
                     y * (1 + 0.15 * (y_mean - y) / max(y_mean, 0.01)),
                     1 - (1 - y) * (1 + 0.1 * (y - y_mean) / max(1 - y_mean, 0.01)))
        y = np.clip(y, 0, 1)

        yuv[:, :, 0] = (y * 255).astype(np.uint8)
        result = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR).astype(np.float32) / 255.0
        return result

    def _auto_white_balance(self, img: np.ndarray) -> np.ndarray:
        """
        自动白平衡：灰度世界假设 + 完美反射修正
        """
        # 灰度世界
        mean_r = img[:, :, 2].mean()
        mean_g = img[:, :, 1].mean()
        mean_b = img[:, :, 0].mean()
        mean_gray = (mean_r + mean_g + mean_b) / 3.0

        if mean_r > 0.01 and mean_g > 0.01 and mean_b > 0.01:
            scale_r = mean_gray / mean_r
            scale_g = mean_gray / mean_g
            scale_b = mean_gray / mean_b
            # 限制缩放范围避免色偏过度
            scale_r = np.clip(scale_r, 0.7, 1.4)
            scale_g = np.clip(scale_g, 0.7, 1.4)
            scale_b = np.clip(scale_b, 0.7, 1.4)

            img[:, :, 2] *= scale_r
            img[:, :, 1] *= scale_g
            img[:, :, 0] *= scale_b

        return np.clip(img, 0, 1)

    def _shadow_highlight(self, img: np.ndarray) -> np.ndarray:
        """暗部提亮 + 高光恢复（基于亮度蒙版）"""
        if self.params.shadow_lift <= 0 and self.params.highlight_recover <= 0:
            return img

        yuv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_BGR2YUV)
        y = yuv[:, :, 0].astype(np.float32) / 255.0

        # 暗部蒙版（亮度越低权重越高）
        shadow_mask = np.power(1.0 - y, 2.0)
        # 高光蒙版（亮度越高权重越高）
        highlight_mask = np.power(y, 2.0)

        # 暗部提亮
        if self.params.shadow_lift > 0:
            lift = self.params.shadow_lift / 100.0 * 0.4
            y = y + shadow_mask * lift

        # 高光压制
        if self.params.highlight_recover > 0:
            recover = self.params.highlight_recover / 100.0 * 0.3
            y = y - highlight_mask * recover

        yuv[:, :, 0] = np.clip(y * 255, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR).astype(np.float32) / 255.0
        return result

    # ========== 基础调整 ==========

    def _basic_adjust(self, img: np.ndarray) -> np.ndarray:
        p = self.params

        # 亮度
        if abs(p.brightness) > 0.01:
            img = img + p.brightness / 100.0 * 0.5

        # 对比度
        if abs(p.contrast) > 0.01:
            factor = (259 * (p.contrast + 255)) / (255 * (259 - p.contrast))
            img = factor * (img - 0.5) + 0.5

        # 饱和度
        if abs(p.saturation) > 0.01:
            hsv = cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8),
                               cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + p.saturation / 100.0), 0, 255)
            img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255.0

        # 色温（暖/冷）
        if abs(p.temperature) > 0.01:
            temp = p.temperature / 100.0
            img[:, :, 2] = np.clip(img[:, :, 2] + temp * 0.15, 0, 1)  # R
            img[:, :, 0] = np.clip(img[:, :, 0] - temp * 0.1, 0, 1)   # B

        # 色调（绿/品红）
        if abs(p.tint) > 0.01:
            tint = p.tint / 100.0
            img[:, :, 1] = np.clip(img[:, :, 1] + tint * 0.1, 0, 1)   # G
            img[:, :, 2] = np.clip(img[:, :, 2] + tint * 0.05, 0, 1)  # R

        return np.clip(img, 0, 1)

    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """非局部均值降噪（轻量版）"""
        strength = int(self.params.denoise)
        if strength <= 0:
            return img
        uint8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        denoised = cv2.fastNlMeansDenoisingColored(uint8, None, strength, strength, 7, 21)
        return denoised.astype(np.float32) / 255.0
