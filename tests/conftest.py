import pytest

from wr_attrs import Attr, container


@pytest.fixture
def xy_container_cls():
    @container
    class C:
        x = Attr()
        y = Attr()

    return C
