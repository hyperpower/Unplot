"""
数据导出模块
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Union
from pathlib import Path


class DataExporter:
    """数据导出器类
    
    支持将提取的数据导出为多种格式：CSV, Excel, JSON 等。
    """
    
    SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xls', '.json', '.txt']
    
    def __init__(self):
        pass
    
    def export(self, x_data: Union[List, np.ndarray],
               y_data: Union[List, np.ndarray],
               file_path: str,
               format: Optional[str] = None,
               **kwargs) -> bool:
        """导出数据到文件
        
        Args:
            x_data: X 数据数组
            y_data: Y 数据数组
            file_path: 输出文件路径
            format: 导出格式，如果为 None 则从文件扩展名推断
            **kwargs: 额外参数传递给具体的导出函数
            
        Returns:
            bool: 导出是否成功
        """
        x = np.array(x_data)
        y = np.array(y_data)
        
        if len(x) != len(y):
            raise ValueError("X 和 Y 数据长度不一致")
        
        if len(x) == 0:
            raise ValueError("数据为空")
        
        # 确定格式
        if format is None:
            ext = Path(file_path).suffix.lower()
            if ext not in self.SUPPORTED_FORMATS:
                format = '.csv'
            else:
                format = ext
        
        # 导出
        try:
            if format == '.csv':
                return self._export_csv(x, y, file_path, **kwargs)
            elif format in ['.xlsx', '.xls']:
                return self._export_excel(x, y, file_path, **kwargs)
            elif format == '.json':
                return self._export_json(x, y, file_path, **kwargs)
            elif format == '.txt':
                return self._export_txt(x, y, file_path, **kwargs)
            else:
                return self._export_csv(x, y, file_path + '.csv', **kwargs)
        except Exception as e:
            print(f"导出失败：{e}")
            return False
    
    def _export_csv(self, x: np.ndarray, y: np.ndarray,
                    file_path: str, **kwargs) -> bool:
        """导出为 CSV 格式"""
        df = pd.DataFrame({"X": x, "Y": y})
        
        # 默认参数
        if 'index' not in kwargs:
            kwargs['index'] = False
        if 'float_format' not in kwargs:
            kwargs['float_format'] = '%.10f'
        
        df.to_csv(file_path, **kwargs)
        return True
    
    def _export_excel(self, x: np.ndarray, y: np.ndarray,
                      file_path: str, **kwargs) -> bool:
        """导出为 Excel 格式"""
        df = pd.DataFrame({"X": x, "Y": y})
        
        # 默认参数
        if 'index' not in kwargs:
            kwargs['index'] = False
        
        df.to_excel(file_path, **kwargs)
        return True
    
    def _export_json(self, x: np.ndarray, y: np.ndarray,
                     file_path: str, **kwargs) -> bool:
        """导出为 JSON 格式"""
        data = {
            "x": x.tolist(),
            "y": y.tolist()
        }
        
        df = pd.DataFrame(data)
        df.to_json(file_path, **kwargs)
        return True
    
    def _export_txt(self, x: np.ndarray, y: np.ndarray,
                    file_path: str, **kwargs) -> bool:
        """导出为文本格式（空格分隔）"""
        with open(file_path, 'w') as f:
            # 写入表头
            if 'header' not in kwargs or kwargs.get('header', True):
                f.write("# X Y\n")
            
            # 写入数据
            for xi, yi in zip(x, y):
                f.write(f"{xi:.10f} {yi:.10f}\n")
        
        return True
    
    def export_with_metadata(self, x_data: Union[List, np.ndarray],
                              y_data: Union[List, np.ndarray],
                              file_path: str,
                              metadata: Optional[dict] = None) -> bool:
        """导出数据（包含元数据）
        
        Args:
            x_data: X 数据数组
            y_data: Y 数据数组
            file_path: 输出文件路径
            metadata: 元数据字典，可包含来源图像、坐标轴范围等信息
            
        Returns:
            bool: 导出是否成功
        """
        x = np.array(x_data)
        y = np.array(y_data)
        
        ext = Path(file_path).suffix.lower()
        
        if ext == '.json':
            data = {
                "metadata": metadata or {},
                "data": {
                    "x": x.tolist(),
                    "y": y.tolist()
                }
            }
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        else:
            # 对于其他格式，忽略元数据
            return self.export(x, y, file_path)