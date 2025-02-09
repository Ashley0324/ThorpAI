import datetime

from btc_model.core.wrapper.okx_api_wrapper import OKxApiWrapper
from btc_model.core.wrapper.bitcoin_data_api_wrapper import BitcoinDataApiWrapper
from btc_model.core.wrapper.alternative_api_wrapper import AlternativeApiWrapper
from btc_model.setting.setting import get_settings
from btc_model.indicator.indicator_pi_cycle import IndicatorPiCycle
from btc_model.indicator.indicator_mayer_multiple import IndicatorMayerMultiple
from btc_model.indicator.indicator_bollinger import IndicatorBollinger
from btc_model.indicator.indicator_rsi import IndicatorRSI
from btc_model.indicator.indicator_macd import IndicatorMACD

from btc_model.core.common.context import Context


class EscapeModel:
    def __init__(self, **kwargs):

        setting = kwargs.get('setting', {})

        self.pi_cycle_short_window = setting.get('pi_cycle.short_window', 111)
        self.pi_cycle_long_window = setting.get('pi_cycle.long_window', 350)

        self.mvrv_zscore_threshold = setting.get('mvrv_zscore.threshold', 8)

        self.mayer_window = setting.get('mayer_multiple.window', 200)
        self.mayer_threshold = setting.get('mayer_multiple.threshold', 2.4)

        self.feargreed_threshold = setting.get('feargreed.threshold', 80)

        self.rsi_window = setting.get('rsi.window', 14)
        self.rsi_upper = setting.get('rsi.upper', 70)
        self.rsi_lower = setting.get('rsi.lower', 30)

        self.macd_fast_period = setting.get('macd.fast_period', 12)
        self.macd_slow_period = setting.get('macd.slow_period', 26)
        self.macd_signal_period = setting.get('macd.signal_period', 9)

        self.sth_mvrv_threshold = setting.get('sth_mvrv.threshold', 2)

        self.bollinger_window = setting.get('bollinger.window', 100)
        self.bollinger_nbdev = setting.get('bollinger.nbdev', 2.5)

        self.kline_data = None
        self.close_array = None
        self.sth_mvrv_data = None
        self.mvrv_zscore_data = None
        self.feargreed_data = None

        setting = get_settings('common')
        self._proxies = setting['proxies']

        setting = get_settings('cex.okx')
        self._apikey = setting['apikey']
        self._secretkey = setting['secretkey']
        self._passphrase = setting['passphrase']
        self._proxy = setting['proxy']

        self.OKxApi = OKxApiWrapper.get_instance(apikey=self._apikey,
                                                 secretkey=self._secretkey,
                                                 passphrase=self._passphrase,
                                                 proxy=self._proxy
                                                 )

        self.bitcoin_data_api = BitcoinDataApiWrapper.get_instance(self._proxies)
        self.alternative_api = AlternativeApiWrapper.get_instance(self._proxies)

        self.context = Context()

    def prepare_data(self):
        # 用当前日期、指标最大回溯窗口计算开始日期，结束日期为当前日期
        current_date = datetime.datetime.today()
        start_dt = current_date - datetime.timedelta(days=max(self.pi_cycle_long_window,
                                                              self.rsi_window,
                                                              self.mayer_window,
                                                              self.bollinger_window
                                                              )
                                                     )
        end_dt = current_date

        # 准备好kline、sth_mvrv、mvrv_zscore、feargreed等数据
        # sth_mvrv、mvrv_zscore、feargreed尚无底层数据，直接从其他免费获取数据的平台网站获取最终指标
        self.kline_data = self.OKxApi.get_history_kline_data(symbol_id='BTC-USD',
                                                             interval='1d',
                                                             start_dt=start_dt,
                                                             end_dt=end_dt
                                                             )

        self.sth_mvrv_data = self.bitcoin_data_api.get_sth_mvrv_data(start_dt=start_dt, end_dt=current_date)
        self.mvrv_zscore_data = self.bitcoin_data_api.get_mvrv_zscore_data(start_dt=start_dt, end_dt=current_date)
        self.feargreed_data = self.alternative_api.get_feargreed_data(start_dt=start_dt, end_dt=current_date)

        # 使用上下文变量（context）保存kline_data、close_array; close_array定义为np.array类型，提高计算效率
        self.context.kline_data = self.kline_data
        self.context.close_array = self.kline_data['close'].to_numpy()

    def calculate_pi_cycle(self):
        indicator = IndicatorPiCycle(short_window=self.pi_cycle_short_window,
                                     long_window=self.pi_cycle_long_window
                                     )

        ma_short, ma_long = indicator.compute(self.context)

        if ma_short[-1] > 2 * ma_long[-1]:
            return True
        else:
            return False

    def calculate_mayer_multiple(self):
        indicator = IndicatorMayerMultiple(window=self.mayer_window)
        mayer_multiple = indicator.compute(self.context)
        if mayer_multiple[-1] > self.mayer_threshold:
            return True
        else:
            return False


    def calculate_bollinger(self):
        indicator = IndicatorBollinger(window=self.bollinger_window,
                                       nbdev=self.bollinger_nbdev
                                       )
        upper_band, middle_band, lower_band = indicator.compute(self.context)

        if self.context.close_array[-1] > upper_band[-1] and self.context.close_array[-2] <= upper_band[-2]:
            return True
        else:
            return False

    def calculate_rsi(self):
        indicator = IndicatorRSI(window=self.rsi_window)
        rsi = indicator.compute(self.context)

        if len(rsi) > 0 and rsi[-1] > self.rsi_upper:
            return True
        else:
            return False

    def calculate_macd(self):
        indicator = IndicatorMACD(fast_period=self.macd_fast_period,
                                  slow_period=self.macd_slow_period,
                                  signal_period=self.macd_signal_period
                                  )

        dif, dea, hist = indicator.compute(context=self.context)

        # 判断是否死叉
        if len(dif) > 2 and dif[-1] < dea[-1] and dif[-2] > dea[-2]:
            return True
        else:
            return False

    def calculate_sth_mvrv(self):
        if self.sth_mvrv_data is not None and len(self.sth_mvrv_data) > 0:
            std_mvrv = self.sth_mvrv_data['sth_mvrv'][self.sth_mvrv_data['sth_mvrv'].notna()].iloc[-1]

            if std_mvrv > 2:
                return True
            else:
                return False
        else:
            return False

    def calculate_mvrv_zscore(self):
        """
        市场高估信号：
            当 MVRV Z-Score 较高（例如，超过某个阈值，通常认为在 7 或 8 左右，但会因市场状况而异）时，这表明市场可能被高估。
            高 MVRV Z-Score 表示比特币的市值相对于其已实现价值明显高于其历史平均值，这可能意味着当前市场价格远高于上次币转手时的平均支付价格。
        潜在的市场顶部：
            当 MVRV Z-Score 达到如此高的水平时，这可能是市场顶部的一个信号。这是因为高 Z-Score 意味着市场处于价格已显著偏离其市值和已实现价值之间历史关系的状态。
            在这一点上，持有比特币一段时间的投资者可能会看到显著的未实现利润，他们可能会开始抛售，从而导致市场调整或价格下跌。
        """
        if self.mvrv_zscore_data is not None and len(self.mvrv_zscore_data) > 0:
            mvrv_zscore = self.mvrv_zscore_data['mvrv_zscore'][self.mvrv_zscore_data['mvrv_zscore'].notna()].iloc[-1]

            if mvrv_zscore > 8:
                return True
            else:
                return False
        else:
            return False

    def calculate_fear_greed(self):
        """
        加密货币恐惧与贪婪指数由 Alternative.me 提供，是一个综合指标，旨在将投资者情绪浓缩为一个单一的数值。
        它汇总了来自多个来源的数据，从而提供了一个关于市场情绪的综合视角。该指数的范围从 0 到 100，其中 0 代表 “极度恐惧”。
        处于这个极端时，投资者情绪的特点是过度消极，表明一种普遍的谨慎和悲观情绪。相反，得分为 100 表示 “极度贪婪”，
        意味着一种错失恐惧症（FOMO）达到顶峰的情况，并且投资者可能会过度热情和看涨。
        如需深入理解和详细分析基础指标，请访问 Alternative.me 的原始来源。
        :return:
        """
        if self.feargreed_data is not None and len(self.feargreed_data) > 0:
            feargreed = self.feargreed_data['value'].iloc[-1]

            if feargreed > self.feargreed_threshold:
                return True
            else:
                return False
        else:
            return False

    def run(self):
        """
        计算逃顶指标，以True/False为标记，组合成dict返回
        :return: 各逃顶指标的信号组合
        """
        self.prepare_data()

        escape_flag = dict()
        escape_flag['pi_cycle'] = self.calculate_pi_cycle()
        escape_flag['mvrv_zscore'] = self.calculate_mvrv_zscore()
        escape_flag['mayer_multiple'] = self.calculate_mayer_multiple()
        escape_flag['feargreed'] = self.calculate_fear_greed()
        escape_flag['rsi'] = self.calculate_rsi()
        escape_flag['macd'] = self.calculate_macd()
        escape_flag['sth_mvrv'] = self.calculate_sth_mvrv()
        escape_flag['boll'] = self.calculate_bollinger()

        return escape_flag


if __name__ == "__main__":
    from btc_model.setting.setting import get_settings

    params = get_settings('escape_model.indicator')

    model = EscapeModel(setting=params)
    result = model.run()

    print(result)
