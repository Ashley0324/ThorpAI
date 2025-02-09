import datetime

import pandas as pd
import talib

from abc import ABC

from btc_model.core.common.context import Context
from btc_model.indicator.base_indicator import BaseIndicator


class IndicatorBollinger(BaseIndicator):
    """
    布林带通过价格的移动平均线和标准差，帮助识别市场的波动性和超买/超卖状态。
    常用于捕捉价格的过度波动和反转信号。

    当价格突破上轨或下轨时，可能表示市场过热或过冷。
    """
    _id = 'boll'
    _name = '布林带'
    _description = '布林带通过移动平均线和标准差，帮助识别市场波动性和超买/超卖状态。'

    _params = {
        'window': 100,
        'nbdev': 2.5
    }

    _return = ('upper', 'middle', 'lower')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.window = kwargs.get('window', self._params['window'])
        self.nbdev = kwargs.get('nbdev', self._params['nbdev'])

    def get_minimum_bars(self):
        """
        获取指标需要的最少bar数量
        :return:
        """
        return self.window

    def compute(self, context: Context, **kwargs):
        close_array = context.close_array

        upper_band, middle_band, lower_band = talib.BBANDS(close_array,
                                                           timeperiod=self.window,
                                                           nbdevup=self.nbdev,
                                                           nbdevdn=self.nbdev,
                                                           matype=0
                                                           )

        if kwargs.get('expect_df', True):
            return pd.DataFrame({'upper': upper_band, 'middle': middle_band, 'lower': lower_band})
        else:
            return upper_band, middle_band, lower_band


if __name__ == '__main__':
    indicator = IndicatorBollinger()
    result = indicator.tag()
    print(result)
    result = indicator.get_indicator_info()
    print(result)
