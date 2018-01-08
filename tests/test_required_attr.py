import pytest

from wr_attrs import AttrContainer, Attr, Required


def test_required_is_set():
    class C(AttrContainer):
        x = Attr(required=False)
        y = Attr(required=True)
        z = Attr()

    c = C()
    assert c.attrs.x.required is False
    assert c.attrs.y.required is True
    assert c.attrs.z.required is False


def test_cannot_set_required_with_default_value():
    with pytest.raises(ValueError) as exc_info:
        class C(AttrContainer):
            x = Attr(required=True, default=5)

    assert 'default= must not be set together with required=True' in str(exc_info.value)


def test_default_for_required_attr_is_NotSet():
    class C(AttrContainer):
        x = Attr(required=True)

    c = C()
    assert c.attrs.x.default is Required


def test_required_value_via_attribute_access_raises_value_error():
    class C(AttrContainer):
        x = Attr(required=True)

    c = C()
    with pytest.raises(ValueError) as exc_info:
        _ = c.x
    assert "'x' is missing value" in str(exc_info.value)

    c.x = 5
    assert c.x == 5


def test_required_value_can_be_accessed_via_attrs():
    class C(AttrContainer):
        x = Attr(required=True)

    c = C()
    assert c.attrs.x.value is Required
