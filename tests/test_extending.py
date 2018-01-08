from wr_attrs import Attr, AttrContainer, _Attrs


def test_can_customise_attrs():
    class MyAttrs(_Attrs):
        pass

    class Base(AttrContainer):
        attrs_cls = MyAttrs

        x = Attr()

    b = Base()
    assert isinstance(b.attrs, MyAttrs)


def test_can_declare_custom_attr_options():
    class MyAttrs(_Attrs):

        @property
        def safe_names(self):
            return [name for name in self.names if self[name].options.get('safe')]

    class Base(AttrContainer):
        attrs_cls = MyAttrs

        x = Attr(safe=True)
        y = Attr(safe=False)
        z = Attr()

    b = Base()
    assert list(b.attrs.names) == ['x', 'y', 'z']
    assert b.attrs.safe_names == ['x']


def test_setter_is_used_to_initialise_attr():
    class A(AttrContainer):
        x = Attr()
        y = Attr()

        @y.setter
        def y(self, value):
            self.attrs.set('y', value * 5)

    a = A(x=3, y=3)
    assert a.x == 3
    assert a.y == 15

    a.attrs.update(x=2, y=2)
    assert a.x == 2
    assert a.y == 10


def test_getter():
    class A(AttrContainer):
        x = Attr()

        @x.getter
        def x(self):
            # TODO allow requesting attr (BoundAttr) in signature
            # TODO so that you can then return attr.value * 5 if attr.value else None
            value = self.attrs.get('x')
            if value is None:
                return None
            else:
                return value * 5

    a = A()
    assert a.x is None

    a.x = 5
    assert a.x == 25
    assert a.x == 25
