import numpy as np
from fractions import Fraction

def compute_new_props(orig_global_scale, orig_query_props, orig_geo_props, iteration=0, new_state_total_prec=None, denom_limit=1024):
    # This function assumes that original query proportion for total is orig_query_props[0]
    # and that original geolevel proportion for state is: ogirg_geo_props[1]
    orig_prec = 1 / orig_global_scale ** 2
    orig_state_total_prec = orig_geo_props[1] * orig_query_props[0] * orig_prec

    # Assume we double precision of the total query at the state geolevel until we meet the error target:
    new_state_total_prec = orig_state_total_prec * (2 ** iteration) if new_state_total_prec is None else new_state_total_prec

    orig_state_geo_prec = orig_geo_props[1] * orig_prec
    new_state_geo_prec = orig_state_geo_prec - orig_state_total_prec + new_state_total_prec
    new_prec = orig_prec - orig_state_total_prec + new_state_total_prec

    # If geolevel is not state, set new_geo_props so that:
    # new_geo_prop * new_prec == orig_geo_prop * orig_prec,
    # and, if geolvel is a state, so that:
    # new_geo_prop * new_prec == new_state_geo_prec.
    new_geo_props = [g_prop * orig_prec / new_prec if k != 1 else new_state_geo_prec / new_prec for k, g_prop in enumerate(orig_geo_props)]
    assert orig_state_total_prec <= new_state_total_prec
    assert np.abs(sum(new_geo_props) - 1) < 1e-5, f"{sum(new_geo_props)} \n {new_geo_props}"

    # If query is not total, set new_state_query_props so that:
    # new_state_query_prop * new_state_geo_prec == orig_query_prop * orig_prec * orig_geo_props[1],
    # and, if query is total, so that:
    # new_state_query_prop * new_state_geo_prec == new_state_total_prec.
    new_state_query_props = [q_prop * orig_prec * orig_geo_props[1] / new_state_geo_prec if k != 0 else new_state_total_prec / new_state_geo_prec for k, q_prop in enumerate(orig_query_props)]
    assert np.abs(sum(new_state_query_props) - 1) < 1e-5, f"{sum(new_state_query_props)} \n {new_state_query_props}"

    new_global_scale = Fraction(np.sqrt(1/new_prec)).limit_denominator(denom_limit)

    # round results:
    new_state_query_props = [Fraction(x).limit_denominator(denom_limit) for x in new_state_query_props]
    new_geo_props = [Fraction(x).limit_denominator(denom_limit) for x in new_geo_props]
    new_state_total_prec = float(new_geo_props[1] * new_state_query_props[0] / new_global_scale**2)

    print(f"set new value of global scale to: {new_global_scale}")
    print(f"set new geolevel proportions to: {new_geo_props}")
    print(f"For state geolevel only, set new query proportions to {new_state_query_props}")
    return new_global_scale, new_state_query_props, new_geo_props, new_state_total_prec


if __name__ == "__main__":
    orig_global_scale = .1
    orig_query_props = (1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11, 1/11)
    orig_geo_props = (1/6,1/6,1/6,1/6,1/6,1/6)

    compute_new_props(orig_global_scale, orig_query_props, orig_geo_props, iteration=1)
