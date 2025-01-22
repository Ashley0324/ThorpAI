# -*- coding: UTF-8 –*-

"""
Author: guozq

Create Date: 2025/01/22

Description:

"""
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



operating_system = platform.system()

if operating_system == "Windows":
    BTC_15_MIN_DATA_PATH = 'D:/source/Data/BTC/BTC_15m.csv'
    BTC_30_MIN_DATA_PATH = 'D:/source/Data/BTC/BTC_30m.csv'
    BTC_1_DAY_DATA_PATH = 'D:/source/Data/BTC/BTC_1d.csv'
else:
    BTC_15_MIN_DATA_PATH = '/Users/Jason/work/03 - data/BTC/BTC_15m.csv'
    BTC_30_MIN_DATA_PATH = '/Users/Jason/work/03 - data/BTC/BTC_30m.csv'
    BTC_1_DAY_DATA_PATH = '/Users/Jason/work/03 - data/BTC/BTC_1d.csv'



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
        ('atr_30m_period', 15),
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

        self.data_15m = self.getdatabyname('15m')
        # self.data_30m = self.getdatabyname('30m')

        self.atr_15m = bt.indicators.AverageTrueRange(self.data_15m, period=self.params.atr_15m_period)

        # self.close_price_15m = self.data_15m.close
        self.bollinger_15m = bt.indicators.BollingerBands(self.data_15m.close,
                                                          period=self.params.bollinger_15m_period,
                                                          devfactor=self.params.bollinger_15m_stddev_multiple
                                                          )

        self.middle_band_15m = self.bollinger_15m.mid
        self.upper_band_15m = self.bollinger_15m.top
        self.lower_band_15m = self.bollinger_15m.bot

        # 添加 SAR 指标
        # self.sar = bt.indicators.ParabolicSAR(self.data)

    def trade_by_bollinger(self):
        dt_15m = self.data_15m.datetime.datetime(0).strftime("%Y-%m-%d %H:%M:%S")

        if self.order:
            return


        # need at least two bollinger records
        if np.count_nonzero(~np.isnan(self.middle_band_15m.get(0, len(self.middle_band_15m)))) == 1:
            return

        if self.position.size == 0 and \
                self.data_15m.close[0] > self.upper_band_15m[0] and \
                self.data_15m.close[-1] < self.upper_band_15m[-1]:


            # 杠杠率/仓位比例调整
            # 参照海龟资金管理，1单位ATR的波动对应策略整体资金规模的0.5%
            atr_value = self.atr_15m[0]
            price = self.data_15m.close[0]
            leverage = 0.005 / atr_value * price if atr_value != 0 else 0

            # 最大4倍杠杆，超过截断
            if leverage > 4:
                leverage = 4

            self.target_price = self.middle_band_15m[0] * self.params.bollinger_15m_stop_profit_std_n

            order_size = self.broker.get_cash() / (price * VOLUME_MULTIPLE) * leverage

            self.order = self.buy(size=order_size)
            self.log('INSERT BUY OPEN ORDER, Pre-Price: %.2f, Price: %.2f, Pre-UB: %.2f, UB: %.2f, Size: %.2f' %
                     (self.data_15m.close[-1],
                      self.data_15m.close[0],
                      self.upper_band_15m[-1],
                      self.upper_band_15m[0],
                      self.getsizing(isbuy=True)))

        elif self.position.size > 0 and (self.data_15m.close[0] < self.middle_band_15m[0] or self.data_15m.close[0] > self.target_price):
            # close long position
            # 收盘价向下穿过布林带中轨
            # pdb.set_trace()

            self.order = self.close()
            self.log('INSERT SELL CLOSE ORDER, Pre-Price: %.2f, Price: %.2f, Pre-MB: %.2f, MB: %.2f, Size: %.2f' %
                     (self.data_15m.close[-1],
                      self.data_15m.close[0],
                      self.middle_band_15m[-1],
                      self.middle_band_15m[0],
                      self.getsizing(isbuy=False)))

        elif self.position.size == 0 and \
                self.data_15m.close[0] < self.lower_band_15m[0] and \
                self.data_15m.close[-1] > self.lower_band_15m[-1]:

            # 杠杠率/仓位比例调整
            # 参照海龟资金管理，1单位ATR的波动对应策略整体资金规模的0.5%
            atr_value = self.atr_15m[0]
            price = self.data_15m.close[0]
            leverage = 0.005 / atr_value * price if atr_value != 0 else 0

            # 最大4倍杠杆，超过截断
            if leverage > 4:
                leverage = 4

            self.target_price = self.middle_band_15m[0] * self.params.bollinger_15m_stop_profit_std_n

            order_size = self.broker.get_cash() / (price * VOLUME_MULTIPLE) * leverage

            self.order = self.sell(size=order_size)
            self.log('INSERT SELL OPEN ORDER, Pre-Price: %.2f, Price: %.2f, Pre-LB: %.2f, LB: %.2f, Size: %.2f' %
                     (self.data_15m.close[-1],
                      self.data_15m.close[0],
                      self.lower_band_15m[-1],
                      self.lower_band_15m[0],
                      self.getsizing(isbuy=False)))


        elif self.position.size < 0 and (self.data_15m.close[0] > self.middle_band_15m[0] or self.data_15m.close[0] < self.target_price):
            # close short position
            # 收盘价向上穿过布林带中轨
            # pdb.set_trace()
            self.order = self.close()
            self.log('INSERT BUY CLOSE ORDER, Pre-Price: %.2f, Price: %.2f, Pre-MB: %.2f, MB: %.2f, Size: %.2f' %
                     (self.data_15m.close[-1],
                      self.data_15m.close[0],
                      self.middle_band_15m[-1],
                      self.middle_band_15m[0],
                      self.getsizing(isbuy=True)))

    def next(self):
        current_date = self.data_15m.datetime.datetime(0).strftime("%Y-%m-%d")
        if self.previous_date is None or self.previous_date != current_date:
            self.previous_date = current_date
            current_value = self.broker.get_value()
            self.daily_values[current_date] = current_value


        self.trade_by_bollinger()

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
    data_15m = pd.read_csv(BTC_15_MIN_DATA_PATH, index_col=0)
    data_15m = data_15m.rename(columns={'code': 'instrument_id', 'time_key': 'datetime'})
    data_15m = data_15m[(data_15m['datetime'] >= '2024-10-25') & (data_15m['datetime'] <= '2024-12-31')]
    data_15m['datetime'] = pd.to_datetime(data_15m['datetime'])
    data_15m = data_15m[['datetime', 'open', 'close', 'high', 'low', 'volume', 'turnover']]

    data_15m = PandasDataFeed(dataname=data_15m)


    cerebro = bt.Cerebro()
    start_cash = 10000000
    # 设置资金
    cerebro.broker.setcash(start_cash)
    # cerebro.addsizer(bt.sizers.PercentSizerInt, percents=95)
    # 设置佣金、最大杠杆比例、保证金比例
    cerebro.broker.setcommission(commission=0.0001, leverage=10.0, margin=0.1)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name="PyFolio")

    cerebro.adddata(data_15m, name='15m')
    cerebro.addstrategy(BollingerStrategy)
    # 不要调用cerebro.run() 策略执行交给run_and_show_performance函数负责
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
