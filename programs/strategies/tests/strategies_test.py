from programs.strategies.strategies import QueryOrderingSelector
from constants import CC

levels = CC.GEOLEVEL_BLOCK, CC.GEOLEVEL_BLOCK_GROUP, CC.GEOLEVEL_TRACT, CC.GEOLEVEL_COUNTY, CC.GEOLEVEL_STATE, CC.GEOLEVEL_US


def test_ordering_types():
    for ordering_name, ordering_maker in QueryOrderingSelector.query_orderings.items():
        ordering = ordering_maker.make(levels)
        first_ordering = ordering[levels[0]][CC.L2_QUERY_ORDERING]
        first_element = first_ordering[list(first_ordering.keys())[0]]
        if isinstance(first_element, dict):
            outer_pass = True
        elif isinstance(first_element, (tuple, list)):
            outer_pass = False
        else:
            raise ValueError(f"Ordering {ordering_name} has wrong syntax")
        for gl, gl_ord in ordering.items():
            for k1, v1 in gl_ord[CC.L2_QUERY_ORDERING].items():
                if outer_pass:
                    assert isinstance(v1, dict), f"Ordering {ordering_name}, outer pass {k1} had {v1} instead of a dict inside L2 Query ordering for geolevel {gl}: {gl_ord}"
                    for k2, v2 in v1.items():
                        assert isinstance(v2, (tuple, list)), f"Ordering {ordering_name}, outer pass {k1}, inner pass {k2} had {v2} instead of list/tuple inside L2 Query ordering for geolevel {gl}: {gl_ord}"
                else:
                    assert isinstance(v1, (tuple, list)), f"Ordering {ordering_name}, pass {k1} had {v1} instead of list/tuple inside L2 Query ordering for geolevel {gl}: {gl_ord}"

            for k1, v1 in gl_ord[CC.ROUNDER_QUERY_ORDERING].items():
                if outer_pass:
                    assert isinstance(v1, dict), f"Ordering {ordering_name}, outer pass {k1} had {v1} instead of a dict inside Rounder Query ordering for geolevel {gl}: {gl_ord}"
                    for k2, v2 in v1.items():
                        assert isinstance(v2, (tuple, list)), f"Ordering {ordering_name}, outer pass {k1}, inner pass {k2} had {v2} instead of list/tuple inside Rounder Query ordering for geolevel {gl}: {gl_ord}"
                else:
                    assert isinstance(v1, (tuple, list)), f"Ordering {ordering_name}, pass {k1} had {v1} instead of list/tuple inside Rounder Query ordering for geolevel {gl}: {gl_ord}"

            if gl_ord[CC.L2_CONSTRAIN_TO_QUERY_ORDERING] is None:
                continue

            for k1, v1 in gl_ord[CC.L2_CONSTRAIN_TO_QUERY_ORDERING].items():
                if outer_pass:
                    assert isinstance(v1, dict), f"Ordering {ordering_name}, outer pass {k1} had {v1} instead of a dict inside Constrain-to L2 Query ordering for geolevel {gl}: {gl_ord}"
                    for k2, v2 in v1.items():
                        assert isinstance(v2, (tuple, list)), f"Ordering {ordering_name}, outer pass {k1}, inner pass {k2} had {v2} instead of list/tuple inside Constrain-to L2 Query ordering for geolevel {gl}: {gl_ord}"
                else:
                    assert isinstance(v1, (tuple, list)), f"Ordering {ordering_name}, pass {k1} had {v1} instead of list/tuple inside Constrain-to L2 Query ordering for geolevel {gl}: {gl_ord}"
