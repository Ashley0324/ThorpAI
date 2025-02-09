import datetime
import talib
import pandas as pd

from abc import ABC

from btc_model.core.common.context import Context
from btc_model.indicator.base_indicator import BaseIndicator


class IndicatorRSI(BaseIndicator):
    """

    """
    _id = 's2f'
    _name = '相对强弱指数'
    _description = 'RSI通过测量价格上涨与下跌的力度，评估市场是否超买或超卖。'

    _params = {
        'window': 14
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.window = kwargs.get('window', self._params['window'])

    def get_minimum_bars(self):
        """
        获取指标需要的最少bar数量
        :return:
        """
        return self.window

    def compute(self, context: Context, **kwargs):
        close_array = context.close_array

        rsi = talib.RSI(close_array, timeperiod=self.window)

        if kwargs.get('expect_df', True):
            return pd.DataFrame({'value': rsi})
        else:
            return rsi





