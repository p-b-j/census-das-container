import os, sys
sys.path.append( os.path.dirname(os.path.dirname(os.path.dirname( os.path.dirname(__file__)))))

import pytest
import warnings
from fractions import Fraction
from programs.engine.curve import zCDPEpsDeltaCurve
import numpy as np

try:
    import programs.engine.budget as bdg
    HAVE_SPARK = True
except ImportError as e:
    HAVE_SPARK = False
    import programs.engine.budget as bdg

def test_assert_sum_to():
    if not HAVE_SPARK:
        warnings.warn("SPARK not available")
        return
    with pytest.raises(AssertionError) as err:
        bdg.assertSumTo((0.1,0.1), msg="Test 1")
    assert "Test 1 values (0.1, 0.1) sum to 0.2 instead of 1.0" in str(err.value)

    bdg.assertSumTo((.3,.2,.5))

def test_getPerAttrEpsilonFromProportionsFunctions():
    attr_query_props = {"hhgq":{
        "hhgq":{"Tract": Fraction(2, 10), "Block_Group": Fraction(2, 10), "Block": Fraction(3, 10)},
        "detailed":{"Tract": Fraction(3, 10), "Block_Group": Fraction(3, 10), "Block": Fraction(1, 10)}},
                        "votingage":{
        "detailed":{"Tract": Fraction(3, 10), "Block_Group": Fraction(3, 10), "Block": Fraction(1, 10)},
        "votingage":{"Tract": Fraction(3, 10), "Block_Group": Fraction(4, 10), "Block": Fraction(1, 10)}}}
    dimnames = ["hhgq", "votingage"]
    geolevel_prop_budgets_dict = {"Tract": Fraction(3, 10), "Block_Group": Fraction(1, 5), "Block": Fraction(1, 2)}
    total_budget = 17
    expected_per_attr_eps = dict((("hhgq", 7.65), ("votingage", 7.14)))
    expected_per_geolevel_attrs = dict((("Tract", 11.9), ("Block_Group", 8.5,)))
    per_attr_epsilons, per_geolevel_epsilons, _ = bdg.Budget.pureDPgetPerAttrEpsilonFromProportions(attr_query_props, dimnames, geolevel_prop_budgets_dict, total_budget)
    for attr_name, attr_eps in expected_per_attr_eps.items():
        assert np.isclose(attr_eps, per_attr_epsilons[attr_name], atol=1e-6)
    for attr_name, geolevel_eps in expected_per_geolevel_attrs.items():
        assert np.isclose(geolevel_eps, per_geolevel_epsilons[attr_name], atol=1e-6)

    delta = 1e-10
    global_scale = .1
    geolevel_prop_budgets = (Fraction(3, 10), Fraction(1, 5), Fraction(1, 2))
    # order is: "total", "hhgq", "votingage", "detailed":
    dp_query_prop = {"Tract": (Fraction(2, 10), Fraction(2, 10), Fraction(3, 10), Fraction(3, 10)),
                      "Block_Group": (Fraction(1, 10), Fraction(2, 10), Fraction(4, 10), Fraction(3, 10)),
                      "Block": (Fraction(5, 10), Fraction(3, 10), Fraction(1, 10), Fraction(1, 10))}

    def getAttrBudgetFromCurve(gaussian_mechanism_curve):
        return Fraction(gaussian_mechanism_curve.get_epsilon(float(delta), global_scale, bounded=True, tol=1e-7, zcdp=True))
    per_attr_epsilons, per_geolevel_epsilons, _ = bdg.Budget.zCDPgetPerAttrEpsilonFromProportions(attr_query_props, getAttrBudgetFromCurve,
                                                                                                    geolevel_prop_budgets_dict, dimnames,
                                                                                                    geolevel_prop_budgets, dp_query_prop)
    expected_per_attr_eps = dict((("hhgq", 107.74557956), ("votingage", 102.58843891)))
    expected_per_geolevel_attrs = dict((("Tract", 148.49113099), ("Block_Group", 116.18815593,)))
    for attr_name, attr_eps in expected_per_attr_eps.items():
        assert np.isclose(attr_eps, float(per_attr_epsilons[attr_name]), atol=1e-6)
    for attr_name, geolevel_eps in expected_per_geolevel_attrs.items():
        assert np.isclose(geolevel_eps, float(per_geolevel_epsilons[attr_name]), atol=1e-6)

if __name__ == "__main__":
    test_getPerAttrEpsilonFromProportionsFunctions()
