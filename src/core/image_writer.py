"""
图像保存模块
"""

import os
from typing import Optional

import cv2
import numpy as np

class ImageWriter:
    """图像保存器类
    
    负责将图像保存到硬盘，支持常见格式如 PNG, JPG, BMP, TIFF 等。
    """

    SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]

    def save(
        self,
        image: np.ndarray,
        path: str,
        quality: Optional[int] = 95,
    ) -> bool:
        """保存图像到指定路径
        
        Args:
            image: 要保存的图像，支持灰度图或 RGB 图
            path: 输出文件路径
            quality: JPEG 质量，范围通常为 0-100
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if image is None or image.size == 0:
                raise ValueError("输入图像不能为空")

            ext = os.path.splitext(path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                raise ValueError(f"不支持的图像格式：{ext}")

            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

            image_to_save = self._prepare_image_for_save(image)
            params = self._get_save_params(ext, quality)

            success = cv2.imwrite(path, image_to_save, params)
            if not success:
                raise ValueError("图像写入失败")

            return True

        except Exception as e:
            print(f"保存图像失败：{e}")
            return False

    def _prepare_image_for_save(self, image: np.ndarray) -> np.ndarray:
        """将输入图像转换为适合 OpenCV 保存的格式"""
        if image.dtype != np.uint8:
            image = self._convert_to_uint8(image)

        if image.ndim == 2:
            return image

        if image.ndim == 3 and image.shape[2] == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if image.ndim == 3 and image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)

        raise ValueError("不支持的图像格式")

    def _convert_to_uint8(self, image: np.ndarray) -> np.ndarray:
        """将图像转换为 uint8"""
        clipped = np.clip(image, 0, None)

        if clipped.size == 0:
            raise ValueError("输入图像不能为空")

        max_value = float(np.max(clipped))
        if max_value <= 1.0:
            clipped = clipped * 255.0
        elif max_value > 255.0:
            clipped = clipped / max_value * 255.0

        return clipped.astype(np.uint8)

    def _get_save_params(self, ext: str, quality: Optional[int]) -> list[int]:
        """根据文件格式生成保存参数"""
        if ext in [".jpg", ".jpeg"]:
            jpeg_quality = 95 if quality is None else max(0, min(100, int(quality)))
            return [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]

        if ext == ".png":
            compression = 3
            return [cv2.IMWRITE_PNG_COMPRESSION, compression]

        return []