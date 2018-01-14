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


def test_update(xy_container_cls):
    c = xy_container_cls()
    c.attrs._update_(x=1, y=2)
    assert (c.x, c.y) == (1, 2)

    c.attrs._update_(x=3)
    assert (c.x, c.y) == (3, 2)

    c.attrs._update_()
    assert (c.x, c.y) == (3, 2)

    with pytest.raises(TypeError) as exc_info:
        xy_container_cls.attrs._update_(x=4)
    assert 'x on class is read-only' in str(exc_info.value)

    # pass dictionary
    c.attrs._update_({'x': 4, 'y': 5})
    assert (c.x, c.y) == (4, 5)


def test_cannot_update_non_attr(xy_container_cls):
    c = xy_container_cls()

    with pytest.raises(AttributeError):
        c.attrs._update_(z=5)  # attribute doesn't exist at all on c

    class D(xy_container_cls):
        z = 55

    d = D()
    with pytest.raises(AttributeError):
        d.attrs._update_(z=5)  # attribute on d is a non-Attr


@pytest.mark.parametrize('payload,kwargs,x_and_y,payload_after', [
    [{}, {}, (None, None), {}],
    [{'x': 1}, {}, (1, None), {'x': 1}],
    [{'x': 1, 'y': 2}, {'consume': True}, (1, 2), {}],
    [{'x': 1, 'y': 2}, {'consume': True, 'apply': False}, (None, None), {}],
    [{'z': 3}, {'ignore_unknown': True}, (None, None), {'z': 3}],
    [{'z': 3}, {}, (None, None), AttributeError],
    [{'x': 1, 'z': 3}, {'consume': True, 'ignore_unknown': True}, (1, None), {'z': 3}],
    [{'x': 1, 'z': 3}, {'consume': True, 'apply': False, 'ignore_unknown': True}, (None, None), {'z': 3}],
    [{'x': 1, 'z': 3}, {'consume': False, 'apply': True, 'ignore_unknown': True}, (1, None), {'x': 1, 'z': 3}],
    [{'x': 1, 'z': 3}, {}, (None, None), AttributeError],
])
def test_process(xy_container_cls, payload, kwargs, x_and_y, payload_after):
    c = xy_container_cls()

    if isinstance(payload_after, type) and issubclass(payload_after, Exception):
        with pytest.raises(payload_after):
            c.attrs._process_(payload, *kwargs)
    else:
        c.attrs._process_(payload, **kwargs)
        assert (c.x, c.y) == x_and_y
        assert payload == payload_after
