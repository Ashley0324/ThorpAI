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


class IndicatorMACD(BaseIndicator):
    __params = {
        'fast_period': 12,
        'slow_period': 5,
        'signal_period': 9
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fast_period = kwargs.get('fast_period', self.__params['fast_period'])
        self.slow_period = kwargs.get('slow_period', self.__params['slow_period'])
        self.signal_period = kwargs.get('signal_period', self.__params['signal_period'])

    def compute(self, context: Context):
        close_array = context.close_array

        macd, signal, hist = talib.MACD(close_array,
                                        fastperiod=self.fast_period,
                                        slowperiod=self.slow_period,
                                        signalperiod=self.signal_period)

        return macd, signal, hist

