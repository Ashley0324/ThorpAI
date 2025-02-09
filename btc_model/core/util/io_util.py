import datetime
import json
import os
import pickle

# from WindPy import *
import pandas as pd
import abc


class BaseIO(metaclass=abc.ABCMeta):
    """
    数据IO基类
    """

    @abc.abstractmethod
    def save_file(self, object_to_save, filename):
        """
        存放数据到本地文件
        """
        pass

    @abc.abstractmethod
    def load_file(self, filename):
        """
        从本地文件导入数据
        :param filename:
        :return:
        """
        pass


class Data_IO(object):
    """
    统一数据IO操作，包括导入、导出数据，数据间相互转换
    """

    def save_file(self, class_type, object_to_save, filename):
        """
        保存数据到本地文件，类型可能为csv、txt、pickle
        """
        class_type.save_file(object_to_save, filename)

    def Load_file(self, class_type, filename):
        ret = class_type.load_file(filename)
        return ret


class IOPickle(BaseIO):
    """
    pickle IO操作
    """

    def save_file(self, object_to_save, filename):
        if os.path.splitext(filename)[-1] == '':
            filename = filename + '.pkl'

        with open(filename, 'wb') as (output):
            pickle.dump(object_to_save, output, pickle.HIGHEST_PROTOCOL)

    def load_file(self, filename):
        if os.path.splitext(filename)[-1] == '':
            filename = filename + '.pkl'

        with open(filename, 'rb') as (input):
            object_to_load = pickle.load(input)
        return object_to_load


class IOCsv(BaseIO):
    """
    CSV IO操作
    """

    def save_file(self, object_to_save, filename, index=False):
        if os.path.splitext(filename)[-1] == '':
            filename = filename + '.csv'

        if isinstance(object_to_save, pd.core.frame.DataFrame):
            object_to_save.to_csv(filename, index=index, encoding='gbk')
        else:
            raise TypeError('save csv file--input data type error, not pd.DataFrame')

    def load_file(self, filename, index_col=None, header=None):
        if os.path.splitext(filename)[-1] == '':
            filename = filename + '.csv'

        object_to_load = pd.read_csv(filename, encoding='gbk', index_col=index_col, header=header)
        return object_to_load


class IOText(BaseIO):
    """
    TXT IO操作
    """

    def save_file(self, object_to_save, filename):
        with open(filename, 'w') as (f):
            f.write(object_to_save)

    def load_file(self, filename):
        with open(filename, 'r') as (f):
            textRead = f.read()
        return textRead

    def read_text(self, path):
        with open(path, 'r') as (f):
            textRead = f.read()
        return textRead

    def write_text(self, path, ContentToWrite, line_wrap=False):
        with open(path, 'w') as (f):
            f.write(ContentToWrite if line_wrap is False else ContentToWrite + '\n')

    def write_text_by_add(self, path, ContentToWrite):
        if os.path.exists(path) is False:
            self.write_text(path, ContentToWrite, True)
            return
        with open(path, 'a+') as (f):
            f.write(ContentToWrite + '\n')


class IOJson(BaseIO):
    """
    Json IO操作
    """

    def load_file(self, filename):
        with open(filename, 'r') as load_f:
            load_dict = json.load(load_f)
        return load_dict

    def save_file(self, object_to_save, filename):
        with open(filename, "w") as f:
            json.dump(object_to_save, f)



io_pickle = IOPickle()
io_csv = IOCsv()
io_text = IOText()
io_json = IOJson()
