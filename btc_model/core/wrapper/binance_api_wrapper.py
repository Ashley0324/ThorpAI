import pandas as pd
from typing import Union, List, Any, Optional, Coroutine, Callable, Tuple, Iterable

from binance.client import Client
from binance.enums import HistoricalKlinesType

from btc_model.core.common.const import Interval, Exchange, InstrumentType, Product
from btc_model.core.common.object import Instrument


class BinanceApiWrapper(object):
    __instance = None

    def __init__(self, apikey, secretkey):
        self._client = Client(api_key=apikey,
                              api_secret=secretkey,
                              )

    @classmethod
    def get_instance(cls, apikey, secretkey):
        if cls.__instance is None:
            cls.__instance = cls(apikey, secretkey)

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

        if interval == Interval.MINUTE_1:
            bar = '1m'
        elif interval == Interval.MINUTE_5:
            bar = '5m'
        elif interval == Interval.MINUTE_15:
            bar = '15m'
        elif interval == Interval.MINUTE_30:
            bar = '30m'
        elif interval == Interval.HOUR:
            bar = '1h'
        elif interval == Interval.DAILY:
            bar = '1d'
        else:
            raise Exception(f'输入参数【interval={interval}】无效或尚未支持!')

        if marketdata_type == 'index':
            klines_type = HistoricalKlinesType.FUTURES_INDEX_PRICE
        elif marketdata_type == 'spot':
            klines_type = HistoricalKlinesType.SPOT
        else:
            raise Exception(f'输入参数【marketdata_type={marketdata_type}】无效或尚未支持!')

        res = self._client.get_historical_klines(symbol=symbol_id,
                                                 interval=bar,
                                                 start_str=start_dt,
                                                 end_str=end_dt,
                                                 klines_type=klines_type)
        if res is not None and len(res) > 0:
            kline_data = pd.DataFrame(res)

            kline_data.columns = [
                'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
                'Close Time', 'Quote Asset Volume', 'Number of Trades',
                'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
            ]
            kline_data['Open Time'] = pd.to_datetime(kline_data['Open Time'], unit='ms')
            kline_data['Close Time'] = pd.to_datetime(kline_data['Close Time'], unit='ms')
            kline_data['symbol_id'] = symbol_id

            kline_data = kline_data.rename(columns={'Open Time': 'datetime',
                                                    'Open': 'open',
                                                    'High': 'high',
                                                    'Low': 'low',
                                                    'Close': 'close',
                                                    'Quote Asset Volume': 'turnover',
                                                    'Volume': 'volume'
                                                    })

            kline_data = kline_data[['symbol_id', 'datetime', 'open', 'high', 'low', 'close', 'turnover', 'volume']]
            kline_data[['open', 'high', 'low', 'close', 'turnover', 'volume']] = kline_data[
                ['open', 'high', 'low', 'close', 'turnover', 'volume']].astype(float)

            return kline_data.sort_values('datetime').reset_index(drop=True)
        else:
            return None


    def _internal_extract_symbol_detail(self, exchange_info):
        symbols = []
        for symbol_info in exchange_info['symbols']:
            symbol = {
                'symbol': symbol_info['symbol'],
                'status': symbol_info['status'],
                'baseAsset': symbol_info['baseAsset'],
                'quoteAsset': symbol_info['quoteAsset'],
                'quotePrecision': symbol_info['quotePrecision'],
                'filters': {}
            }

            # 提取过滤器信息
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'PRICE_FILTER':
                    symbol['filters']['minPrice'] = filter['minPrice']
                    symbol['filters']['maxPrice'] = filter['maxPrice']
                    symbol['filters']['tickSize'] = filter['tickSize']
                elif filter['filterType'] == 'LOT_SIZE':
                    symbol['filters']['minQty'] = filter['minQty']
                    symbol['filters']['maxQty'] = filter['maxQty']
                    symbol['filters']['stepSize'] = filter['stepSize']
                elif filter['filterType'] == 'MIN_NOTIONAL':
                    symbol['filters']['minNotional'] = filter['minNotional']
                elif filter['filterType'] == 'PERCENT_PRICE':
                    symbol['filters']['multiplierUp'] = filter['multiplierUp']
                    symbol['filters']['multiplierDown'] = filter['multiplierDown']

            symbols.append(symbol)

        return symbols

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
            exchange_info = self._client.get_exchange_info()
            if exchange_info is not None:
                symbols = self._internal_extract_symbol_detail(exchange_info=exchange_info)
                for symbol in symbols:
                    instrument: Instrument = Instrument(
                        instrument_id=symbol['symbol'],
                        instrument_name=symbol['symbol'],
                        exchange=Exchange.BINANCE.value,
                        instrument_type=InstrumentType.CRYPTO,
                        product=product,
                        list_date='',
                        expire_date='',
                        price_tick=float(symbol['filters'].get('tickSize', 0)),
                        min_limit_order_volume=float(symbol['filters'].get('minQty')),
                        max_limit_order_volume=float(symbol['filters'].get('maxQty')),
                        min_market_order_volume=float(symbol['filters'].get('minQty')),
                        max_market_order_volume=float(symbol['filters'].get('minQty')),
                        status=symbol['status'],
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

        return fetch_data


if __name__ == "__main__":
    from btc_model.setting.setting import get_settings

    setting = get_settings('cex.binance')

    apikey = setting['apikey']
    secretkey = setting['secretkey']

    instance = BinanceApiWrapper.get_instance(apikey, secretkey)

    # instruments = instance.get_instruments(product=Product.SPOT)
    # print(instruments)

    start_dt = '2024-01-01 00:00:00'
    end_dt = '2025-01-18 23:59:59'
    result = instance.get_history_kline_data("BTCUSDT", Interval.DAILY, start_dt, end_dt)

    print(result)
