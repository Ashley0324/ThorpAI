import os
import sys
import datetime
import logging
from logging import getLogger, Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler

from btc_model.core.common.const import PROJECT_NAME


class Logger:
    @staticmethod
    def config_logger():
        # 创建一个logging对象
        logger = getLogger()

        file_dir = f"{os.path.expanduser('~')}{os.sep}.{PROJECT_NAME}{os.sep}log"
        os.makedirs(file_dir, exist_ok=True)

        file_name = '{}{}{}_{}.txt'.format(
            file_dir,
            os.sep,
            'log',
            # os.path.basename(sys.argv[0]).split('.py')[0],
            str(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        )

        fh = TimedRotatingFileHandler(filename=file_name,
                                      when="MIDNIGHT",
                                      interval=1,
                                      backupCount=5)
        # 配置显示格式  可以设置两个配置格式  分别绑定到文件和屏幕上
        # 绑定到文件
        fh_formatter = Formatter('%(levelname)-7s: %(asctime)s %(filename)s[line:%(lineno)d] >>> %(message)s')
        fh.setFormatter(fh_formatter)  # 将格式绑定到两个对象上
        logger.addHandler(fh)  # 将handler绑定到logger
        # 创建一个屏幕对象
        sh = StreamHandler()
        sh_formatter = Formatter('%(levelname)-7s: %(asctime)s >>> %(message)s')
        sh.setFormatter(sh_formatter)
        logger.addHandler(sh)
        logger.setLevel(20)  # 总开关
        fh.setLevel(10)  # 写入文件的从10开始
        sh.setLevel(10)  # 在屏幕显示的从30开始

    @staticmethod
    def debug(logs, ui_log=None, ui_progress=None):
        logging.debug(logs)

    @staticmethod
    def info(logs, ui_log=None, ui_progress=None, ui_progress_int_value=None):
        logging.info(logs)

        # 给GUI使用，更新当前任务到日志和进度
        if ui_log is not None:
            if isinstance(logs, str):
                ui_log.emit(logs)
            if isinstance(logs, list):
                for iStr in logs:
                    ui_log.emit(iStr)

        if ui_progress is not None and ui_progress_int_value is not None:
            ui_progress.emit(ui_progress_int_value)

    @staticmethod
    def warning(logs, ui_log=None, ui_progress=None):
        logging.warning(logs)

    @staticmethod
    def error(logs, ui_log=None, ui_progress=None):
        logging.error(logs)


Logger.config_logger()
