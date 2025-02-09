import os
import datetime
from typing import Union, List, Any, Optional, Coroutine, Callable, Tuple, Iterable

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from btc_model.core.common.const import PROJECT_NAME
from btc_model.core.common.const import (Exchange,
                                         Interval,
                                         InstrumentType,
                                         Product,
                                         EntityType,
                                         ProviderType
                                         )
from btc_model.core.common.context import Context

from btc_model.core.update_data.okx_downloader import OKxDownloader
from btc_model.core.update_data.binance_downloader import BinanceDownloader
from btc_model.core.update_data.bitcoin_data_downloader import BitcoinDataDownloader
from btc_model.core.update_data.alternative_downloader import AlternativeDownloader

from btc_model.core.data_loader.crypto_data_loader import CryptoDataLoader
from btc_model.core.util.log_util import Logger
from btc_model.core.util.file_util import FileUtil
from btc_model.setting.setting import get_settings

from btc_model.indicator.base_indicator import BaseIndicator
from btc_model.indicator.indicator_bollinger import IndicatorBollinger
from btc_model.indicator.indicator_macd import IndicatorMACD
from btc_model.indicator.indicator_mayer_multiple import IndicatorMayerMultiple
from btc_model.indicator.indicator_pi_cycle import IndicatorPiCycle
from btc_model.indicator.indicator_rsi import IndicatorRSI


class UpdateManager:
    """
    更新数据管理类
    为便于维护管理，采用逐天更新方式，并对缺失日期进行数据补齐
    """

    def __init__(self):
        self.data_directory = FileUtil.get_project_dir(project_name=PROJECT_NAME, sub_dir='data')

        self.downloader = dict()

        setting = get_settings('cex.okx')
        apikey = setting['apikey']
        secretkey = setting['secretkey']
        passphrase = setting['passphrase']
        proxy = setting['proxy']
        self.okx_downloader = OKxDownloader(apikey, secretkey, passphrase, proxy, output_dir=self.data_directory)
        self.downloader[Exchange.OKX] = self.okx_downloader

        setting = get_settings('cex.binance')
        apikey = setting['apikey']
        secretkey = setting['secretkey']
        self.binance_downloader = BinanceDownloader(apikey, secretkey, output_dir=self.data_directory)
        self.downloader[Exchange.BINANCE] = self.binance_downloader

        setting = get_settings('common')
        proxies = setting.get('proxies', None)
        self.bitcoin_data_downloader = BitcoinDataDownloader(output_dir=self.data_directory, proxies=proxies)
        self.downloader[ProviderType.BITCOIN_DATA] = self.bitcoin_data_downloader

        self.alternative_downloader = AlternativeDownloader(output_dir=self.data_directory, proxies=proxies)
        self.downloader[ProviderType.ALTERNATIVE] = self.alternative_downloader

        self.indicator_list = dict()
        setting = get_settings('escape_model.indicator.bollinger')
        self.indicator_list['IndicatorBollinger'] = IndicatorBollinger(**setting)
        setting = get_settings('escape_model.indicator.macd')
        self.indicator_list['IndicatorMACD'] = IndicatorMACD(**setting)
        setting = get_settings('escape_model.indicator.mayer_multiple')
        self.indicator_list['IndicatorMayerMultiple'] = IndicatorMayerMultiple(**setting)
        setting = get_settings('escape_model.indicator.pi_cycle')
        self.indicator_list['IndicatorPiCycle'] = IndicatorPiCycle(**setting)
        setting = get_settings('escape_model.indicator.rsi')
        self.indicator_list['IndicatorRSI'] = IndicatorRSI(**setting)

        # 获得计算各指标需要最少bar数量（日线）
        self.bar_size = max([x.get_minimum_bars() for x in self.indicator_list.values()])

    def _internal_save_data(self, data, key_columns, partition_columns, entity_type: EntityType,
                            exchange: Exchange, **kwargs):
        # 按 symbol_id进行分区存储
        if entity_type in [EntityType.KLINE, entity_type.KLINE_INDEX, entity_type.INDICATOR]:
            interval = kwargs.get('interval', None)
            if interval is None:
                raise Exception('Invalid argument, interval must not be empty!')

            root_path = f"{self.data_directory}/{entity_type.value.lower()}/{exchange.value.lower()}/{interval.value.lower()}"
        else:
            root_path = f"{self.data_directory}/{entity_type.value.lower()}/{exchange.value.lower()}/"

        if not os.path.exists(root_path):
            os.makedirs(root_path)

        # 读取已有的分区数据
        try:
            existing_df = pd.read_parquet(root_path)
            if len(existing_df) > 0:
                existing_df = existing_df.reset_index()
        except FileNotFoundError:
            existing_df = pd.DataFrame()

        # 合并新数据和旧数据，并去除重复行
        merged_df = pd.concat([existing_df, data], ignore_index=True)
        merged_df = merged_df.drop_duplicates(subset=key_columns, keep='first')
        merged_df.set_index(key_columns, inplace=True)
        # 将合并后的数据转换为 Arrow 表
        merged_df = pa.Table.from_pandas(merged_df)

        # 追加数据到指定目录和分区
        pq.write_to_dataset(table=merged_df,
                            partition_cols=partition_columns,
                            root_path=root_path,
                            existing_data_behavior='delete_matching'  # 删除匹配的分区并写入新数据
                            )

    # TODO: 待完善，需要更细的任务管理方式
    def download_exchange_data(self):
        """
        下载交易所（OKx、Binance））数据到本地文件，当前下载数据包括：
        1. 合约信息
        2. 币种K线（日)
        3. 指数K线（日）
        :return:
        """
        # exchange_list = [Exchange.OKX, Exchange.BINANCE]
        exchange_list = [Exchange.OKX]
        for exchange in exchange_list:
            # 下载合约信息，全量下载、存量更新&增量写入
            downloader = self.downloader[exchange]

            # ######################################################################
            # 1. 下载合约信息, 存量更新、增量追加
            Logger.info(f'startto download and update instrument data, exchange={exchange.value.lower()}')
            df_instrument = downloader.download_instruments()
            Logger.info(f'success download and update instrument data, exchange={exchange.value.lower()}')
            # ######################################################################

            # ######################################################################
            # 2. 下载历史日K线数据
            # 取上次最后更新日期，更新范围 (最后更新日期, 当前日期）
            Logger.info(f'startto download kline data, exchange={exchange.value.lower()}')

            start_dt = (downloader.get_last_update_date(entity_type=EntityType.KLINE,
                                                        exchange=exchange,
                                                        interval=Interval.DAILY,
                                                        provider_type=ProviderType.NONE
                                                        ) + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            end_dt = datetime.datetime.today().strftime('%Y-%m-%d 23:59:59')
            downloader.download_history_kline_data(df_instrument['instrument_id'].to_list(),
                                                   start_dt,
                                                   end_dt,
                                                   Interval.DAILY)

            Logger.info(f'success download kline data, exchange={exchange.value.lower()}')
            # ######################################################################

            # ######################################################################
            # 3. 下载指数历史日K线数据
            Logger.info(f'startto download index kline data, exchange={exchange.value.lower()}')

            start_dt = (downloader.get_last_update_date(entity_type=EntityType.KLINE_INDEX,
                                                        provider_type=ProviderType.NONE,
                                                        exchange=exchange,
                                                        interval=Interval.DAILY
                                                        ) + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            end_dt = datetime.datetime.today().strftime('%Y-%m-%d 23:59:59')
            downloader.download_history_index_kline_data(df_instrument['instrument_id'].to_list(),
                                                         start_dt,
                                                         end_dt,
                                                         Interval.DAILY)

            Logger.info(f'success download index kline data, exchange={exchange.value.lower()}')
            # ######################################################################

            # ######################################################################
            # 4. 下载历史分钟K线数据
            # 取上次最后更新日期，更新范围 (最后更新日期, 当前日期）
            # Logger.info(f'startto download 1 minute kline data, exchange={exchange.value.lower()}')
            #
            # start_dt = (downloader.get_last_update_date(EntityType.KLINE, exchange, Interval.MINUTE_1) + datetime.timedelta(minutes
            #     =1)).strftime('%Y-%m-%d %H:%M:%S')
            # end_dt = datetime.datetime.today().strftime('%Y-%m-%d 23:59:59')
            # downloader.download_history_kline_data(df_instrument['instrument_id'].to_list(),
            #                                        start_dt,
            #                                        end_dt,
            #                                        Interval.MINUTE_1)
            #
            # Logger.info(f'success download 1 minute kline data, exchange={exchange.value.lower()}')
            # ######################################################################

    def download_other_data(self):
        """
        下载其他从交易所数据无法获得或计算的数据，包括不容易计算的数据，通过第三方平台接口下载到本地：
        1. alternative 的 fear and greed index
        2. bitcoin data 的 sth_mvrv, mvrv_zscore
        :return:
        """
        for provider_type in [ProviderType.ALTERNATIVE, ProviderType.BITCOIN_DATA]:
            downloader = self.downloader[provider_type]
            downloader.download_indicators()

    def update_indicator(self):
        settings = get_settings('update_manager.indicator')
        exchange = settings.get('use_exchange', 'OKX')
        exchange = Exchange[exchange]
        symbols = settings.get('symbols', [])

        if len(symbols) == 0:
            Logger.warning('symbols is empty, will not update indicators!')
            return

        downloader = self.downloader[exchange]
        # 获取最新的KLine数据，假定Kline数据在此前已经正常更新好
        kline_data = downloader.load_index_kline_data(id_or_symbols=symbols, interval=Interval.DAILY)

        data_loader = CryptoDataLoader(self.data_directory)
        df_indicator = data_loader.load_indicator_data(exchange=exchange, interval=Interval.DAILY)

        if df_indicator is None or len(df_indicator) == 0:
            df_indicator = pd.DataFrame(
                columns=['datetime', 'symbol_id', 'open', 'high', 'low', 'close', 'insert_timestamp',
                         'modify_timestamp'])
            df_indicator[['datetime', 'symbol_id', 'open', 'high', 'low', 'close']] = kline_data[
                ['datetime', 'symbol_id', 'open', 'high', 'low', 'close']]
            df_indicator['insert_timestamp'] = datetime.datetime.now()
            df_indicator['modify_timestamp'] = datetime.datetime.now()
        else:
            df_indicator = pd.merge(
                df_indicator,
                kline_data[['datetime', 'symbol_id', 'open', 'high', 'low', 'close']],
                on=['datetime', 'symbol_id'],
                how='outer',
                suffixes=('', '_new')
            )

            # 更新 insert_timestamp 和 modify_timestamp
            df_indicator['modify_timestamp'] = datetime.datetime.now()
            df_indicator['insert_timestamp'] = df_indicator['insert_timestamp'].fillna(datetime.datetime.now())

            # 如果有新的数据，更新 open, high, low, close
            df_indicator['open'] = df_indicator['open_new'].combine_first(df_indicator['open'])
            df_indicator['high'] = df_indicator['high_new'].combine_first(df_indicator['high'])
            df_indicator['low'] = df_indicator['low_new'].combine_first(df_indicator['low'])
            df_indicator['close'] = df_indicator['close_new'].combine_first(df_indicator['close'])

            # 删除临时列
            df_indicator.drop(columns=['open_new', 'high_new', 'low_new', 'close_new'], inplace=True)

        context = Context()

        # 获取df_indicator中不同的symbol_id
        symbol_ids = df_indicator['symbol_id'].unique()
        for symbol_id in symbol_ids:
            kline_data_filtered = df_indicator[df_indicator['symbol_id'] == symbol_id]

            context.close_array = kline_data_filtered['close'].to_numpy()

            for indicator in self.indicator_list.values():
                tag = indicator.tag()  # 获得指标用于列名的tag
                # 计算指标
                indicator_data = indicator.compute(context=context, expect_df=True)
                # 设置indicator_data索引与kline_data_filtered相同，以便后续的检索、定位
                indicator_data.index = kline_data_filtered.index

                # 处理单列和多列返回值
                if isinstance(indicator_data, pd.Series):
                    # 单列数据
                    if tag not in df_indicator.columns:
                        df_indicator[tag] = None  # 如果tag列不存在，初始化

                    # 找到指标值为空的记录行
                    missing = df_indicator.loc[df_indicator['symbol_id'] == symbol_id, tag].isnull()
                    if missing.any():
                        df_indicator.loc[missing[missing].index, tag] = indicator_data.loc[
                            missing[missing].index, tag].values
                elif isinstance(indicator_data, pd.DataFrame):
                    # 多列数据
                    for col in indicator_data.columns:
                        full_tag = f"{tag}_{col}"  # 组合tag和列名，确保唯一性
                        if full_tag not in df_indicator.columns:
                            df_indicator[full_tag] = None  # 如果列不存在，初始化

                        missing = df_indicator[df_indicator['symbol_id'] == symbol_id][full_tag].isnull()  # 找到指标值为空的记录行
                        if missing.any():
                            df_indicator.loc[missing[missing].index, full_tag] = indicator_data.loc[
                                missing[missing].index, col].values
                else:
                    Logger.error(f"Unsupported indicator data type: {type(indicator_data)}")
                    continue

        # 将时间戳移动到最后
        columns = [col for col in df_indicator.columns if col not in ['insert_timestamp', 'modify_timestamp']]
        df_indicator = df_indicator[columns + ['insert_timestamp', 'modify_timestamp']]
        df_indicator = df_indicator.sort_values(by=['datetime', 'symbol_id'])
        df_indicator = df_indicator.reset_index(drop=True)

        self._internal_save_data(data=df_indicator,
                                 key_columns=['symbol_id', 'datetime'],
                                 partition_columns=['symbol_id'],
                                 entity_type=EntityType.INDICATOR,
                                 exchange=exchange,
                                 interval=Interval.DAILY
                                 )

        return df_indicator

    def run(self):
        update_manager.download_exchange_data()
        update_manager.download_other_data()
        update_manager.update_indicator()

if __name__ == "__main__":
    update_manager = UpdateManager()

    # update_manager.download_exchange_data()
    # update_manager.download_other_data()
    update_manager.update_indicator()
