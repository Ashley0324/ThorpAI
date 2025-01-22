# -- coding: utf-8 --
import os

from logging import getLogger, Formatter, StreamHandler
from logging.handlers import TimedRotatingFileHandler

def config_logger():
    # 创建一个logging对象
    logger = getLogger()
    # 创建一个文件对象  创建一个文件对象,以UTF-8 的形式写入 标配版.log 文件中
    # fh = logging.FileHandler('log.txt',encoding='utf-8')
    file_dir = 'logs'
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    fh = TimedRotatingFileHandler(f'{file_dir}\\log.txt',
                                  when="MIDNIGHT",
                                  interval=1,
                                  backupCount=5)
    # 配置显示格式  可以设置两个配置格式  分别绑定到文件和屏幕上
    #绑定到文件
    fh_formatter = Formatter('%(levelname)s: %(asctime)s %(filename)s[line:%(lineno)d]  \n%(message)s')
    fh.setFormatter(fh_formatter)  # 将格式绑定到两个对象上
    logger.addHandler(fh)  # 将handler绑定到logger
    # 创建一个屏幕对象
    sh = StreamHandler()
    sh_formatter = Formatter('%(levelname)s: %(asctime)s %(message)s')
    sh.setFormatter(sh_formatter)
    logger.addHandler(sh)
    logger.setLevel(10)  # 总开关
    fh.setLevel(10)  # 写入文件的从10开始
    sh.setLevel(10)  # 在屏幕显示的从30开始
