"""
批量导出 core 图像处理结果
"""

import sys
from pathlib import Path


# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.image_loader import ImageLoader
from core.image_writer import ImageWriter
from core.image_normalizer import ImageNormalizer
from core.layout_detector import LayoutDetector
from core.orientation_detector import OrientationDetector
from core.page_dewarper import PageDewarper
from core.perspective_corrector import PerspectiveCorrector
from core.roi_extractor import ROIExtractor

INPUT_DIR = Path(__file__).parent / "images"
OUTPUT_DIR = Path(__file__).parent / "output"

def process_single_image(image_path: Path) -> None:
    """处理单张图片并导出中间结果"""
    loader = ImageLoader()
    writer = ImageWriter()
    normalizer = ImageNormalizer()
    orientation_detector = OrientationDetector()
    perspective_corrector = PerspectiveCorrector()
    layout_detector = LayoutDetector()
    roi_extractor = ROIExtractor()
    dewarper = PageDewarper()

    if not loader.load(str(image_path)):
        print(f"[FAIL] load: {image_path.name}")
        return

    source_image = loader.image
    if source_image is None:
        print(f"[FAIL] image none: {image_path.name}")
        return

    image_output_dir = OUTPUT_DIR / image_path.stem
    image_output_dir.mkdir(parents=True, exist_ok=True)

    writer.save(source_image, str(image_output_dir / "source.jpg"))

    normalized = normalizer.normalize(source_image)
    writer.save(normalized.normalized_image, str(image_output_dir / "normalized.jpg"))
    writer.save(normalized.grayscale_image, str(image_output_dir / "grayscale.jpg"))
    writer.save(normalized.enhanced_image, str(image_output_dir / "enhanced.jpg"))

    orientation = orientation_detector.detect_and_correct(normalized.normalized_image)
    writer.save(orientation.image, str(image_output_dir / "oriented.jpg"))

    perspective = perspective_corrector.correct(orientation.image)
    writer.save(perspective.image, str(image_output_dir / "perspective.jpg"))

    layout = layout_detector.detect(perspective.image)
    writer.save(layout.debug_image, str(image_output_dir / "layout_debug.jpg"))

    if layout.success:
        roi = roi_extractor.extract(perspective.image, layout)
        if roi.plot_roi is not None:
            writer.save(roi.plot_roi, str(image_output_dir / "plot_roi.jpg"))
        if roi.x_axis_roi is not None:
            writer.save(roi.x_axis_roi, str(image_output_dir / "x_axis_roi.jpg"))
        if roi.y_axis_roi is not None:
            writer.save(roi.y_axis_roi, str(image_output_dir / "y_axis_roi.jpg"))
        if roi.legend_roi is not None:
            writer.save(roi.legend_roi, str(image_output_dir / "legend_roi.jpg"))

    dewarp = dewarper.dewarp(perspective.image)
    writer.save(dewarp.image, str(image_output_dir / "dewarp.jpg"))

    summary_lines = [
        f"input={image_path.name}",
        f"orientation_success={orientation.success}",
        f"orientation_angle={orientation.angle}",
        f"perspective_success={perspective.success}",
        f"layout_success={layout.success}",
        f"layout_region_count={len(layout.regions)}",
        f"dewarp_success={dewarp.success}",
        f"dewarp_method={dewarp.method}",
    ]
    (image_output_dir / "summary.txt").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print(f"[OK] {image_path.name} -> {image_output_dir}")

def main() -> None:
    """主入口"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image_files = [
        path for path in sorted(INPUT_DIR.iterdir())
        if path.is_file() and path.suffix.lower() in ImageLoader.SUPPORTED_FORMATS
    ]

    if not image_files:
        print("tests/images 中没有可处理的图片")
        return

    for image_path in image_files:
        process_single_image(image_path)

if __name__ == "__main__":
    main()