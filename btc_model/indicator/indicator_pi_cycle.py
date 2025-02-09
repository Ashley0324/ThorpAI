import datetime
import numpy as np
import pandas as pd
import talib as ta

from btc_model.core.common.context import Context
from btc_model.indicator.base_indicator import BaseIndicator


class IndicatorPiCycle(BaseIndicator):
    """
    Pi Cycle通过比特币的200日移动平均线与111日移动平均线的交叉，
    帮助预测比特币价格的顶部和底部，常用于捕捉市场反转信号。

    当200日MA与111日MA交叉时，通常被视为价格反转的预兆。
    """
    _id = 'pi_cycle'
    _name = 'Pi Cycle'
    _description = 'Pi Cycle通过200日和111日移动平均线的交叉，预测比特币价格的顶部和底部。'

    _params = {
        'short_window': 111,
        'long_window': 350
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.short_window = kwargs.get('short_window', self._params['short_window'])
        self.long_window = kwargs.get('long_window', self._params['long_window'])

    def get_minimum_bars(self):
        """
        获取指标需要的最少bar数量
        :return:
        """
        return self.long_window

    def compute(self, context: Context, **kwargs):
        close_array = context.close_array

        ma_short = ta.SMA(close_array, timeperiod=self.short_window)
        ma_long = ta.SMA(close_array, timeperiod=self.long_window)

        if kwargs.get('expect_df', True):
            return pd.DataFrame({'_ma_short': ma_short, 'ma_long': ma_long})
        else:
            return ma_short, ma_long
