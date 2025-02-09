from concurrent.futures import ThreadPoolExecutor, wait
import threading


class MultiThreadDataProcessor:
    def __init__(self, thread_num=4):
        """
        多线程读取数据文件， 实例生成好之后，采用添加文件操作单元的方式传入读取函数字典，fileos_fun_dict, 然后在运行load_file
        文件操作单元为字典   unit

        文件操作单元： unit = {func: func_handle, param: {param1:xx, param2: xxx}}， 是需要添加到 __fileos_tasks 中

        func中如果有多个参数 param: {} 以字典传入，如果只有一个参数不用采用字典 直接 param: n， 如果没有参数，仍需要给param值，此时为 None

        文件任务集 __fileos_tasks = {

                                    'task_1': unit_1,
                                    'task_2': unit_2,
                                    ...

                                    }

        :param thread_num: 线程池线程数

        """
        # 线程池
        self.__pool = ThreadPoolExecutor(thread_num)
        self.__tasks = []

    def append_units(self, units):
        """
        添加文件操作函数列表

        unit = {func: func_handle, param: {param1:xx, param2: xxx}}

        func中如果有多个参数 param: {} 以字典传入，如果只有一个参数不用采用字典 直接 param: n， 如果没有参数，仍需要给param值，此时为 None

        :param units: [unit_1, unit_2, ... ]
        :return:
        """
        # 如果只传入一个字典
        if isinstance(units, dict):
            self.__tasks.append(units)

        # 如果传入列表，多个文件操作字典
        if isinstance(units, list):
            for s in units:
                self.__tasks.append(s)

    def run(self):
        """
        执行任务列表中的所有任务
        :return:
        """

        futures = []
        for task in self.__tasks:
            _func = task['func']
            _param = task['param']
            _tsk = self.__submit_task(_func, _param)
            futures.append(_tsk)

        wait(futures)

        data = []
        for s in futures:
            data.append(s.result())

        # 执行完毕后清楚文件任务list
        self.__tasks = []

        return data

    def __submit_task(self, _func, _param):
        if _param is None:
            # 可以默认空参数的文件读取
            return self.__pool.submit(_func)
        if isinstance(_param, dict):
            # 带有字典形式的文件读取
            return self.__pool.submit(_func, **_param)
        else:
            # 只传入一个值的参数
            return self.__pool.submit(_func, _param)
