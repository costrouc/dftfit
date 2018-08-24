import json
import re

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        """
        if input object is a ndarray it will be converted into a dict holding dtype, shape and the data base64 encoded
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder(self, obj)


def get_naive_attr_path(d, attr_path):
    """ Allow simple nested dict key access

    example: "pair.1.parameters.1.coefficients.2"
    """
    attr_keys = attr_path.split('.')
    current_path = []
    try:
        for key in attr_keys:
            current_path.append(key)
            if re.match('[0-9]+', key):
                d = d[int(key)]
            else:
                d = d[key]
    except (IndexError, KeyError, TypeError):
        raise Exception('key path %s does not exist in dictionary or list' % '.'.join(current_path))
    return d


def set_naive_attr_path(d, attr_path, value):
    """ Allow simple nested dict key access

    example: "pair.1.parameters.1.coefficients.2"
    """
    *attr_keys, last_key = attr_path.split('.')
    current_path = []
    try:
        for key in attr_keys:
            current_path.append(key)
            if re.match('[0-9]+', key):
                d = d[int(key)]
            else:
                d = d[key]
        d[last_key] = value
    except (IndexError, KeyError, TypeError):
        raise Exception('key path %s does not exist in dictionary or list' % '.'.join(current_path))
