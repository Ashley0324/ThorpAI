import os
import numpy as np
import pandas as pd
import datetime
import pyarrow as pa
import pyarrow.parquet as pq

from btc_model.core.common.const import (Exchange,
                                         Interval,
                                         InstrumentType,
                                         Product,
                                         EntityType,
                                         ProviderType
                                         )
from btc_model.core.wrapper.binance_api_wrapper import BinanceApiWrapper
from btc_model.core.update_data.base_downloader import BaseDownloader
from btc_model.core.util.log_util import Logger
from btc_model.core.util.file_util import FileUtil


class CryptoDataLoader():
    def __init__(self, data_directory):
        self.data_directory = data_directory

    def _internal_load_data(self,
                            exchange: Exchange,
                            entity_type: EntityType,
                            interval: Interval,
                            provider_type: ProviderType
                            ):
        root_path = FileUtil.get_local_entity_root_path(output_dir=self.data_directory,
                                                        entity_type=entity_type,
                                                        interval=interval,
                                                        exchange=exchange,
                                                        provider_type=provider_type
                                                        )
        if not os.path.exists(root_path):
            return None

        # 读取 Parquet 文件
        data = pd.read_parquet(root_path)
        data.reset_index(inplace=True)
        return data

    def load_instruments(self, exchange: Exchange):
        return self._internal_load_data(exchange=exchange,
                                        entity_type=EntityType.INSTRUMENT,
                                        interval=Interval.NONE,
                                        provider_type=ProviderType.NONE
                                        )

    def load_kline_data(self, exchange: Exchange, interval: Interval):
        return self._internal_load_data(exchange=exchange,
                                        entity_type=EntityType.KLINE,
                                        interval=interval,
                                        provider_type=ProviderType.NONE
                                        )

    def load_kline_index_data(self, exchange: Exchange, interval: Interval):
        return self._internal_load_data(exchange=exchange,
                                        entity_type=EntityType.KLINE_INDEX,
                                        interval=interval,
                                        provider_type=ProviderType.NONE
                                        )

    def load_indicator_data(self, exchange: Exchange, interval: Interval, provider_type: ProviderType):
        return self._internal_load_data(exchange=exchange,
                                        entity_type=EntityType.INDICATOR,
                                        interval=interval,
                                        provider_type=provider_type
                                        )


if __name__ == "__main__":
    from btc_model.core.common.const import PROJECT_NAME
    from btc_model.core.util.file_util import FileUtil

    output_dir = FileUtil.get_project_dir(project_name=PROJECT_NAME, sub_dir='data')

    data_loader = CryptoDataLoader(output_dir)
    result = data_loader.load_instruments(Exchange.OKX)
    print(result)

    Logger.info('loading kline data of exchange okx')
    result = data_loader.load_kline_data(Exchange.OKX, Interval.DAILY)
    print(result)

    Logger.info('loading index bar data of exchange okx')
    result = data_loader.load_kline_index_data(Exchange.OKX, Interval.DAILY)
    print(result)

    Logger.info('loading indicators of exchange okx')
    result = data_loader.load_indicator_data(Exchange.OKX, Interval.DAILY, ProviderType.OKX)
    print(result)

    for provider_type in [ProviderType.ALTERNATIVE, ProviderType.BITCOIN_DATA]:
        Logger.info(f'loading indicators of data provider {provider_type.value.lower()}')
        result = data_loader.load_indicator_data(Exchange.NONE, Interval.DAILY, provider_type=provider_type)
        print(result)
