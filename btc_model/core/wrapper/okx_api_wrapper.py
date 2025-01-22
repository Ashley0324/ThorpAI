# -*- coding: utf-8 -*
import pandas as pd
from tqdm import tqdm
from time import sleep
import requests, time, hmac, hashlib, json, os
from urllib.parse import urlencode

import okx.MarketData as MarketData

class OKxApiWrapper(object):
    __instance = None

    def __init__(self, apikey, secretkey, passphrase, proxy):
        self._market_api = MarketData.MarketAPI(api_key=apikey,
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

    def get_kline(self, symbol_id, interval, start_dt, end_dt, **kwargs):
        """
        获取的K线数据
        :param symbol: 交易对，如 "BTC-USDT"
        :param interval: K线时间间隔，如 "1d" 表示每天
        :param start_time: 开始时间戳（毫秒）
        :param end_time: 结束时间戳（毫秒）
        :param limit: 返回的K线数量限制
        :return: K线数据列表
        """
        # 字符串的日期转换为datetime
        start_dt = str(int(pd.to_datetime(start_dt).timestamp() * 1000))
        end_dt = str(int(pd.to_datetime(end_dt).timestamp() * 1000))

        all_data = []
        received_rows = 0
        current_date = end_dt

        with tqdm() as pbar:
            while current_date > start_dt:
                try:
                    res = self._market_api.get_index_candlesticks(instId="BTC-USD",
                                                            bar="1D",
                                                            after=current_date,
                                                            before=start_dt,
                                                            limit=100)
                except Exception as e:
                    print(f"从OKX获取行情失败, 错误信息: {e}")
                    return None

                data = res['data']
                if not data:  # 如果没有更多数据，退出循环
                    break

                df = pd.DataFrame(data)
                received_rows += len(df)

                all_data.append(df)

                # 更新 current_date 为最早一条数据的时间
                current_date = df.iloc[-1][0]

                # 添加延迟以避免超过 API 速率限制
                time.sleep(0.1)

                pbar.update(received_rows)
                pbar.set_description(
                    f"fetching data from OKX, symbol_id: {symbol_id}, received rows: {received_rows}")

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            # final_df = final_df[final_df['Open Time'] <= start_dt]
            final_df.columns = [
                'datetime', 'open', 'high', 'low', 'close', 'ignore'
            ]
            final_df['datetime'] = pd.to_datetime(final_df['datetime'].astype('int64'), unit='ms', origin='unix')
            final_df['symbol_id'] = symbol_id


            final_df = final_df[['symbol_id', 'datetime', 'open', 'high', 'low', 'close']]
            final_df[['open', 'high', 'low', 'close']] = final_df[['open', 'high', 'low', 'close']].astype(float)
            return final_df.sort_values('datetime').reset_index(drop=True)
        else:
            return None

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

    limit = setting['limit']
    apikey = setting['apikey']
    secretkey = setting['secretkey']
    passphrase = setting['passphrase']
    proxy = setting['proxy']

    instance = OKxApiWrapper.get_instance(apikey, secretkey, passphrase, proxy)

    # start_dt = '2024-01-01 00:00:00'
    # end_dt = '2025-01-18 23:59:59'
    # result = instance.get_kline("BTC-USD", '1D', start_dt, end_dt)

    result = instance.get_index_ticker(symbol_id='BTC-USD')

    print(result)
