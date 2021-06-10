import argparse


class AttDict(dict):
    """
    Object that adds to a regular dict the ability to refer to the keys as if they were attributes.
    Doctest:
    >>> d_ = {'orange': 'acid', \
              'pear':'sweet'}
    >>> d = AttDict(d_)
    >>> d['chocolate'] = 'super_yummy!'
    >>> d.chocolate
    'super_yummy!'
    >>> d['chocolate']
    'super_yummy!'
    >>> {k:v for k, v in d.items()}
    {'orange': 'acid', 'pear': 'sweet', 'chocolate': 'super_yummy!'}
    """

    def __init__(self, d, **kwargs):
        if isinstance(d, argparse.Namespace):
            d = d.__dict__
        super().__init__(**kwargs)
        for att_name in d.keys():
            self.__setitem__(att_name, d[att_name])

    # def __getattr__(self, item):
    #     return self[item]  # if item in self.keys() else dict.__getattr__(item)

    def __getattr__(self, item):
        return self.__getitem__(item)  # if item in self.keys() else dict.__getattr__(item)

    def __setattr__(self, key, value):
        return self.__setitem__(key, value)

    def __copy__(self) -> 'AttDict':
        return AttDict(super().copy())

    # def __getattribute__(self, item):
    #     return self.__getitem__(item)  # if item in self.keys() else dict.__getattr__(item)


class InstanceDict:
    """
    Object that mimicks a regular dict syntax but matches key-value pairs by referencing the same parent class.
    Elegant but not high performant at all.
    """
    """
    Doctest:
    >>> import pandas as pd
    >>> df = pd.DataFrame({'col1': [1,2,3], 'col2': [10, 20, 30]})
    >>> d_ = {str: 'string', \
              int: 'integer'}
    >>> d = InstanceDict(d_)
    >>> d[pd.DataFrame] = 'pandas!'
    >>> d[df]
    'pandas!'
    >>> d['chocolate']
    'string'
    >>> {k:v for k, v in d.items()}
    {str: 'string', int: 'integer', pd.DataFrame: 'pandas!'}
    """

    def __init__(self, dict_):
        self.D = dict_

    def __getitem__(self, item):
        for k, v in self.D.items():
            if item is k or isinstance(item, k):
                return v
        raise KeyError(item)

    def keys(self):
        return self.D.keys()

    def items(self):
        return self.D.items()

    def values(self):
        return self.D.values()

    def get(self, key, default):
        try:
            return self[key]
        except KeyError:
            return default
