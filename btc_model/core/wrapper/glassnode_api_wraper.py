"""
Author: guozq

Create Date: 2025-01-19

Description:
    Wrapper for fetching data of indicators provided by glassnode.
    These indicators are freely available from glassnode but cannot be obtained for free through exchange APIs.

History:
    2025-01-19: initial version.
"""

import pandas as pd
import requests


class GlassnodeApiWrapper(object):
    BASE_URL = "https://api.glassnode.com/"
    BASE_V1_URL = BASE_URL + "/v1"
    METRICS_URL = BASE_V1_URL + '/metrics'
    INDICATORS_URL = METRICS_URL + '/indicators'

    __instance = None

    def __init__(self, proxies):
        self.proxies = proxies

    @classmethod
    def get_instance(cls, proxies):
        if cls.__instance is None:
            cls.__instance = cls(proxies)

        return cls.__instance

    def get_indicator_data(self, request_path, params):
        url = self.INDICATORS_URL + '/' + request_path
        response = requests.get(url, params=params, proxies=self.proxies)

        if response.status_code == 200:
            data = response.json()

            data = pd.DataFrame(data)
            return data

        else:
            print("无法获取数据:", response.status_code, response.text)
            return None

    def get_s2f_data(self, start_dt, end_dt):
        """
        The Stock to Flow (S/F) Ratio is a popular model that assumes that scarcity drives value.
        Stock to Flow is defined as the ratio of the current stock of a commodity (i.e. circulating Bitcoin supply)
        and the flow of new production (i.e. newly mined bitcoins). Bitcoin's price has historically followed the S/F Ratio
        and therefore it is a model that can be used to predict future Bitcoin valuations. This metric was first coined by PlanB.
        For a detailed description see https://medium.com/@100trillionUSD/modeling-bitcoins-value-with-scarcity-91fa0fc03e25.
        """
        start_dt = int(pd.to_datetime(start_dt).timestamp() * 1000)
        end_dt = int(pd.to_datetime(end_dt).timestamp() * 1000)

        params = {
            'a': 'BTC',         # string, asset symbol: BTC
            's': start_dt,      # int, since, unix timestamp
            'u': end_dt,         # int, until, unix timestamp
            'i': '24h',         # string, frequency interval: 24h
            'timestamp_format': 'YYYY-MM-DD'
        }

        data = self.get_indicator_data('stock_to_flow_ratio', params)
        data.columns = ['date', 'timestamp', 'sth_mvrv']
        data[['sth_mvrv']] = data[['sth_mvrv']].astype(float)

        return data


if __name__ == "__main__":
    from btc_model.setting.setting import get_settings

    setting = get_settings('common')
    proxies = setting['proxies']

    instance = GlassnodeApiWrapper.get_instance(proxies)

    start_dt = '2024-01-01'
    end_dt = '2025-01-18'
    result = instance.get_s2f_data(start_dt, end_dt)
    print(result)
