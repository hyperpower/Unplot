# Unplot

从图像中提取数据点的 PySide6 应用程序。

## 功能特性

- 支持常见图像格式（PNG, JPG, BMP 等）
- 坐标轴校准：设置 X/Y 轴的最小/最大值
- 数据点提取：手动点击或自动检测曲线/散点
- 实时数据预览
- 支持导出 CSV、Excel 格式

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python src/main.py
```

## 项目结构

```
Unplot/
├── src/              # 源代码
│   ├── core/         # 核心功能模块
│   ├── ui/           # 用户界面模块
│   └── utils/        # 工具模块
├── docs/             # Sphinx 文档
├── tests/            # 测试文件
└── assets/           # 资源文件
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 构建文档

```bash
cd docs
make html
```

## 许可证

MIT License