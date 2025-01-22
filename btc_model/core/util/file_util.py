# -*- coding: utf-8 -*-
"""
Author: guozq

Create Date: 2025/01/19

Description:

"""

from pathlib import Path
import json


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
