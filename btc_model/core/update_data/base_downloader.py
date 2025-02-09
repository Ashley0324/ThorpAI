import numpy as np
import pandas as pd
import datetime
import abc
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

from btc_model.core.common.const import (Exchange,
                                         Interval,
                                         InstrumentType,
                                         Product,
                                         EntityType,
                                         ProviderType
                                         )


class BaseDownloader(abc.ABC):
    def __init__(self, provider_type: ProviderType, output_dir):
        self.provider_type = provider_type
        self.output_dir = output_dir

    def download_instruments(self, **kwargs):
        pass

    def download_history_kline_data(self, symbols: Union[str, List[str]], start_dt, end_dt, interval: Interval,
                                    **kwargs):
        pass

    def download_history_index_kline_data(self, symbols: Union[str, List[str]], start_dt, end_dt, interval: Interval,
                                          **kwargs):
        pass

    def load_instruments(self, exchange: Exchange):
        root_path = f"{self.output_dir}/instrument/{exchange.value.lower()}/"

        if not os.path.exists(root_path):
            raise FileNotFoundError(f"no instrument data found!")

        # 读取 Parquet 文件
        data = pd.read_parquet(root_path)
        data.reset_index(inplace=True)
        return data

    def get_last_update_date(self,
                             entity_type: EntityType,
                             provider_type: ProviderType,
                             interval: Interval,
                             exchange: Exchange = Exchange.NONE
                             ):
        root_path = self._internal_get_root_path(entity_type=entity_type,
                                                 interval=interval,
                                                 exchange=exchange,
                                                 provider_type=provider_type
                                                 )

        if not os.path.exists(root_path):
            return pd.to_datetime('2010-01-01 00:00:00')

        # 读取 Parquet 文件
        date_data = pd.read_parquet(root_path, columns=[])
        if date_data is None or len(date_data) == 0:
            return pd.to_datetime('2010-01-01 00:00:00')

        date_data = date_data.index.get_level_values('datetime')
        return date_data.max()

    def _internal_save_data(self,
                            data,
                            key_columns,
                            partition_columns,
                            entity_type: EntityType,
                            interval: Interval = Interval.NONE,
                            exchange: Exchange = Exchange.NONE,
                            provider_type: ProviderType = ProviderType.NONE,
                            **kwargs
                            ):

        root_path = self._internal_get_root_path(entity_type=entity_type,
                                                 interval=interval,
                                                 exchange=exchange,
                                                 provider_type=provider_type
                                                 )

        if not os.path.exists(root_path):
            os.makedirs(root_path)

        # 读取已有的分区数据
        try:
            existing_df = pd.read_parquet(root_path)
            if len(existing_df) > 0:
                existing_df = existing_df.reset_index()
        except FileNotFoundError:
            existing_df = pd.DataFrame()

        if len(existing_df) > 0:
            # 合并 DataFrame，保留所有列并根据 key 对齐
            merged_df = pd.merge(existing_df, data, on=key_columns, how='outer', suffixes=('_existing', '_new'))

            # 对相同列优先使用 data 中的值，如果 data 无此列，则使用 existing_df 中的值
            for col in merged_df.columns:
                if col.endswith('_existing'):
                    _col = col.split('_existing')[0]
                    merged_df[_col] = merged_df[col].fillna(merged_df[f'{_col}_new'])

                # 删除合并后的临时列
            merged_df.drop(
                columns=[col for col in merged_df.columns if col.endswith('_existing') or col.endswith('_new')],
                inplace=True)
        else:
            merged_df = data

        merged_df.set_index(key_columns, inplace=True)

        # 将合并后的数据转换为 Arrow 表
        merged_df = pa.Table.from_pandas(merged_df)

        # 追加数据到指定目录和分区
        pq.write_to_dataset(table=merged_df,
                            partition_cols=partition_columns,
                            root_path=root_path,
                            existing_data_behavior='delete_matching'  # 删除匹配的分区并写入新数据
                            )

    def _internal_get_root_path(self,
                                entity_type: EntityType,
                                interval: Interval,
                                exchange: Exchange,
                                provider_type: ProviderType
                                ):
        if entity_type in [EntityType.INSTRUMENT]:
            if exchange is None or exchange == Exchange.NONE:
                raise Exception('Invalid argument, exchange must not be empty or none!')
            root_path = f"{self.output_dir}/{entity_type.value.lower()}/{exchange.value.lower()}"
        elif entity_type in [EntityType.KLINE, entity_type.KLINE_INDEX]:
            if exchange is None or exchange == Exchange.NONE:
                raise Exception('Invalid argument, exchange must not be empty or none!')

            if interval is None or interval == Interval.NONE:
                raise Exception('Invalid argument, interval must not be empty or none!')

            root_path = f"{self.output_dir}/{entity_type.value.lower()}/{exchange.value.lower()}/{interval.value.lower()}"
        elif entity_type in [EntityType.INDICATOR]:
            if interval is None:
                raise Exception('Invalid argument, interval must not be empty or none!')

            root_path = f"{self.output_dir}/{entity_type.value.lower()}/{provider_type.value.lower()}/{interval.value.lower()}"
        else:
            root_path = f"{self.output_dir}/{entity_type.value.lower()}/{provider_type.value.lower()}"

        return root_path
