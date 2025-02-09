import os
import numpy as np
import pandas as pd
import datetime

from btc_model.core.common.const import (Exchange, Interval, EntityType, ProviderType)
from btc_model.core.wrapper.alternative_api_wrapper import AlternativeApiWrapper
from btc_model.core.update_data.base_downloader import BaseDownloader
from btc_model.core.util.log_util import Logger


class AlternativeDownloader(BaseDownloader):
    def __init__(self, proxies, output_dir):
        super().__init__(provider_type=ProviderType.ALTERNATIVE, output_dir=output_dir)
        self._api_wrapper = AlternativeApiWrapper.get_instance(proxies=proxies)

    def _internal_download_indicator(self, indicator_id):
        # 按 Interval=DAILY 日频处理
        root_path = f"{self.output_dir}/{EntityType.INDICATOR.value.lower()}/{ProviderType.ALTERNATIVE.value.lower()}/1d/"

        start_dt = '2010-01-01 00:00:00'
        end_dt = (datetime.datetime.today()).strftime('%Y-%m-%d 23:59:59')

        saved_data = pd.DataFrame()

        if os.path.exists(root_path):
            # 读取 Parquet 文件
            saved_data = pd.read_parquet(root_path)
            if len(saved_data) > 0 and indicator_id in saved_data.columns:
                start_dt = saved_data[indicator_id].dropna().index.get_level_values('date').max()

        if indicator_id == 'FGI':
            data = self._api_wrapper.get_feargreed_data(start_dt, end_dt)
            # 仅保留feargreed_value
            data = data[['datetime', 'signal_type', 'value']]
            data.columns = ['date', 'fgi_signal', 'fgi']
        else:
            return None

        # 最后一天可能没更新，删除NA的记录
        data = data.dropna()

        self._internal_save_data(data=data,
                                 key_columns=['date'],
                                 partition_columns=None,
                                 entity_type=EntityType.INDICATOR,
                                 interval=Interval.DAILY,
                                 provider_type=self.provider_type
                                 )

        return data

    def download_feargreed(self, **kwargs):
        data = self._internal_download_indicator('FGI')
        return data

    def download_indicators(self):
        self.download_feargreed()

if __name__ == "__main__":
    from btc_model.setting.setting import get_settings
    from btc_model.core.common.const import PROJECT_NAME
    from btc_model.core.util.file_util import FileUtil

    setting = get_settings('common')
    proxies = setting.get('proxies')

    output_dir = FileUtil.get_project_dir(project_name=PROJECT_NAME, sub_dir='data')
    downloader = AlternativeDownloader(output_dir=output_dir, proxies=proxies)

    # result = downloader.download_sth_mvrv()
    result = downloader.download_feargreed()
    print(result)
