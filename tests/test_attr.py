import pytest

from wr_attrs import Attr


def test_repr():
    x = Attr(name='x')
    assert repr(x) == "<Attr 'x'>"


def test_cannot_set_nonexistent_attribute_of_attr():
    x = Attr()

    with pytest.raises(AttributeError):
        x.safe = True


def test_cannot_set_default_value_and_required_together():
    with pytest.raises(ValueError):
        Attr(required=True, default=1)
