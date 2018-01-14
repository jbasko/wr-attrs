import pytest

from wr_attrs import Attr, Attrs, container


def test_attrs_cls_names_is_a_property():
    assert isinstance(Attrs._names_, property)


def test_attrs_cls_all_is_a_property():
    assert isinstance(Attrs._all_, property)


def test_attrs_cls_tagged_is_a_property():
    assert callable(Attrs._tagged_)


def test_cannot_access_non_attr_via_attrs():
    @container
    class C:
        x = Attr()
        y = 10  # non-attr

    c = C()

    with pytest.raises(AttributeError) as exc_info:
        _ = C.attrs.y  # noqa
    assert 'C.y is not an Attr' in str(exc_info.value)

    with pytest.raises(AttributeError) as exc_info:
        _ = c.attrs.y  # noqa
    assert 'C.y is not an Attr' in str(exc_info.value)


def test_cannot_reset_attr_on_attrs(xy_container_cls):
    with pytest.raises(AttributeError):
        xy_container_cls.attrs.x = Attr('x', default=100)


def test_cannot_reset_attrs(xy_container_cls):
    c = xy_container_cls()

    with pytest.raises(AttributeError) as exc_info:
        c.attrs = Attrs(c)

    assert 'C.attrs is read-only' in str(exc_info.value)
