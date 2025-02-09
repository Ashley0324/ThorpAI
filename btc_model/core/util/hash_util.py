"""
Author: guozq

Create Date: 2022/5/20

Description:

"""
import hashlib
from typing import Dict, List, Set, Tuple, Type, Any, Callable, Union


class HashUtil:
    @staticmethod
    def get_md5(input_str: str):
        m = hashlib.md5()
        m.update(input_str.encode())
        return m.hexdigest()

    @staticmethod
    def get_sha256(input_str: str):
        m = hashlib.sha256()
        m.update(input_str.encode())
        return m.hexdigest()

    @staticmethod
    def get_hash_str(input_str: Union[str, List[str]], hash_name: str = 'sha256'):
        m = hashlib.new(hash_name)
        if isinstance(input_str, str):
            m.update(input_str.encode())
        else:
            for s in input_str:
                m.update(s.encode())

        return m.hexdigest()


if __name__ == '__main__':
    result = HashUtil.get_hash_str(['dasfa', 'DFAF'])
    print(result)
