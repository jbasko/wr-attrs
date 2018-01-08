from wr_attrs import Attr, AttrContainer, BoundAttr


def test_container_attrs_returns_bound_attr():
    class C(AttrContainer):
        x = Attr()
        y = Attr()

    a = C()
    b = C()

    assert isinstance(a.attrs.x, BoundAttr)
    assert a.attrs.x._owner_ is a

    assert isinstance(b.attrs.x, BoundAttr)
    assert b.attrs.x._owner_ is b

    a.attrs.x.set('hello')
    assert a.x == 'hello'
    assert b.x is None

    b.attrs.x.set('world')
    assert b.x == 'world'
    assert a.x == 'hello'
