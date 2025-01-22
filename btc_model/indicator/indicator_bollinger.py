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


class IndicatorBollinger(BaseIndicator):
    _params = {
        'window': 100,
        'nbdev': 2.5
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.window = kwargs.get('window', self._params['window'])
        self.nbdev = kwargs.get('nbdev', self._params['nbdev'])

    def compute(self, context: Context):
        close_array = context.close_array

        upper_band, middle_band, lower_band = talib.BBANDS(close_array,
                                                           timeperiod=self.window,
                                                           nbdevup=self.nbdev,
                                                           nbdevdn=self.nbdev,
                                                           matype=0
                                                           )

        return upper_band, middle_band, lower_band
