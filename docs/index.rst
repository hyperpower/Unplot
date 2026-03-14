Unplot 文档
===========

从图像中提取数据点的 PySide6 应用程序。

.. toctree::
   :maxdepth: 2
   :caption: 目录：

   用户指南 <user_guide>
   API 参考 <api_reference>
   开发指南 <development>

用户指南
========

安装
----

.. code-block:: bash

   pip install -r requirements.txt

运行
----

.. code-block:: bash

   python src/main.py

主要功能
--------

- 支持常见图像格式（PNG, JPG, BMP 等）
- 坐标轴校准
- 数据点提取
- 数据导出（CSV, Excel）

API 参考
========

.. autosummary::
   :toctree: generated

   src.core
   src.ui
   src.utils

开发指南
========

贡献代码
--------

欢迎提交 Pull Request！

运行测试
--------

.. code-block:: bash

   pytest tests/

构建文档
--------

.. code-block:: bash

   cd docs
   make html

索引和表格
==========

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`