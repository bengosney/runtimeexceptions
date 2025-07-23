import collections.abc
import copy


def deep_merge(target_dict, source_dict):
    """
    Recursively merges source_dict into target_dict.
    Nested dictionaries are merged; other types are overwritten.
    Modifies target_dict in place.
    """
    merged_dict = copy.deepcopy(target_dict)
    for key, value in source_dict.items():
        if isinstance(value, collections.abc.Mapping):
            merged_dict[key] = deep_merge(merged_dict.get(key, {}), value)
        else:
            merged_dict[key] = value
    return merged_dict
