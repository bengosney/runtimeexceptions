from strava.utils import MarkedString


def test_marked_string_str():
    ms = MarkedString("hello", "*")
    assert str(ms) == "*hello*"


def test_remove_from_text():
    ms = MarkedString("world", "#")
    text = "Say #world# loudly!"
    assert ms.remove_from_text(text) == "Say  loudly!"


def test_replace_in_text():
    ms = MarkedString("foo", "$")
    text = "This is $bar$ test."
    assert ms.replace_in_text(text) == "This is $foo$ test."


def test_replace_or_append_replace():
    ms = MarkedString("baz", "!")
    text = "Hello !old! friend."
    assert ms.replace_or_append(text) == "Hello !baz! friend."


def test_replace_or_append_append():
    ms = MarkedString("baz", "!")
    text = "Hello friend."
    assert ms.replace_or_append(text) == "Hello friend. !baz!"
