import datetime
from abc import ABC

from btc_model.core.common.context import Context


class BaseIndicator(ABC):
    """
    指标基础类
    """
    _id: str
    _name: str
    _description: str

    _params = {
    }

    _return = ()

    def __init__(self, **kwargs):
        pass

    def compute(self, context: Context, **kwargs):
        pass

    def tag(self):
        """
        动态生成用于存储的列名，使用 '@' 替代小数点和其他分隔符。
        格式：indicator_param1_param2_...
        """
        column_name = self._id
        for value in self._params.values():
            # 将小数点替换为 '@'，确保列名简洁且不含特殊符号
            value_str = str(value).replace('.', '@')
            column_name += f"_{value_str}"

        return column_name

    def get_minimum_bars(self):
        pass

    def get_indicator_info(self):
        return {'id': self._id,
                'name': self._name,
                'description': self._description
                }
