import numpy as np
import pandas as pd
import datetime

from btc_model.core.common.const import (Exchange, Interval, EntityType, ProviderType)
from btc_model.core.wrapper.binance_api_wrapper import BinanceApiWrapper
from btc_model.core.update_data.base_downloader import BaseDownloader
from btc_model.core.util.log_util import Logger



class BinanceDownloader(BaseDownloader):
    def __init__(self, apikey, secretkey, output_dir):
        super().__init__(provider_type=ProviderType.BINANCE, output_dir=output_dir)
        self.binance_api_wrapper = BinanceApiWrapper.get_instance(apikey=apikey, secretkey=secretkey)

    def download_instruments(self, **kwargs):
        """
        下载加密货币产品信息
        :param kwargs:
        :return:
        """
        data = self.binance_api_wrapper.get_instruments()
        data = pd.DataFrame(data)
        data['instrument_type'] = data['instrument_type'].apply(lambda x: x.value)
        data['product'] = data['product'].apply(lambda x: x.value)

        self._internal_save_data(data=data,
                                 key_columns=['instrument_id'],
                                 partition_columns=None,
                                 entity_type=EntityType.INSTRUMENT,
                                 exchange=Exchange.BINANCE,
                                 data_provider=ProviderType.BINANCE
                                 )

        return data

    def download_history_kline_data(self, symbol_id, start_dt, end_dt, interval: Interval, **kwargs):
        if symbol_id is None:
            raise Exception('Invalid argument, symbol_id must not be empty!')

        symbols = symbol_id if isinstance(symbol_id, list) else [symbol_id]

        all_data = []
        for symbol_id in symbols:
            Logger.info(f'getting kline from binance, symbol_id={symbol_id}')
            kline_data = self.binance_api_wrapper.get_history_kline_data(symbol_id, interval, start_dt, end_dt)

            if kline_data is not None and len(kline_data) > 0:
                all_data.append(kline_data)

        if len(all_data) > 0:
            kline_data = pd.concat(all_data, ignore_index=True)

            self._internal_save_data(data=kline_data,
                                     key_columns=['symbol_id', 'datetime'],
                                     partition_columns=['symbol_id'],
                                     entity_type=EntityType.KLINE,
                                     interval=interval,
                                     exchange=Exchange.BINANCE,
                                     data_provider=ProviderType.BINANCE
                                     )

            return kline_data
        else:
            return None

    def download_history_index_kline_data(self, symbol_id, start_dt, end_dt, interval: Interval, **kwargs):
        if symbol_id is None:
            raise Exception('Invalid argument, symbol_id must not be empty!')

        symbols = symbol_id if isinstance(symbol_id, list) else [symbol_id]

        all_data = []
        for symbol_id in symbols:
            kline_data = self.binance_api_wrapper.get_history_index_kline_data(symbol_id, interval, start_dt, end_dt)

            if kline_data is not None and len(kline_data) > 0:
                all_data.append(kline_data)

        if len(all_data) > 0:
            kline_data = pd.concat(all_data, ignore_index=True)

            self._internal_save_data(data=kline_data,
                                     key_columns=['symbol_id', 'datetime'],
                                     partition_columns=['symbol_id'],
                                     entity_type=EntityType.KLINE_INDEX,
                                     interval=interval,
                                     exchange=Exchange.BINANCE,
                                     data_provider=ProviderType.BINANCE
                                     )

            return kline_data
        else:
            return None


if __name__ == "__main__":
    from btc_model.setting.setting import get_settings
    from btc_model.core.common.const import PROJECT_NAME
    from btc_model.core.util.file_util import FileUtil

    setting = get_settings('cex.okx')

    apikey = setting['apikey']
    secretkey = setting['secretkey']

    output_dir = FileUtil.get_project_dir(project_name=PROJECT_NAME, sub_dir='data')
    downloader = BinanceDownloader(apikey, secretkey, output_dir=output_dir)

    # result = downloader.download_instruments()
    # print(result)

    # symbol_id = 'BTCUSDT'
    # start_dt = '2024-01-01 00:00:00'
    # end_dt = '2025-01-18 23:59:59'
    # result = downloader.download_history_kline_data(symbol_id=symbol_id, interval=Interval.DAILY, start_dt=start_dt,
    #                                                 end_dt=end_dt)

    # symbol_id = 'BTCUSDT'
    # start_dt = '2024-01-01 00:00:00'
    # end_dt = '2025-01-18 23:59:59'
    # result = downloader.download_history_index_kline_data(symbol_id=symbol_id, interval=Interval.DAILY, start_dt=start_dt,
    #                                                       end_dt=end_dt)

    instruments = downloader.load_instruments(Exchange.BINANCE)
    instrument_ids = instruments['instrument_id'].tolist()

    start_dt = '2020-02-15 00:00:00'
    end_dt = '2024-12-31 23:59:59'

    result = downloader.download_history_kline_data(symbol_id=instrument_ids,
                                                    interval=Interval.DAILY,
                                                    start_dt=start_dt,
                                                    end_dt=end_dt
                                                    )

    print(result)
