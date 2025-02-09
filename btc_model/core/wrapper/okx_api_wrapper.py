import pandas as pd
import time
from typing import Union, List, Any, Optional, Coroutine, Callable, Tuple, Iterable

from okx.MarketData import MarketAPI
from okx.PublicData import PublicAPI

from btc_model.core.common.const import Interval, Exchange, InstrumentType, Product
from btc_model.core.common.object import Instrument


class OKxApiWrapper(object):
    __instance = None

    def __init__(self, apikey, secretkey, passphrase, proxy):
        self._market_api = MarketAPI(api_key=apikey,
                                     api_secret_key=secretkey,
                                     passphrase=passphrase,
                                     proxy=proxy,
                                     flag='0',
                                     debug=False
                                     )

        self._public_api = PublicAPI(api_key=apikey,
                                     api_secret_key=secretkey,
                                     passphrase=passphrase,
                                     proxy=proxy,
                                     flag='0'
                                     )

    @classmethod
    def get_instance(cls, apikey, secretkey, passphrase, proxy):
        if cls.__instance is None:
            cls.__instance = cls(apikey, secretkey, passphrase, proxy)

        return cls.__instance

    def _internal_get_kline_data(self, symbol_id, marketdata_type, interval: Interval, start_dt, end_dt, **kwargs):
        """
        指数、现货行情的调用接口和返回数据不同，其他处理方式相同，封装成一个内部调用函数
        :param symbol_id:
        :param marketdata_type: index/spot
        :param interval:
        :param start_dt:
        :param end_dt:
        :param kwargs:
        :return:
        """
        # 字符串的日期转换为datetime
        start_dt = str(int(pd.to_datetime(start_dt).timestamp() * 1000))
        end_dt = str(int(pd.to_datetime(end_dt).timestamp() * 1000))

        all_data = []
        received_rows = 0
        current_date = end_dt

        if interval == Interval.MINUTE_1:
            bar = '1m'
        elif interval == Interval.MINUTE_5:
            bar = '5m'
        elif interval == Interval.MINUTE_15:
            bar = '15m'
        elif interval == Interval.MINUTE_30:
            bar = '30m'
        elif interval == Interval.DAILY:
            bar = '1D'
        else:
            raise Exception(f'输入参数【interval={interval}】无效或尚未支持!')


        while current_date > start_dt:
            try:
                if marketdata_type == 'index':
                    res = self._market_api.get_index_candlesticks(instId=symbol_id,
                                                                  bar=bar,
                                                                  after=current_date,
                                                                  before=start_dt,
                                                                  limit=100)
                elif marketdata_type == 'spot':
                    res = self._market_api.get_history_candlesticks(instId=symbol_id,
                                                                    bar=bar,
                                                                    after=current_date,
                                                                    before=start_dt,
                                                                    limit=100)
                else:
                    raise Exception(f'输入参数【marketdata_type={marketdata_type}】无效或尚未支持!')

            except Exception as e:
                print(f"从OKX获取行情失败, 错误信息: {e}")
                return None

            data = res['data']
            if not data:  # 如果没有更多数据，退出循环
                break

            df = pd.DataFrame(data)
            received_rows += len(df)

            if len(df) > 0:
                all_data.append(df)

            # 更新 current_date 为最早一条数据的时间
            current_date = df.iloc[-1][0]

            # 添加延迟以避免超过 API 速率限制
            time.sleep(0.1)

        if all_data and len(all_data) > 0:
            all_data = pd.concat(all_data, ignore_index=True)
        else:
            all_data = None

        return all_data

    def get_instruments(self, product: Union[List[Product], Product] = None, **kwargs):
        """

        :param product_type:
        :param kwargs:
        :return: List(Instrument)
        """
        if product is None:
            # product_type_list = list(ProductType)
            product_list = [Product.SPOT]
        else:
            product_list = [product]

        if set(product_list).intersection({Product.OPTION,
                                                Product.SWAP,
                                                Product.FUTURES,
                                                Product.MARGIN
                                                }):
            raise Exception('Input argument not valid! 【product】only support spot recently.')

        instrument_list = []

        for product in product_list:
            res = self._public_api.get_instruments(instType=product.value,
                                                   uly='',
                                                   instFamily='',
                                                   instId=''
                                                   )

            if res['code'] != '0':
                raise Exception(res['msg'])



            for d in res['data']:
                instrument: Instrument = Instrument(
                    instrument_id=d['instId'],
                    instrument_name=d['instId'],
                    exchange=Exchange.OKX.value,
                    instrument_type=InstrumentType.CRYPTO,
                    product=product,
                    list_date=pd.to_datetime(pd.to_numeric(d['listTime'],  errors='coerce'), unit='ms', origin='unix').strftime('%Y-%m-%d') if d['listTime'].strip() else '',
                    expire_date=pd.to_datetime(pd.to_numeric(d['expTime'],  errors='coerce'), unit='ms', origin='unix').strftime('%Y-%m-%d') if d['expTime'].strip() else '',
                    price_tick=float(d['tickSz']),
                    min_limit_order_volume=float(d['minSz']),
                    max_limit_order_volume=float(d['maxLmtSz']),
                    min_market_order_volume=float(d['minSz']),
                    max_market_order_volume=float(d['maxMktSz']),
                    status=d['state']
                )

                instrument_list.append(instrument)

        return instrument_list

    def get_history_index_kline_data(self, symbol_id, interval: Interval, start_dt, end_dt, **kwargs):
        """
        获取指数的K线数据。指数是通过特定的计算方法，选取多个相关市场或交易对的数据进行综合计算得出的一个数值。
        OKX指数行情通常会综合多个主流加密货币交易平台上 BTC 的价格信息，经过加权平均等计算方式得到一个指数价格，以反映市场的整体价格水平。

        :param symbol_id 交易对，如 "BTC-USDT"
        :param interval: K线时间间隔，如 "1d" 表示每天
        :param start_dt: 开始时间, 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS‘
        :param end_dt: 结束时间
        :return: K线数据列表
        """

        fetch_data = self._internal_get_kline_data(symbol_id=symbol_id,
                                                   marketdata_type='index',
                                                   interval=interval,
                                                   start_dt=start_dt,
                                                   end_dt=end_dt,
                                                   **kwargs
                                                   )

        if fetch_data is not None:
            fetch_data.columns = [
                'datetime', 'open', 'high', 'low', 'close', 'ignore'
            ]
            fetch_data['datetime'] = pd.to_datetime(fetch_data['datetime'].astype('int64'), unit='ms', origin='unix')
            fetch_data['symbol_id'] = symbol_id

            fetch_data = fetch_data[['symbol_id', 'datetime', 'open', 'high', 'low', 'close']]
            fetch_data[['open', 'high', 'low', 'close']] = fetch_data[['open', 'high', 'low', 'close']].astype(float)
            fetch_data = fetch_data.sort_values('datetime').reset_index(drop=True)

        return fetch_data

    def get_history_kline_data(self, symbol_id, interval: Interval, start_dt, end_dt, **kwargs):
        """
        获取的K线数据
        :param symbol_id 交易对，如 "BTC-USDT"
        :param interval: K线时间间隔，如 "1d" 表示每天
        :param start_dt: 开始时间, 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS‘
        :param end_dt: 结束时间
        :return: K线数据列表
        """
        fetch_data = self._internal_get_kline_data(symbol_id=symbol_id,
                                                   marketdata_type='spot',
                                                   interval=interval,
                                                   start_dt=start_dt,
                                                   end_dt=end_dt,
                                                   **kwargs
                                                   )

        if fetch_data is not None and len(fetch_data) > 0:
            fetch_data.columns = [
                'datetime', 'open', 'high', 'low', 'close', 'volume', 'ignore', 'turnover', 'ignore'
            ]
            fetch_data['datetime'] = pd.to_datetime(fetch_data['datetime'].astype('int64'), unit='ms', origin='unix')
            fetch_data['symbol_id'] = symbol_id

            fetch_data = fetch_data[['symbol_id', 'datetime', 'open', 'high', 'low', 'close', 'volume', 'turnover']]
            fetch_data[['open', 'high', 'low', 'close', 'volume', 'turnover']] = fetch_data[['open',
                                                                                             'high',
                                                                                             'low',
                                                                                             'close',
                                                                                             'volume',
                                                                                             'turnover'
                                                                                             ]].astype(float)
            if interval in [Interval.MINUTE_1,
                            Interval.MINUTE_5,
                            Interval.MINUTE_15,
                            Interval.MINUTE_30,
                            Interval.TICK
                            ]:
                fetch_data['date'] = fetch_data['datetime'].dt.date
                fetch_data['time'] = fetch_data['datetime'].dt.time

            fetch_data = fetch_data.sort_values('datetime').reset_index(drop=True)

        return fetch_data

    def get_index_ticker(self, symbol_id):
        try:
            res = self._market_api.get_index_tickers(instId="BTC-USD")
        except Exception as e:
            print(f"从OKX获取行情失败, 错误信息: {e}")
            return None

        data = res['data']

        df = pd.DataFrame(data)

        return df


if __name__ == "__main__":
    from btc_model.setting.setting import get_settings

    setting = get_settings('cex.okx')

    apikey = setting['apikey']
    secretkey = setting['secretkey']
    passphrase = setting['passphrase']
    proxy = setting['proxy']

    instance = OKxApiWrapper.get_instance(apikey, secretkey, passphrase, proxy)

    # start_dt = '2024-01-01 00:00:00'
    # end_dt = '2025-01-18 23:59:59'
    # result = instance.get_history_kline_data("BTC-USD", Interval.DAILY, start_dt, end_dt)

    # result = instance.get_index_ticker(symbol_id='BTC-USD')

    result = instance.get_instruments(product_type=Product.SPOT)
    print(pd.DataFrame(result))
