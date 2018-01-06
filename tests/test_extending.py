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
