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
    class D(C):
        attrs_cls = CustomAttrs

    assert isinstance(C.attrs, Attrs)
    assert not isinstance(C.attrs, CustomAttrs)

    assert isinstance(D.attrs, CustomAttrs)
    assert D.attrs.owner is D


def test_attrs_owner_is_correct():
    @container
    class C:
        pass

    @container
    class C2(C):
        pass

    class D(C):
        pass

    class E(D):
        pass

    assert C.attrs.owner is C
    assert C2.attrs.owner is C2
    assert D.attrs.owner is D
    assert E.attrs.owner is E

    c = C()
    c2 = C2()
    d = D()
    e = E()

    assert C.attrs.owner is C
    assert C2.attrs.owner is C2
    assert D.attrs.owner is D
    assert E.attrs.owner is E

    assert c.attrs.owner is c
    assert c2.attrs.owner is c2
    assert d.attrs.owner is d
    assert e.attrs.owner is e


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


def test_attr_cls_is_a_decorator_for_getter():
    @container
    class C:
        @Attr
        def x(self, attr):
            return attr.value * 2

    c = C(x=5)
    assert c.x == 10

    c.x = 15
    assert c.x == 30


def test_attr_with_options_still_is_a_decorator_for_getter():
    @container
    class C:
        @Attr(default=10)
        def x(self, attr: BoundAttr):
            if attr.has_value_initialised:
                return attr.value * 5
            else:
                return attr.default

    c = C()
    assert c.attrs.x.default == 10
    assert c.x == 10

    c.x = 20
    assert c.x == 100


def test_attrs_all():
    @container
    class C:
        x = Attr()

        @Attr
        def y(self, attr):
            return attr.value

    class D(C):
        @Attr.init_value
        def z(self, attr, value):
            attr.value = value

    assert set(C.attrs._all_) == {C.attrs.x, C.attrs.y}
    assert set(D.attrs._all_) == {D.attrs.x, D.attrs.y, D.attrs.z}


def test_attrs_tagged():
    @container
    class C:
        x = Attr(safe=True, cli=True)
        y = Attr(cli='y')

    assert set(C.attrs._names_) == {'x', 'y'}
    assert C.attrs.owner is C

    assert set(C.attrs._tagged_('safe')) == {C.attrs.x}
    assert set(C.attrs._tagged_('cli')) == {C.attrs.x, C.attrs.y}

    c = C()
    assert c.attrs.owner is c
    assert set(c.attrs._tagged_('safe')) == {c.attrs.x}
    assert set(c.attrs._tagged_('cli')) == {c.attrs.x, c.attrs.y}
    assert set(c.attrs._tagged_('safe', 'cli')) == {c.attrs.x}


def test_cannot_set_container_cls_attrs():
    @container
    class C:
        x = Attr()

    with pytest.raises(TypeError) as exc_info:
        C.attrs.set('x', 'No no no')
    assert 'x on class is read-only' in str(exc_info.value)


def test_sets_attr_attribute_on_container_class_bound_attr():
    @container
    class C:
        x = Attr(safe=True)

    assert C.attrs.x.safe is True
    assert C.attrs.x.options['safe'] is True
    C.attrs.x.safe = False
    assert C.attrs.x.safe is False
    assert C.attrs.x.options['safe'] is False

    assert C.attrs.x.default is None
    C.attrs.x.default = 0
    assert C.attrs.x.default == 0


def test_cannot_set_attr_attribute_on_container_instance_bound_attr():
    # Because for a container class C, BoundAttr x, the underlying Attr is shared between all instances of C.
    @container
    class C:
        x = Attr(safe=True)

    c = C()

    with pytest.raises(TypeError) as exc_info:
        c.attrs.x.safe = False
    assert "Cannot set attribute 'safe' on instance-bound Attr 'x'" in str(exc_info.value)


def test_cannot_set_nonexistent_attr_attribute():
    @container
    class C:
        x = Attr()

    with pytest.raises(AttributeError):
        C.attrs.x.safe = True

    c = C()

    with pytest.raises(AttributeError):
        c.attrs.x.safe = True


def test_cannot_delete_attr_of_container_class_or_instance():
    @container
    class C:
        x = Attr()

    with pytest.raises(AttributeError):
        del C.x

    c = C(x=2)

    with pytest.raises(NotImplementedError):
        del c.x
