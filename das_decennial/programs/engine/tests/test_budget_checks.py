import pytest
from das_utils import checkDyadic
from exceptions import DASValueError


class TestBudgetChecks:

    @pytest.mark.parametrize("values", [
        (.25, .5),
        (".25", ".375"),
        (13 / 1024, 3 / 512),
        ("13/1024", "3/512")
    ] )
    def test_dyadic(self, values):
        checkDyadic(values)

    @pytest.mark.parametrize("values", [
        (.1, .2),
        (.1, .4),
        (".258", ".375"),
        (13 / 1024, 3 / 2048)
    ])
    def test_error_dyadic(self, values):
        with pytest.raises(DASValueError, match="Non-dyadic-rational factor"):
            checkDyadic(values)
