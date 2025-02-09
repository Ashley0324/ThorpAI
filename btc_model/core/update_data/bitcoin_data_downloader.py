import os
import numpy as np
import pandas as pd
import datetime

from btc_model.core.common.const import (Exchange, Interval, EntityType, ProviderType)
from btc_model.core.wrapper.bitcoin_data_api_wrapper import BitcoinDataApiWrapper
from btc_model.core.update_data.base_downloader import BaseDownloader
from btc_model.core.util.log_util import Logger


class BitcoinDataDownloader(BaseDownloader):
    def __init__(self, proxies, output_dir):
        super().__init__(provider_type=ProviderType.BITCOIN_DATA, output_dir=output_dir)
        self.bitcoin_data_api_wrapper = BitcoinDataApiWrapper.get_instance(proxies=proxies)

    def _internal_download_indicator(self, indicator_id):
        # 按 Interval=DAILY 日频处理
        root_path = f"{self.output_dir}/indicator/{self.provider_type.value.lower()}/1d/"

        start_dt = '2010-01-01 00:00:00'
        end_dt = (datetime.datetime.today()).strftime('%Y-%m-%d 23:59:59')

        saved_data = pd.DataFrame()

        if os.path.exists(root_path):
            # 读取 Parquet 文件
            saved_data = pd.read_parquet(root_path)
            if len(saved_data) > 0 and indicator_id in saved_data.columns:
                start_dt = saved_data[indicator_id].dropna().index.get_level_values('date').max()

        if indicator_id == 'sth_mvrv':
            data = self.bitcoin_data_api_wrapper.get_sth_mvrv_data(start_dt, end_dt)
        elif indicator_id == 'mvrv_zscore':
            data = self.bitcoin_data_api_wrapper.get_mvrv_zscore_data(start_dt, end_dt)
        else:
            return None

        data = data[['date', indicator_id]]

        # 最后一天可能没更新，删除NA的记录
        data = data.dropna()

        self._internal_save_data(data=data,
                                 key_columns=['date'],
                                 partition_columns=None,
                                 entity_type=EntityType.INDICATOR,
                                 interval=Interval.DAILY,
                                 provider_type=ProviderType.BITCOIN_DATA
                                 )

        return data

    def download_sth_mvrv(self, **kwargs):
        data = self._internal_download_indicator('sth_mvrv')
        return data

    def download_mvrv_zero(self, **kwargs):
        data = self._internal_download_indicator('mvrv_zscore')
        return data

    def download_indicators(self):
        self.download_sth_mvrv()
        self.download_mvrv_zero()

if __name__ == "__main__":
    from btc_model.setting.setting import get_settings
    from btc_model.core.common.const import PROJECT_NAME
    from btc_model.core.util.file_util import FileUtil

    setting = get_settings('common')
    proxies = setting.get('proxies')

    output_dir = FileUtil.get_project_dir(project_name=PROJECT_NAME, sub_dir='data')
    downloader = BitcoinDataDownloader(output_dir=output_dir, proxies=proxies)

    # result = downloader.download_sth_mvrv()
    result = downloader.download_mvrv_zero()
    print(result)
