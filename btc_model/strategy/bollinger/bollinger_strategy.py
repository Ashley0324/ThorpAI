import platform
import pandas as pd
import numpy as np
import seaborn as sns
import pyfolio as pf
import backtrader as bt
import backtrader.feeds as bt_feeds
import matplotlib.pyplot as plt
import pytz
import empyrical
from empyrical import sharpe_ratio

from btc_model.core.util.file_cache_util import FileCacheUtil

operating_system = platform.system()

if operating_system == "Windows":
    BTC_1_MIN_DATA_PATH = 'D:/source/Data/加密货币/1分钟k线/1M-Binance_BTCUSDT_data.csv'
else:
    BTC_1_MIN_DATA_PATH = '/Users/Jason/work/03 - data/加密货币/1分钟k线/1M-Binance_BTCUSDT_data.csv'

# 恒生指数期货合约乘数
VOLUME_MULTIPLE = 1


class PandasDataFeed(bt.feeds.PandasData):
    params = (
        ('datetime', 0),
        ('open', 'open'),
        ('close', 'close'),
        ('high', 'high'),
        ('low', 'low'),
        ('volume', 'volume'),
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
    )


# class GenericCSVData(bt.feeds.GenericCSVData):
#     lines = ('trend',)
#     params = (
#         ('datetime', 0),
#         ('open', 1),
#         ('close', 2),
#         ('high', 3),
#         ('low', 4),
#         ('volume', 5),
#         ('trend', 6),
#         ('dtformat', '%Y-%m-%d %H:%M:%S'),
#     )


class BollingerStrategy(bt.Strategy):
    params = (
        ('bollinger_15m_period', 300),
        ('bollinger_15m_stddev_multiple', 1.5),
        ('bollinger_15m_stop_profit_std_n', 8),
        ('atr_15m_period', 300),

        ('bollinger_30m_period', 20),
        ('bollinger_30m_stddev_multiple', 2),
        ('bollinger_30m_stop_profit_std_n', 8),
        ('atr_30m_period', 15),


        ('bollinger_60m_period', 300),
        ('bollinger_60m_stddev_multiple', 1.5),
        ('bollinger_60m_stop_profit_std_n', 8),
        ('atr_60m_period', 300),

        ('printlog', True),
    )

    def __init__(self):
        # pdb.set_trace()
        super(BollingerStrategy, self).__init__()

        self.order = None
        self.buy_price = None
        self.buy_comm = None
        self.bar_executed = None
        self.value_start = None

        self.target_price = 0

        # 存储每天的市值
        self.daily_values = {}
        self.previous_date = None

        self.data_1m = self.getdatabyname('data_1m')
        self.data_15m = self.getdatabyname('data_15m')
        self.data_30m = self.getdatabyname('data_30m')
        self.data_60m = self.getdatabyname('data_60m')

        self.atr_15m = bt.indicators.AverageTrueRange(self.data_15m, period=self.params.atr_15m_period)
        self.atr_30m = bt.indicators.AverageTrueRange(self.data_30m, period=self.params.atr_30m_period)
        self.atr_60m = bt.indicators.AverageTrueRange(self.data_60m, period=self.params.atr_60m_period)

        self.bollinger_15m = bt.indicators.BollingerBands(self.data_15m.close,
                                                          period=self.params.bollinger_15m_period,
                                                          devfactor=self.params.bollinger_15m_stddev_multiple
                                                          )
        self.bollinger_30m = bt.indicators.BollingerBands(self.data_30m.close,
                                                          period=self.params.bollinger_30m_period,
                                                          devfactor=self.params.bollinger_30m_stddev_multiple
                                                          )
        self.bollinger_60m = bt.indicators.BollingerBands(self.data_60m.close,
                                                          period=self.params.bollinger_60m_period,
                                                          devfactor=self.params.bollinger_60m_stddev_multiple
                                                          )

        self.middle_band_15m = self.bollinger_15m.mid
        self.upper_band_15m = self.bollinger_15m.top
        self.lower_band_15m = self.bollinger_15m.bot

        self.middle_band_30m = self.bollinger_30m.mid
        self.upper_band_30m = self.bollinger_30m.top
        self.lower_band_30m = self.bollinger_30m.bot

        self.middle_band_60m = self.bollinger_60m.mid
        self.upper_band_60m = self.bollinger_60m.top
        self.lower_band_60m = self.bollinger_60m.bot

    def trade_by_bollinger(self, params):
        data = params['data']
        upper_band = params['upper_band']
        middle_band = params['middle_band']
        lower_band = params['lower_band']
        atr = params['atr']
        stop_profit_std_n = params['stop_profit_std_n']

        if self.data_1m.datetime.datetime(0) != data.datetime.datetime(0):
            return

        # print(data.datetime.datetime(0).strftime("%Y-%m-%d %H:%M:%S"))

        if self.order:
            return

        # need at least two bollinger records
        if np.count_nonzero(~np.isnan(middle_band.get(0, len(middle_band)))) == 1:
            return

        if self.position.size == 0 and \
                data.close[0] > upper_band[0] and \
                data.close[-1] < upper_band[-1]:

            # 杠杠率/仓位比例调整
            # 参照海龟资金管理，1单位ATR的波动对应策略整体资金规模的0.5%
            atr_value = atr[0]
            price = data.close[0]
            leverage = 0.005 / atr_value * price if atr_value != 0 else 0

            # 最大4倍杠杆，超过截断
            if leverage > 4:
                leverage = 4

            self.target_price = middle_band[0] * stop_profit_std_n

            order_size = self.broker.get_cash() / (price * VOLUME_MULTIPLE) * leverage

            self.order = self.buy(size=order_size)
            self.log('INSERT BUY OPEN ORDER, Pre-Price: %.2f, Price: %.2f, Pre-UB: %.2f, UB: %.2f, Size: %.2f' %
                     (data.close[-1],
                      data.close[0],
                      upper_band[-1],
                      upper_band[0],
                      self.getsizing(isbuy=True)))

        elif self.position.size > 0 and (
                data.close[0] < middle_band[0] or data.close[0] > self.target_price):
            # close long position
            # 收盘价向下穿过布林带中轨

            self.order = self.close()
            self.log('INSERT SELL CLOSE ORDER, Pre-Price: %.2f, Price: %.2f, Pre-MB: %.2f, MB: %.2f, Size: %.2f' %
                     (data.close[-1],
                      data.close[0],
                      middle_band[-1],
                      middle_band[0],
                      self.getsizing(isbuy=False)))

        elif self.position.size == 0 and \
                data.close[0] < lower_band[0] and \
                data.close[-1] > lower_band[-1]:

            # 杠杠率/仓位比例调整
            # 参照海龟资金管理，1单位ATR的波动对应策略整体资金规模的0.5%
            atr_value = atr[0]
            price = data.close[0]
            leverage = 0.005 / atr_value * price if atr_value != 0 else 0

            # 最大4倍杠杆，超过截断
            if leverage > 4:
                leverage = 4

            self.target_price = middle_band[0] * stop_profit_std_n

            order_size = self.broker.get_cash() / (price * VOLUME_MULTIPLE) * leverage

            self.order = self.sell(size=order_size)
            self.log('INSERT SELL OPEN ORDER, Pre-Price: %.2f, Price: %.2f, Pre-LB: %.2f, LB: %.2f, Size: %.2f' %
                     (data.close[-1],
                      data.close[0],
                      lower_band[-1],
                      lower_band[0],
                      self.getsizing(isbuy=False)))

        elif self.position.size < 0 and (
                data.close[0] > middle_band[0] or data.close[0] < self.target_price):
            # close short position
            # 收盘价向上穿过布林带中轨
            # pdb.set_trace()
            self.order = self.close()
            self.log('INSERT BUY CLOSE ORDER, Pre-Price: %.2f, Price: %.2f, Pre-MB: %.2f, MB: %.2f, Size: %.2f' %
                     (data.close[-1],
                      data.close[0],
                      middle_band[-1],
                      middle_band[0],
                      self.getsizing(isbuy=True)))

    def next(self):
        params = {
            'data': self.data_60m,
            'upper_band': self.upper_band_60m,
            'middle_band': self.middle_band_60m,
            'lower_band': self.lower_band_60m,
            'atr': self.atr_60m,
            'stop_profit_std_n': self.params.bollinger_60m_stop_profit_std_n,
        }
        current_date = self.data_15m.datetime.datetime(0).strftime("%Y-%m-%d")
        if self.previous_date is None or self.previous_date != current_date:
            self.previous_date = current_date
            current_value = self.broker.get_value()
            self.daily_values[current_date] = current_value

            print(f'{current_date}, current value={current_value}')

        self.trade_by_bollinger(params)

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def start(self):
        self.value_start = self.broker.get_cash()  # keep the starting cash

    def stop(self):
        # calculate the actual returns
        print(self.analyzers)
        roi = (self.broker.get_value() / self.value_start) - 1
        self.log('ROI:        {:.2f}%'.format(100.0 * roi))
        self.log('BollingerStrategy Ending Value %.2f' %
                 (self.broker.getvalue()),
                 doprint=True)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:  # order.Partial
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %.0f, Cost: %.2f, Comm %.2f, RemSize: %.0f, RemCash: %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.remsize,
                     self.broker.get_cash()))

                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Size: %.0f, Cost: %.2f, Comm %.2f, RemSize: %.0f, RemCash: %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.remsize,
                     self.broker.get_cash()))

            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Expired, order.Margin, order.Rejected]:
            self.log('Order Failed')

        self.order = None


def show_result_empyrical(returns, risk_free=0.00):
    print('\n\n<----Emprical策略评价---->')
    # 总收益率
    pan = empyrical.cum_returns(returns)[len(returns) - 1]
    print('总收益率：', pan)
    print('年化收益：', empyrical.annual_return(returns))
    # print('非系统性风险ALPHA：', empyrical.alpha(returns, factor_returns, risk_free=risk_free))
    # print('系统性风险BETA：', beta(returns, factor_returns, risk_free=risk_free))
    # print('alpha_beta_aligned:',alpha_beta_aligned(returns))
    print('最大回撤：', empyrical.max_drawdown(returns))
    print('夏普比', empyrical.sharpe_ratio(returns))
    print('卡玛比', empyrical.calmar_ratio(returns))
    print('omega', empyrical.omega_ratio(returns, risk_free))
    print('annual_volatility', empyrical.annual_volatility(returns))
    print('downside_risk', empyrical.downside_risk(returns))
    print('sortino_ratio', empyrical.sortino_ratio(returns))
    print('tail_ratio', empyrical.tail_ratio(returns))
    print('<----Emprical 评价 End---->\n')


if __name__ == '__main__':
    start_dt = '2023-01-01'
    end_dt = '2023-12-31'

    cached_data, cache_file_path, cache_file_desc = (
        FileCacheUtil.load_cached_data(params=[start_dt, end_dt, BTC_1_MIN_DATA_PATH]))
    if cached_data is not None:
        data_1m = cached_data['data_1m']
    else:
        data_1m = pd.read_csv(BTC_1_MIN_DATA_PATH, index_col=-1)
        data_1m = data_1m.rename(columns={'open_time': 'datetime'})
        data_1m = data_1m[(data_1m['datetime'] >= start_dt) & (data_1m['datetime'] <= end_dt)]
        data_1m['datetime'] = pd.to_datetime(data_1m['datetime'])
        data_1m = data_1m[['datetime', 'open', 'close', 'high', 'low', 'volume']]
        data_1m = data_1m.reset_index(drop=True)

        FileCacheUtil.save_cached_data(file_path=cache_file_path, file_desc=cache_file_desc,
                                       object_to_save={'data_1m': data_1m})

    data_1m = PandasDataFeed(dataname=data_1m)

    cerebro = bt.Cerebro()
    start_cash = 10000000
    # 设置资金
    cerebro.broker.setcash(start_cash)
    # cerebro.addsizer(bt.sizers.PercentSizerInt, percents=95)
    # 设置佣金、最大杠杆比例、保证金比例
    cerebro.broker.setcommission(commission=0.0001, leverage=10.0, margin=0.1)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name="PyFolio")

    cerebro.adddata(data_1m, name='data_1m')
    # 重采样
    cerebro.resampledata(data_1m, name="data_15m", timeframe=bt.TimeFrame.Minutes, compression=15)
    cerebro.resampledata(data_1m, name="data_30m", timeframe=bt.TimeFrame.Minutes, compression=30)
    cerebro.resampledata(data_1m, name="data_60m", timeframe=bt.TimeFrame.Minutes, compression=60)

    cerebro.addstrategy(BollingerStrategy)
    results = cerebro.run()

    # 获取回测结束后的总资金
    port_value = cerebro.broker.getvalue()
    pnl = port_value - start_cash
    # 打印结果
    print(f'初始资金：{start_cash}')
    print(f'总资金: {round(port_value, 2)}')
    print(f'净收益: {round(pnl, 2)}')

    date_values = results[0].daily_values

    pyfolio = results[0].analyzers.PyFolio
    returns, positions, transactions, gross_lev = pyfolio.get_pf_items()

    show_result_empyrical(returns)
