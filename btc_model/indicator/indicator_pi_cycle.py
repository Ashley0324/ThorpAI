# -*- coding: utf-8 -*-
"""
Author: guozq

Create Date: 2025/01/19

Description:

"""
import datetime
import numpy as np
from abc import ABC
import talib as ta

from btc_model.core.common.context import Context
from btc_model.indicator.BaseIndicator import BaseIndicator


class IndicatorPiCycle(BaseIndicator, ABC):
    __params = {
        'short_window': 111,
        'long_window': 350
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.short_window = kwargs.get('short_window', self.__params['short_window'])
        self.long_window = kwargs.get('long_window', self.__params['long_window'])

    def compute(self, context: Context):
        close_array = context.close_array

        ma_short = ta.SMA(close_array, timeperiod=self.short_window)
        ma_long = ta.SMA(close_array, timeperiod=self.long_window)

        if ma_short[-1] > 2 * ma_long[-1]:
            return True
        else:
            return False
