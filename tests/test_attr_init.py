from wr_attrs import Attr, AttrContainer, BoundAttr


class C(AttrContainer):
    x = Attr()

    @x.init
    def x(self, attr: BoundAttr, value=None):
        attr.set(value.upper() if value else 'NOT_SET')


def test_attr_has_value():
    c1 = C()
    assert not c1.attrs.has_value('x')
    c1.x = 'ha'
    assert c1.attrs.has_value('x')

    c2 = C(x='ba')
    assert c2.attrs.has_value('x')
    c2.x = ''
    assert c2.attrs.has_value('x')
    c2.x = None
    assert c2.attrs.has_value('x')

    c3 = C(x=None)
    assert c3.attrs.has_value('x')


def test_attr_init_is_called_on_first_access_only():
    c1 = C()
    assert c1.x == 'NOT_SET'
    c1.x = 'hello'
    assert c1.x == 'hello'

    c2 = C(x='hello')
    assert c2.x == 'HELLO'
    c2.x = 'world'
    assert c2.x == 'world'

    c3 = C()
    c3.x = 'hello'
    assert c3.x == 'HELLO'
    c3.x = 'hello'
    assert c3.x == 'hello'

    c4 = C()
    c4.attrs.update(x='world')
    assert c4.x == 'WORLD'
    c4.x = 'world'
    assert c4.x == 'world'


def test_attr_init_is_called_with_default_value():
    class D(C):
        x = 'hello world'

    assert D.x.default == 'hello world'

    d = D()
    assert not d.attrs.has_value('x')
    assert d.x == 'HELLO WORLD'

    d.x = 'not default'
    assert d.x == 'not default'
