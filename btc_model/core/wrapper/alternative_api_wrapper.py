# -*- coding: utf-8 -*-
"""
Author: guozq

Create Date: 2025-01-19

Description:
    Wrapper for fetching data of indicators provided by alternative (https://alternative.me).
    These indicators are freely available from alternative but cannot be obtained for free through exchange APIs.

History:
    2025-01-19: initial version.
"""


import pandas as pd
import requests


class AlternativeApiWrapper(object):
    BASE_URL = "https://api.alternative.me"

    __instance = None


    def __init__(self, proxies=None):
        self._proxies = proxies

    @classmethod
    def get_instance(cls, proxies=None):
        if cls.__instance is None:
            cls.__instance = cls(proxies)

        return cls.__instance

    def get_data(self, request_path, params):
        url = self.BASE_URL + '/' + request_path
        response = requests.get(url, params=params, proxies=self._proxies)

        if response.status_code == 200:
            data = response.json()

            data = pd.DataFrame(data['data'])
            return data

        else:
            print("无法获取数据:", response.status_code, response.text)
            return None

    def get_feargreed_data(self, start_dt, end_dt):
        start_dt = pd.to_datetime(start_dt)
        end_dt = pd.to_datetime(end_dt)

        current_date = pd.Timestamp.now()

        date_diff = (current_date - start_dt).days

        params = {
            'limit': date_diff,
            'date_format': 'cn'
        }

        data = self.get_data('fng/', params)
        data[['value']] = data[['value']].astype(int)
        data = data.rename(columns={'timestamp': 'datetime', 'value_classification': 'signal_type'})
        data = data[['datetime', 'signal_type', 'value', 'time_until_update']]
        data = data.sort_values('datetime')

        return data



if __name__ == "__main__":
    instance = AlternativeApiWrapper.get_instance()

    start_dt = '2024-01-01'
    end_dt = '2025-01-18'
    result = instance.get_feargreed_data(start_dt, end_dt)
    print(result)
