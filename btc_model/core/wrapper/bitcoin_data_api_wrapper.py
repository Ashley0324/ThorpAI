# -*- coding: utf-8 -*-
"""
Author: guozq

Create Date: 2025-01-19

Description:
    Wrapper for fetching data of indicators provided by BGeometrics (www.bitcoin-data.com).
    These indicators are freely available from BGeometrics but cannot be obtained for free through exchange APIs.

History:
    2025-01-19: initial version.
"""

import pandas as pd
import requests


class BitcoinDataApiWrapper(object):
    BASE_URL = "https://bitcoin-data.com"
    BASE_URL_V1 = BASE_URL + "/v1"
    STH_MVRV_URL = BASE_URL_V1 + '/sth_mvrv'


    __instance = None


    def __init__(self, proxies):
        self.proxies = proxies

    @classmethod
    def get_instance(cls, proxies):
        if cls.__instance is None:
            cls.__instance = cls(proxies)

        return cls.__instance

    def get_data(self, request_path, params):
        url = self.BASE_URL_V1 + '/' + request_path
        response = requests.get(url, params=params, proxies=self.proxies)

        if response.status_code == 200:
            data = response.json()

            data = pd.DataFrame(data)
            return data

        else:
            print("无法获取数据:", response.status_code, response.text)
            return None

    def get_sth_mvrv_data(self, start_dt, end_dt):
        params = {
            'startday': start_dt,
            'endday': end_dt
        }

        data = self.get_data('sth-mvrv', params)
        data.columns = ['date', 'timestamp', 'sth_mvrv']
        data[['sth_mvrv']] = data[['sth_mvrv']].astype(float)

        return data

    def get_sth_mvrv_zsccore_data(self, start_dt, end_dt):
        params = {
            'startday': start_dt,
            'endday': end_dt
        }

        data = self.get_data('mvrv-zscore', params)
        data.columns = ['date', 'timestamp', 'mvrv_zscore']
        data[['mvrv_zscore']] = data[['mvrv_zscore']].astype(float)

        return data

if __name__ == "__main__":
    instance = BitcoinDataApiWrapper.get_instance()

    start_dt = '2024-01-01'
    end_dt = '2025-01-18'
    result = instance.get_sth_mvrv_data(start_dt, end_dt)
    print(result)
