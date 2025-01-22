# -*- coding: utf-8 -*-
"""
Author: guozq

Create Date: 2025/01/19

Description:

"""
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
    _author: str

    def __init__(self, **kwargs):
        pass

    def compute(self, context: Context):
        pass

    def get_indicator_info(self):
        return {'id': self._id,
                'name': self._name,

                'description': self._description,
                'author': self._author,
                }
