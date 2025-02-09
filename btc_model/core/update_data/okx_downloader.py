import os
import numpy as np
import pandas as pd
import datetime
from typing import Union, List, Any, Optional, Coroutine, Callable, Tuple, Iterable
import concurrent
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from threading import Lock
import pyarrow as pa
import pyarrow.parquet as pq

# from logging import getLogger

from btc_model.core.common.const import Exchange, Interval, InstrumentType, Product, EntityType, ProviderType
from btc_model.core.util.log_util import Logger
from btc_model.core.wrapper.okx_api_wrapper import OKxApiWrapper

from btc_model.core.update_data.base_downloader import BaseDownloader


class OKxDownloader(BaseDownloader):
    def __init__(self, apikey, secretkey, passphrase, proxy, output_dir):
        super().__init__(provider_type=ProviderType.OKX, output_dir=output_dir)
        self.okx_api_wrapper = OKxApiWrapper.get_instance(apikey, secretkey, passphrase, proxy)

    def download_instruments(self, **kwargs):
        """
        下载加密货币产品信息
        :param kwargs:
        :return:
        """
        data = self.okx_api_wrapper.get_instruments()
        data = pd.DataFrame(data)
        data['instrument_type'] = data['instrument_type'].apply(lambda x: x.value)
        data['product'] = data['product'].apply(lambda x: x.value)

        self._internal_save_data(data=data,
                                 key_columns=['instrument_id'],
                                 partition_columns=None,
                                 entity_type=EntityType.INSTRUMENT,
                                 exchange=Exchange.OKX,
                                 provider_type=ProviderType.NONE
                                 )

        return data

    def download_history_kline_data(self, symbol_id: Union[str, List[str]], start_dt, end_dt, interval: Interval,
                                    **kwargs):
        if symbol_id is None:
            raise Exception('Invalid argument, symbol_id must not be empty!')

        symbols = symbol_id if isinstance(symbol_id, list) else [symbol_id]

        all_data = []
        for symbol_id in symbols:
            kline_data = self.okx_api_wrapper.get_history_kline_data(symbol_id, interval, start_dt, end_dt)

            if kline_data is not None and len(kline_data) > 0:
                all_data.append(kline_data)

        if len(all_data) > 0:
            kline_data = pd.concat(all_data, ignore_index=True)

            partition_columns = ['symbol_id']
            if interval in [Interval.MINUTE_1, Interval.MINUTE_5, Interval.MINUTE_15, Interval.MINUTE_30,
                            Interval.TICK]:
                partition_columns = ['symbol_id', 'date']

            self._internal_save_data(data=kline_data,
                                     key_columns=['symbol_id', 'datetime'],
                                     partition_columns=partition_columns,
                                     entity_type=EntityType.KLINE,
                                     exchange=Exchange.OKX,
                                     data_provider=ProviderType.OKX,
                                     interval=interval
                                     )

            return kline_data
        else:
            return None

    def download_history_index_kline_data(self, symbol_id: Union[str, List[str]], start_dt, end_dt, interval: Interval,
                                          **kwargs):
        if symbol_id is None:
            raise Exception('Invalid argument, symbol_id must not be empty!')

        symbols = symbol_id if isinstance(symbol_id, list) else [symbol_id]

        all_data = []
        for symbol_id in symbols:
            kline_data = self.okx_api_wrapper.get_history_index_kline_data(symbol_id, interval, start_dt, end_dt)

            if kline_data is not None and len(kline_data) > 0:
                all_data.append(kline_data)

        if len(all_data) > 0:
            kline_data = pd.concat(all_data, ignore_index=True)

            self._internal_save_data(data=kline_data,
                                     key_columns=['symbol_id', 'datetime'],
                                     partition_columns=['symbol_id'],
                                     entity_type=EntityType.KLINE_INDEX,
                                     exchange=Exchange.OKX,
                                     interval=interval
                                     )

            return kline_data
        else:
            return None

    def load_kline_data(self, symbol_id: Union[str, List[str], None], interval: Interval) -> pd.DataFrame:
        """
        加载存储的行情数据。
        :param symbol_id: 交易对符号，例如 'BTC-USDT'
        :param interval: 频率
        :return: Pandas DataFrame 格式的行情数据。
        """
        root_path = f"{self.output_dir}/kline/okx/{interval.value}/"

        if not os.path.exists(root_path):
            raise FileNotFoundError(f"file path not exists: {root_path}")

        if isinstance(symbol_id, str):
            filters = [("symbol_id", "==", symbol_id)]
        elif isinstance(symbol_id, list):
            filters = [("symbol_id", "in", symbol_id)]
        else:
            filters = None

        # 读取 Parquet 文件
        kline_data = pd.read_parquet(root_path, filters=filters)
        kline_data.reset_index(inplace=True)
        return kline_data

    def load_index_kline_data(self,
                              id_or_symbols: Union[str, List[str], None],
                              interval: Interval,
                              start_dt=None,
                              end_dt=None,
                              ) -> pd.DataFrame:
        """
        加载存储的行情数据。
        :param start_dt:
        :param end_dt:
        :param id_or_symbols: 交易对符号，例如 'BTC-USDT'
        :param interval: 频率
        :return: Pandas DataFrame 格式的行情数据。
        """

        root_path = f"{self.output_dir}/kline_index/okx/{interval.value}/"

        if not os.path.exists(root_path):
            raise FileNotFoundError(f"No data found for symbol: {id_or_symbols}")

        if isinstance(id_or_symbols, str):
            filters = [("symbol_id", "==", id_or_symbols)]
        elif isinstance(id_or_symbols, list):
            filters = [("symbol_id", "in", id_or_symbols)]
        else:
            filters = None

        # 读取 Parquet 文件
        kline_data = pd.read_parquet(root_path, filters=filters)
        kline_data.reset_index(inplace=True)
        return kline_data


if __name__ == "__main__":
    from btc_model.setting.setting import get_settings
    from btc_model.core.common.const import PROJECT_NAME
    from btc_model.core.util.file_util import FileUtil

    setting = get_settings('cex.okx')

    apikey = setting['apikey']
    secretkey = setting['secretkey']
    passphrase = setting['passphrase']
    proxy = setting['proxy']

    output_dir = FileUtil.get_project_dir(project_name=PROJECT_NAME, sub_dir='data')
    downloader = OKxDownloader(apikey, secretkey, passphrase, proxy, output_dir=output_dir)

    # result = downloader.load_instruments()
    # result = downloader.download_instruments()

    # symbol_id = 'BTC-USD'

    instruments = downloader.load_instruments(exchange=Exchange.OKX)
    instrument_ids = instruments['instrument_id'].tolist()

    start_dt = '2020-02-15 00:00:00'
    end_dt = '2024-12-31 23:59:59'

    result = downloader.download_history_kline_data(symbol_id=instrument_ids,
                                                    interval=Interval.DAILY,
                                                    start_dt=start_dt,
                                                    end_dt=end_dt
                                                    )

    # result = downloader.load_kline_data(symbol_id=['BTC-USDT', 'CAT-USDC'], interval=Interval.DAILY)

    # -------------------------------
    # result = downloader.get_latest_date(data_type='kline', interval=Interval.DAILY)
    print(result)
