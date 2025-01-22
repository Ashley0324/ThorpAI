# -*- coding: utf-8 -*-
"""
Author: guozq

Create Date: 2025/01/19

Description:

"""
import datetime
import talib

from abc import ABC

from btc_model.core.common.context import Context
from btc_model.indicator.BaseIndicator import BaseIndicator


class IndicatorRSI(BaseIndicator):
    __params = {
        'window': 14
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.window = kwargs.get('window', self.__params['window'])

    def compute(self, context: Context=None):
        close_array = context.close_array

        rsi = talib.RSI(close_array, timeperiod=self.window)

        return rsi


