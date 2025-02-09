
from pathlib import Path
import json

from btc_model.core.common.const import (Exchange,
                                         Interval,
                                         InstrumentType,
                                         Product,
                                         EntityType,
                                         ProviderType
                                         )

class FileUtil:
    """
    读写操作类
    """

    @staticmethod
    def get_project_dir(project_name: str, sub_dir: str = None):
        """
        """
        home_path = Path.home()
        project_path = home_path.joinpath('.' + project_name)

        if not project_path.exists():
            project_path.mkdir()

        if sub_dir is not None:
            project_path = project_path.joinpath(sub_dir)

            if not project_path.exists():
                project_path.mkdir()

        return project_path

    @staticmethod
    def load_json(filename: str) -> dict:
        """
        Load data from json file in temp path.
        """
        filepath = Path(filename)

        if filepath.exists():
            with open(filepath, mode="r", encoding="UTF-8") as f:
                data = json.load(f)
            return data
        else:
            FileUtil.save_json(filename, {})
            return {}

    @staticmethod
    def save_json(filename: str, data: dict) -> None:
        """
        Save data into json file in temp path.
        """
        filepath = Path(filename)

        with open(filepath, mode="w+", encoding="UTF-8") as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

    @staticmethod
    def get_local_entity_root_path(output_dir: str,
                                entity_type: EntityType,
                                interval: Interval,
                                exchange: Exchange,
                                provider_type: ProviderType
                                ):
        if entity_type in [EntityType.INSTRUMENT]:
            if exchange is None or exchange == Exchange.NONE:
                raise Exception('Invalid argument, exchange must not be empty or none!')
            root_path = f"{output_dir}/{entity_type.value.lower()}/{exchange.value.lower()}"
        elif entity_type in [EntityType.KLINE, entity_type.KLINE_INDEX]:
            if exchange is None or exchange == Exchange.NONE:
                raise Exception('Invalid argument, exchange must not be empty or none!')

            if interval is None or interval == Interval.NONE:
                raise Exception('Invalid argument, interval must not be empty or none!')

            root_path = f"{output_dir}/{entity_type.value.lower()}/{exchange.value.lower()}/{interval.value.lower()}"
        elif entity_type in [EntityType.INDICATOR]:
            if interval is None:
                raise Exception('Invalid argument, interval must not be empty or none!')

            root_path = f"{output_dir}/{entity_type.value.lower()}/{provider_type.value.lower()}/{interval.value.lower()}"
        else:
            root_path = f"{output_dir}/{entity_type.value.lower()}/{provider_type.value.lower()}"

        return root_path