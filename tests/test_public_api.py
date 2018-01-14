from wr_attrs import Attr, container


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
