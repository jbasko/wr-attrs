import pytest


def test_repr(xy_container_cls):
    c = xy_container_cls()
    assert '<BoundAttr C.x>' == repr(c.attrs.x)


def test_class_bound_attr_has_no_value(xy_container_cls):
    with pytest.raises(TypeError):
        _ = xy_container_cls.attrs.x.value  # noqa
