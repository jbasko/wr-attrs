import pytest

from wr_attrs import Attr, AttrContainer


class A(AttrContainer):
    p = Attr()


class B(A):
    q = Attr()
    r = Attr()


def test_attributes_are_descriptors_for_classes_and_values_for_instances():
    a = A()

    assert isinstance(A.p, Attr)
    assert A.p.name == 'p'
    assert A.p.default is None

    assert a.p is None


def test_attributes_can_be_safely_initialised():
    a = A(p=23)

    assert isinstance(A.p, Attr)
    assert A.p.default is None

    assert a.p == 23


def test_attributes_are_inherited():
    b = B(p=23, q=42)

    assert B.p is A.p

    assert b.p == 23
    assert b.q == 42
    assert b.r is None


def test_attrs_collection():
    b = B(q=42)

    assert len(b.attrs) == 3
    assert list(b.attrs.names) == ['p', 'q', 'r']
    assert list(b.attrs.values) == [('p', None), ('q', 42), ('r', None)]

    assert b.attrs.q is B.q
    assert b.attrs['q'] is B.q
    assert b.attrs.get('q') == 42


def test_default_value_set_in_inherited_class():
    class C(B):
        p = 0
        q = 1

    c = C()

    assert c.p == 0
    assert c.q == 1
    assert c.r is None

    assert C.p is not B.p
    assert C.p.default == 0
    assert B.p.default is None

    assert C.q is not B.q
    assert C.q.default == 1
    assert B.q.default is None

    assert C.r is B.r


def test_custom_setter():
    class D(B):
        s = Attr()

        @s.setter
        def s(self, value):
            self.attrs.set('s', value * 5)

    assert isinstance(D.s, Attr)

    d = D(s=0)
    d.s = 5
    assert d.s == 25


def test_custom_getter():
    class D(B):
        s = Attr()

        @s.getter
        def s(self):
            return self.attrs.get('s') * 10

    d = D(s=5)
    assert d.s == 50

    d.s = 10
    assert d.s == 100


def test_cannot_delete_attr():
    b = B(q=1)
    with pytest.raises(AttributeError) as exc_info:
        delattr(b, 'q')

    assert str(exc_info.value) == '__delete__'


def test_can_inspect_attrs_on_container_class():
    class D(B):
        s = Attr()

    assert D.attrs.owner is D
    assert D.attrs.get('p') is D.p
    assert list(D.attrs.names) == ['p', 'q', 'r', 's']
    assert len(D.attrs) == 4


def test_cannot_set_unknown_attr():
    class D(B):
        pass

    with pytest.raises(AttributeError) as exc_info:
        D(p=1, q=2, r=3, zzz=5)
    assert str(exc_info.value) == 'zzz'

    d = D(p=1, q=2, r=3)

    with pytest.raises(AttributeError) as exc_info:
        d.attrs.set('yyy', 5)
    assert str(exc_info.value) == 'yyy'

    with pytest.raises(AttributeError) as exc_info:
        d.attrs.update(xxx=5)
    assert str(exc_info.value) == 'xxx'


def test_can_set_other_attributes():
    b = B()
    b.something_else = 5
    assert b.something_else == 5
