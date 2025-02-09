import datetime
import talib
import pandas as pd
from abc import ABC

from btc_model.core.common.context import Context
from btc_model.indicator.base_indicator import BaseIndicator


class IndicatorMACD(BaseIndicator):
    """
    MACD通过计算短期和长期移动平均线的差值，识别市场的趋势和反转信号。
    常用于判断市场的强弱和潜在的价格反转点。

    当MACD线突破信号线时，通常视为买入信号；反之，则为卖出信号。
    """
    _id = 'macd'
    _name = '移动平均收敛/发散指标'
    _description = 'MACD通过短期与长期移动平均线的差值，识别市场趋势和反转信号。'

    _params = {
        'fast_period': 16,
        'slow_period': 26,
        'signal_period': 9
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fast_period = kwargs.get('fast_period', self._params['fast_period'])
        self.slow_period = kwargs.get('slow_period', self._params['slow_period'])
        self.signal_period = kwargs.get('signal_period', self._params['signal_period'])

    def get_minimum_bars(self):
        """
        获取指标需要的最少bar数量
        :return:
        """
        return self.slow_period


    def compute(self, context: Context, **kwargs):
        close_array = context.close_array


        dif, dea, hist = talib.MACD(close_array,
                                        fastperiod=self.fast_period,
                                        slowperiod=self.slow_period,
                                        signalperiod=self.signal_period)

        if kwargs.get('expect_df', True):
            # dif --> macd, dea --> signal, same meaning
            return pd.DataFrame({'dif': dif, 'dea': dea, 'hist': hist})
        else:
            return dif, dea, hist


