"""
Pipeline 与 image step 执行测试。
"""

import sys
from pathlib import Path

import pytest

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.image_process import (
    ImageLoader,
    ImageNormalizer,
    ImageWriter,
    LayoutDetector,
    OrientationDetector,
    PageDewarper,
    PerspectiveCorrector,
    ROIExtractor,
)
from core.pipeline import Pipeline, PipelineContext, StepRegistry


@pytest.fixture
def image_path() -> Path:
    """返回测试图片路径。"""
    path = Path(__file__).parent / "images" / "image_001.jpg"
    assert path.exists()
    return path


@pytest.fixture
def loaded_image(image_path: Path):
    """加载测试图片。"""
    loader = ImageLoader()
    assert loader.load(str(image_path)) is True
    assert loader.image is not None
    return loader.image


class TestImageStepRun:
    """测试各个 image step 的 run(context) 路径。"""

    def test_image_loader_describes_contract(self):
        step = ImageLoader()

        input_names = [port.name for port in step.describe_inputs()]
        output_names = [port.name for port in step.describe_outputs()]
        config_names = [field.name for field in step.describe_config()]

        assert input_names == ["path"]
        assert output_names == ["image"]
        assert config_names == ["status", "width", "height"]

    def test_image_loader_run_sets_context(self, image_path: Path):
        step = ImageLoader(config={"path": str(image_path)})
        context = PipelineContext()

        step.run(context)

        assert context.get("image") is not None
        assert step.image_path == str(image_path)

    def test_image_loader_run_requires_configured_path(self):
        step = ImageLoader()
        context = PipelineContext()

        with pytest.raises(ValueError, match="缺少图像路径"):
            step.run(context)

    def test_image_loader_is_ready_requires_existing_readable_path(self, image_path: Path):
        assert ImageLoader().is_ready() is False
        assert ImageLoader(config={"path": "tests/images/missing.jpg"}).is_ready() is False
        assert ImageLoader(config={"path": str(image_path)}).is_ready() is True

    def test_image_loader_inputs_check_reports_missing_or_invalid_path(self, image_path: Path):
        assert ImageLoader().inputs_check() == ["请输入图像文件路径"]
        assert ImageLoader(config={"path": "tests/images/missing.jpg"}).inputs_check() == [
            "图像文件不存在: tests/images/missing.jpg"
        ]
        assert ImageLoader(config={"path": str(image_path)}).inputs_check() == []

    def test_image_normalizer_run_sets_result(self, loaded_image):
        step = ImageNormalizer()
        context = PipelineContext(data={"image": loaded_image})

        step.run(context)

        result = context.get("normalization_result")
        assert result is not None
        assert result.normalized_image.ndim == 3
        assert context.get("image") is result.normalized_image

    def test_orientation_detector_run_sets_result(self, loaded_image):
        step = OrientationDetector()
        context = PipelineContext(data={"image": loaded_image})

        step.run(context)

        result = context.get("orientation_result")
        assert result is not None
        assert result.image.ndim == 3
        assert isinstance(result.success, bool)
        assert context.get("image") is result.image

    def test_perspective_corrector_run_sets_result(self, loaded_image):
        step = PerspectiveCorrector()
        context = PipelineContext(data={"image": loaded_image})

        step.run(context)

        result = context.get("perspective_result")
        assert result is not None
        assert result.image.ndim == 3
        assert isinstance(result.success, bool)
        assert context.get("image") is result.image

    def test_layout_detector_run_sets_result(self, loaded_image):
        step = LayoutDetector()
        context = PipelineContext(data={"image": loaded_image})

        step.run(context)

        result = context.get("layout_result")
        assert result is not None
        assert result.image.ndim == 3
        assert isinstance(result.regions, list)
        assert context.get("layout_debug_image") is result.debug_image

    def test_roi_extractor_run_sets_result(self, loaded_image):
        layout_detector = LayoutDetector()
        layout_context = PipelineContext(data={"image": loaded_image})
        layout_detector.run(layout_context)

        step = ROIExtractor()
        context = PipelineContext(
            data={
                "image": loaded_image,
                "layout_result": layout_context.get("layout_result"),
            }
        )

        step.run(context)

        result = context.get("roi_result")
        assert result is not None
        assert isinstance(result.success, bool)
        if result.success:
            assert context.get("plot_roi") is result.plot_roi
            assert context.get("x_axis_roi") is result.x_axis_roi
            assert context.get("y_axis_roi") is result.y_axis_roi

    def test_page_dewarper_run_sets_result(self, loaded_image):
        step = PageDewarper()
        context = PipelineContext(data={"image": loaded_image})

        step.run(context)

        result = context.get("dewarp_result")
        assert result is not None
        assert result.image.ndim == 3
        assert result.success is True
        assert context.get("image") is result.image

    def test_image_writer_run_saves_output(self, loaded_image, tmp_path: Path):
        output_path = tmp_path / "pipeline_output.jpg"
        step = ImageWriter(config={"path": str(output_path)})
        context = PipelineContext(data={"image": loaded_image})

        step.run(context)

        assert output_path.exists()
        assert context.get("save_success") is True


class TestPipelineExecution:
    """测试 Pipeline 本身的执行能力。"""

    def test_pipeline_runs_multiple_steps(self, image_path: Path):
        pipeline = Pipeline(
            name="image processing",
            steps=[
                ImageLoader(config={"path": str(image_path)}),
                ImageNormalizer(),
                OrientationDetector(),
                PageDewarper(),
            ],
        )

        result = pipeline.run()

        assert result.success is True
        assert result.pipeline_name == "image processing"
        assert len(result.records) == 4
        assert all(record.success for record in result.records)
        assert result.context.get("image") is not None
        assert result.context.get("normalization_result") is not None
        assert result.context.get("orientation_result") is not None
        assert result.context.get("dewarp_result") is not None

    def test_pipeline_skips_disabled_step(self, image_path: Path):
        pipeline = Pipeline(
            name="image processing",
            steps=[
                ImageLoader(config={"path": str(image_path)}),
                ImageNormalizer(enabled=False),
            ],
        )

        result = pipeline.run()

        assert result.success is True
        assert len(result.records) == 2
        assert result.records[1].skipped is True
        assert result.context.get("normalization_result") is None

    def test_pipeline_from_dict_uses_registry(self, image_path: Path):
        payload = {
            "name": "image processing",
            "steps": [
                {
                    "type": "ImageLoader",
                    "name": "load-image",
                    "config": {"path": str(image_path)},
                },
                {
                    "type": "ImageNormalizer",
                    "name": "normalize-image",
                },
                {
                    "type": "PageDewarper",
                    "name": "dewarp-page",
                },
            ],
        }

        pipeline = Pipeline.from_dict(payload)
        result = pipeline.run()

        assert pipeline.name == "image processing"
        assert [step.name for step in pipeline.steps] == [
            "load-image",
            "normalize-image",
            "dewarp-page",
        ]
        assert result.success is True
        assert result.context.get("dewarp_result") is not None

    def test_image_steps_are_auto_registered(self):
        registered_types = StepRegistry.get_registered_types()

        assert "ImageLoader" in registered_types
        assert "ImageNormalizer" in registered_types
        assert "ImageWriter" in registered_types
        assert "OrientationDetector" in registered_types
        assert "PerspectiveCorrector" in registered_types
        assert "LayoutDetector" in registered_types
        assert "ROIExtractor" in registered_types
        assert "PageDewarper" in registered_types
