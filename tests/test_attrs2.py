from copy import copy

import pytest

from wr_attrs import Attr, Attrs, BoundAttr, container


def test_basics():
    @container
    class C:
        x = Attr('x')
        y = Attr('y')
        z = Attr('z', required=True)

    c = C()

    assert c.x is None
    assert c.attrs.x.name == 'x'
    assert c.attrs.x.required is False
    assert c.attrs.x.default is None
    assert c.attrs.x.value is None

    assert c.y is None

    c.x = 5
    assert c.x == 5
    c.y = 6
    assert c.y == 6

    assert c.attrs.x.value == 5

    assert c.attrs.z.required is True
    with pytest.raises(ValueError):
        _ = c.z  # noqa


def test_init_value_decorator():
    @container
    class C:
        @Attr.init_value
        def x(self, attr):
            attr.value = 5

        y = Attr()

        @y.init_value
        def y(self, attr):
            attr.value = 20

    c = C()

    assert c.x == 5

    c.x = 10
    assert c.x == 10

    assert c.y == 20


def test_get_value_decorator():
    @container
    class C:
        @Attr.get_value
        def x(self, attr):
            return attr.value * 5 if attr.value else attr.value

        y = Attr()

        @y.get_value
        def y(self, attr):
            return attr.value * 2 if attr.value else attr.value

    c = C()

    assert c.x is None

    c.x = 10
    assert c.x == 50

    c.y = 10
    assert c.y == 20


def test_set_value_decorator():
    @container
    class C:
        @Attr.set_value
        def x(self, attr, value):
            attr.value = value * 5

        y = Attr()

        @y.set_value
        def y(self, attr, value):
            attr.value = value * 2

    c = C()

    assert c.x is None
    c.x = 5
    assert c.x == 25

    c.y = 5
    assert c.y == 10


def test_container_decorator():
    @container
    class C:
        x = Attr()
        y = Attr()

    c = C()
    assert isinstance(c.attrs, Attrs)
    assert c.attrs.x
    assert c.attrs.y

    with pytest.raises(AttributeError):
        _ = c.attrs.z  # noqa


def test_inheritance():
    @container
    class C:
        x = Attr()
        y = Attr()

    class D(C):
        z = Attr()

    d = D()
    assert hasattr(d.attrs, 'x')
    assert hasattr(d.attrs, 'y')
    assert hasattr(d.attrs, 'z')
    assert (d.x, d.y, d.z) == (None, None, None)


def test_setting_attr_in_inherited_class_sets_default():
    @container
    class C:
        x = Attr()

    class D(C):
        x = 100

    c = C()
    assert c.attrs.x.default is None
    assert c.x is None

    d = D()
    assert d.attrs.x.default == 100
    assert d.x == 100

    assert c.attrs.x.default is None
    assert c.x is None


def test_customising_inherited_attribute():
    @container
    class C:
        x = Attr()

    class D(C):
        x = copy(C.x)  # Must shallow-copy the attribute from parent class.

        @x.set_value
        def x(self, attr, value):
            attr.value = value * 5

    d = D()
    d.x = 5
    assert d.x == 25

    c = C()
    c.x = 5
    assert c.x == 5


def test_initialiser():
    @container
    class C:
        x = Attr()
        y = Attr()

    c = C(y=2)
    assert c.y == 2
    assert c.x is None


def test_derived_class_initialiser():
    @container
    class C:
        x = Attr()

    class D(C):
        y = Attr()

    class E(D):
        z = Attr()

    c = C(x=1)
    assert c.x == 1

    d = D(x=1, y=2)
    assert (d.x, d.y) == (1, 2)

    e = E(x=1, y=2, z=3)
    assert (e.x, e.y, e.z) == (1, 2, 3)


def test_initialiser_with_init_value():
    @container
    class C:
        x = Attr()

        @x.init_value
        def x(self, attr, value):
            attr.value = value.upper()

        @Attr.init_value
        def y(self, attr, value):
            attr.value = value.lower()

    c = C(x='hello')
    assert c.x == 'HELLO'

    c.x = 'world'
    assert c.x == 'world'

    c.y = 'WORLD'
    assert c.y == 'world'

    c.y = 'hello'
    assert c.y == 'hello'


def test_override_attrs_cls_and_bound_attr_cls():
    class CustomBoundAttr(BoundAttr):
        pass

    class CustomAttrs(Attrs):
        pass

    @container
    class C:
        attrs_cls = CustomAttrs
        bound_attr_cls = CustomBoundAttr

        x = Attr()

    c = C()
    assert isinstance(c.attrs, CustomAttrs)
    assert isinstance(c.attrs.x, CustomBoundAttr)


def test_container_class_attrs_is_attrs_of_container_class():
    @container
    class C:
        pass

    class CustomAttrs(Attrs):
        pass

    @container
    class D:
        attrs_cls = CustomAttrs

    assert isinstance(C.attrs, Attrs)
    assert not isinstance(C.attrs, CustomAttrs)

    assert isinstance(D.attrs, CustomAttrs)


def test_attrs_names():
    @container
    class C:
        x = Attr()

    assert C.attrs._names_ == ['x']
    assert C().attrs._names_ == ['x']


def test_attrs_container_stores_list_of_all_names():
    # In Python 3.5 there we cannot control the __dict__ creation of C class
    # with __prepare__ so we cannot guarantee the order of attrs.
    @container
    class C:
        x = Attr()
        y = Attr()

    c = C()
    names = c.attrs._names_
    assert isinstance(names, list)

    assert set(names) == {'x', 'y'}

    class D(C):
        a = Attr()
        x = 5
        b = Attr()

    d = D(y=3)
    assert set(d.attrs._names_) == {'x', 'y', 'a', 'b'}


def test_attrs_is_an_iterator_over_all_names():
    @container
    class C:
        w = Attr()
        x = Attr()
        y = Attr()

    class D(C):
        z = Attr()

    d = D()
    assert set(d.attrs) == {'w', 'x', 'y', 'z'}
