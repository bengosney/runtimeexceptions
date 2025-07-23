import collections.abc


def deep_merge(target_dict, source_dict):
    """
    Recursively merges source_dict into target_dict.
    Nested dictionaries are merged; other types are overwritten.
    Modifies target_dict in place.
    """
    for key, value in source_dict.items():
        if isinstance(value, collections.abc.Mapping):
            target_dict[key] = deep_merge(target_dict.get(key, {}), value)
        else:
            target_dict[key] = value
    return target_dict
