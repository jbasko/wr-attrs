import pytest

from wr_attrs import Attr, container


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


def test_init_value_called_once():
    @container
    class C:
        def __init__(self, *args, **kwargs):
            self.x_init_value_called = False
            super().__init__(*args, **kwargs)

        @Attr.init_value
        def x(self, attr, value):
            if self.x_init_value_called:
                raise AssertionError('x.init_value was already called!')
            self.x_init_value_called = True
            attr.value = value

    c3 = C(x=3)
    assert c3.x == 3

    c4 = C()
    c4.x = 4
    assert c4.x == 4

    c5 = C()
    assert c5.x is None
