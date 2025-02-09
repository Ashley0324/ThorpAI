import talib as ta
import pandas as pd

from btc_model.core.common.context import Context
from btc_model.indicator.base_indicator import BaseIndicator


class IndicatorMayerMultiple(BaseIndicator):
    """
    Mayer Multiple通过比特币当前价格与其200日移动平均价格的比值，
    帮助评估比特币是否处于高估或低估状态，常用于判断市场的长期趋势。

    值较高时，可能表示市场高估；值较低时，可能表示市场低估。
    """
    _id = 'mayer_multiple'
    _name = '梅耶倍数'
    _description = '梅耶倍数通过比特币当前价格与200日移动平均的比值，评估市场的高估或低估状态。'


    _params = {
        'window': 200
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

        ma = ta.SMA(close_array, timeperiod=self.window)
        mayer_multiple = close_array / ma

        if kwargs.get('expect_df', True):
            return pd.DataFrame({'value': mayer_multiple})
        else:
            return mayer_multiple

