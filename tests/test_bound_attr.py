from wr_attrs import Attr, AttrContainer, BoundAttr


class C(AttrContainer):
    x = Attr()
    y = Attr()


def test_container_attrs_provides_bound_attrs():
    c = C(y=2)

    cx = c.attrs.x
    cy = c.attrs.y

    assert isinstance(cx, BoundAttr)
    assert isinstance(cy, BoundAttr)


def test_set_get():
    c = C(y=3)
    d = C(y=3)

    cx, cy = c.attrs.x, c.attrs.y
    dx, dy = d.attrs.x, d.attrs.y

    cx.set(5)
    assert (c.x, c.y) == (5, 3)
    assert (d.x, d.y) == (None, 3)

    assert (cx.get(), cy.get()) == (5, 3)

    dy.set('hello')
    assert (c.x, c.y) == (5, 3)
    assert (d.x, d.y) == (None, 'hello')

    assert (dx.get(), dy.get()) == (None, 'hello')


def test_value_property():
    c = C()

    cx = c.attrs.x
    assert cx.value is None
    assert c.x is None

    cx.value = 5
    assert c.x == 5
    assert cx.value == 5


def test_has_value_property():
    c = C()

    d = C(x=2)

    e = C()
    e.x = None

    f = C(x=None)

    assert not c.attrs.x.has_value
    assert d.attrs.x.has_value
    assert e.attrs.x.has_value
    assert f.attrs.x.has_value
