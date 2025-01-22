# -*- coding: utf-8 -*-
"""
Author: guozq

Create Date: 2025/01/19

Description:

"""
import talib as ta


from btc_model.core.common.context import Context
from btc_model.indicator.BaseIndicator import BaseIndicator


class IndicatorMayerMultiple(BaseIndicator):
    __params = {
        'window': 200
    }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.window = kwargs.get('window', self.__params['window'])

    def compute(self, context: Context):
        close_array = context.close_array

        ma = ta.SMA(close_array, timeperiod=self.window)
        mayer_multiple = close_array[-1] / ma[-1]

        if mayer_multiple > 2.4:
            return True
        else:
            return False

