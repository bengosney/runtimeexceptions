from runtimeexceptions.utils import deep_merge


def test_deep_merge_simple():
    a = {"x": 1, "y": 2}
    b = {"y": 3, "z": 4}
    result = deep_merge(a, b)
    assert result == {"x": 1, "y": 3, "z": 4}
    assert a == {"x": 1, "y": 2}  # original dict unchanged


def test_deep_merge_nested():
    a = {"x": {"y": 1}, "z": 2}
    b = {"x": {"y": 2, "w": 3}, "z": 4}
    result = deep_merge(a, b)
    assert result == {"x": {"y": 2, "w": 3}, "z": 4}


def test_deep_merge_empty_source():
    a = {"x": 1}
    b = {}
    result = deep_merge(a, b)
    assert result == {"x": 1}


def test_deep_merge_empty_target():
    a = {}
    b = {"x": 1}
    result = deep_merge(a, b)
    assert result == {"x": 1}


def test_deep_merge_non_dict_overwrite():
    a = {"x": {"y": 1}}
    b = {"x": 2}
    result = deep_merge(a, b)
    assert result == {"x": 2}


def test_deep_merge_lists():
    a = {"x": [1, 2]}
    b = {"x": [3, 4]}
    result = deep_merge(a, b)
    assert result == {"x": [3, 4]}


def test_deep_merge_multiple_levels():
    a = {"a": {"b": {"c": 1}}}
    b = {"a": {"b": {"d": 2}}}
    result = deep_merge(a, b)
    assert result == {"a": {"b": {"c": 1, "d": 2}}}
