from constants import CC
from fractions import Fraction as Fr
from collections import defaultdict


class TestStrategy:
    @staticmethod
    def make(levels):
        test_strategy = defaultdict(lambda: defaultdict(dict))  # So as to avoid having to specify empty dicts and defaultdicts
        test_strategy.update({
            CC.GEODICT_GEOLEVELS: levels,
            CC.DPQUERIES + "default": (
                "total",
                "numraces",
                "numraces * votingage",
                "numraces * votingage * hispanic",
                "numraces * hhgq * hispanic * votingage",
                "detailed"),
            CC.QUERIESPROP + "default": (tuple(Fr(num, 100) for num in (20, 20, 20, 15, 15, 10))),
            # CC.DPQUERIES: {},
            # CC.QUERIESPROP: {},
            # CC.UNITDPQUERIES: {},
            # CC.UNITQUERIESPROP: {},
            # CC.VACANCYDPQUERIES: {},
            # CC.VACANCYQUERIESPROP: {},
        })

        for level in test_strategy[CC.GEODICT_GEOLEVELS]:
            test_strategy[CC.DPQUERIES][level] = test_strategy[CC.DPQUERIES + "default"]
            test_strategy[CC.QUERIESPROP][level] = test_strategy[CC.QUERIESPROP + "default"]
        test_strategy[CC.QUERIESPROP][CC.GEOLEVEL_COUNTY]      = tuple(Fr(num, 100) for num in (10, 30, 20, 15, 15, 10))
        test_strategy[CC.QUERIESPROP][CC.GEOLEVEL_TRACT]       = tuple(Fr(num, 100) for num in ( 5, 35, 20, 15, 15, 10))
        test_strategy[CC.QUERIESPROP][CC.GEOLEVEL_BLOCK_GROUP] = tuple(Fr(num, 100) for num in ( 1, 39, 20, 15, 15, 10))
        test_strategy[CC.QUERIESPROP][CC.GEOLEVEL_BLOCK]       = tuple(Fr(num, 100) for num in (39,  1, 20, 15, 15, 10))
        return test_strategy


class SingleStateTestStrategyRegularOrdering:
    @staticmethod
    def make(levels):
        # levels = (CC.GEOLEVEL_BLOCK, CC.GEOLEVEL_BLOCK_GROUP, CC.GEOLEVEL_TRACT, CC.GEOLEVEL_COUNTY, CC.GEOLEVEL_STATE)
        ordering = {

            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ("total", "numraces",),
                    1: ("numraces",),
                    2: ("numraces * votingage",),
                    3: ("numraces * votingage * hispanic",),
                },
                1: {
                    0: ("numraces * hhgq * hispanic * votingage",),
                    1: ("detailed",)
                }
            },

            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ("total",),
                    1: ("numraces",),
                    2: ("numraces * votingage",),
                    3: ("numraces * votingage * hispanic",),
                },
                1: {
                    0: ("numraces * hhgq * hispanic * votingage",),
                    1: ("detailed",)
                }

            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ("total", "numraces", "numraces * votingage", "numraces * votingage * hispanic",)
                },
                1: {
                    0: ("numraces * hhgq * hispanic * votingage", "detailed",)
                }
            }

        }

        query_ordering = {}
        for geolevel in levels:
            query_ordering[geolevel] = {
                CC.L2_QUERY_ORDERING: ordering[CC.L2_QUERY_ORDERING],
                CC.L2_CONSTRAIN_TO_QUERY_ORDERING: ordering[CC.L2_CONSTRAIN_TO_QUERY_ORDERING],
                CC.ROUNDER_QUERY_ORDERING: ordering[CC.ROUNDER_QUERY_ORDERING]
            }
        query_ordering[CC.GEOLEVEL_COUNTY][CC.L2_QUERY_ORDERING] = {
            0: {
                0: ("total",),
                1: ("numraces",),
                2: ("numraces * votingage",),
                3: ("numraces * votingage * hispanic",),
            },
            1: {
                0: ("numraces * hhgq * hispanic * votingage",),
                1: ("detailed",)
            }
        }
        return query_ordering


class Strategies1:
    @staticmethod
    def getDPQNames():
        return ("total",
                "cenrace",
                "hispanic",
                "votingage",
                "hhinstlevels",
                "hhgq",
                "detailed")


class Strategies2:
    @staticmethod
    def getDPQNames():
        return ("total",
                "hispanic * cenrace11cats",
                "votingage",
                "hhinstlevels",
                "hhgq",
                "hispanic * cenrace11cats * votingage",
                "detailed")


class StandardRedistrictingRounderOrdering:
    @staticmethod
    def get():
        return {
            0: (
                'total',
                'hhgq',
                'hhgq * hispanic',
                'hhgq * hispanic * cenrace',
                'hhgq * votingage * hispanic * cenrace',
                'detailed'
            )
        }


class Strategy1a:
    @staticmethod
    def make(levels):
        strategy1a = defaultdict(lambda: defaultdict(dict))
        strategy1a.update({
            CC.GEODICT_GEOLEVELS: levels,
            CC.DPQUERIES + "default": Strategies1.getDPQNames(),

            CC.QUERIESPROP + "default": tuple([Fr(1, 7)] * 7),
        })
        for level in strategy1a[CC.GEODICT_GEOLEVELS]:
            strategy1a[CC.DPQUERIES][level] = strategy1a[CC.DPQUERIES + "default"]
            strategy1a[CC.QUERIESPROP][level] = strategy1a[CC.QUERIESPROP + "default"]
        return strategy1a


class Strategy1b:
    @staticmethod
    def make(levels):
        strategy1b = defaultdict(lambda: defaultdict(dict))
        strategy1b.update({
            CC.GEODICT_GEOLEVELS: levels,
            CC.DPQUERIES + "default": Strategies1.getDPQNames(),

            CC.QUERIESPROP + "default": tuple(Fr(num, 1024) for num in (1, 2, 1, 1, 1, 1, 5, 5, 1, 17, 989)),
        })
        for level in strategy1b[CC.GEODICT_GEOLEVELS]:
            strategy1b[CC.DPQUERIES][level] = strategy1b[CC.DPQUERIES + "default"]
            strategy1b[CC.QUERIESPROP][level] = strategy1b[CC.QUERIESPROP + "default"]
        return strategy1b


class Strategy2a:
    @staticmethod
    def make(levels):
        strategy2a = defaultdict(lambda: defaultdict(dict))
        strategy2a.update({
            CC.GEODICT_GEOLEVELS: levels,
            CC.DPQUERIES + "default": Strategies2.getDPQNames(),

            CC.QUERIESPROP + "default": tuple([Fr(1, 7)] * 7),
        })
        for level in strategy2a[CC.GEODICT_GEOLEVELS]:
            strategy2a[CC.DPQUERIES][level] = strategy2a[CC.DPQUERIES + "default"]
            strategy2a[CC.QUERIESPROP][level] = strategy2a[CC.QUERIESPROP + "default"]
        return strategy2a


class Strategy1a_St_Cty_isoTot:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = tuple([Fr(1, 10)] * 10)
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(507,512),Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                            Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,11),Fr(1,11),Fr(1,11),Fr(1,11),Fr(1,11),
                                                            Fr(1,11),Fr(1,11),Fr(1,11),Fr(1,11),Fr(1,11),Fr(1,11))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = tuple([Fr(1, 11)] * 11)
        return geos_qs_props_dict


class Strategy1a_St_Cty_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic'),
                    1: ('hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic'),
                    2: ('votingage * hispanic * cenrace',),
                    3: ('detailed',),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels'),
                    1: ('hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic'),
                    2: ('votingage * hispanic * cenrace',),
                    3: ('detailed',),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic'),
                    2: ('hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic'),
                    3: ('votingage * hispanic * cenrace',),
                    4: ('detailed',),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels'),
                    2: ('hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic'),
                    3: ('votingage * hispanic * cenrace',),
                    4: ('detailed',),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        subCounty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic'),
                    1: ('hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic'),
                    2: ('votingage * hispanic * cenrace',),
                    3: ('detailed',),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels'),
                    1: ('hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic'),
                    2: ('votingage * hispanic * cenrace',),
                    3: ('detailed',),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County"):
                query_ordering[geolevel] = st_cty_ordering
            else:
                query_ordering[geolevel] = subCounty_ordering
        return query_ordering


class Strategy1b_St_Cty_isoTot:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,512), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(17,1024), Fr(990,1024))
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(339,512),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                            Fr(1,1024),Fr(1,1024),Fr(1,512),Fr(1,512),
                                                            Fr(1,1024),Fr(3,512),Fr(165,512))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024), Fr(1,512), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(17,1024), Fr(989,1024))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024), Fr(1,512), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(17,1024), Fr(989,1024))
        return geos_qs_props_dict


class Strategy1b_St_Cty_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hispanic * cenrace', 'votingage * cenrace',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hispanic * cenrace', 'votingage * cenrace',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace',
                        'detailed'),
                },
            },

            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        subCounty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County"):
                query_ordering[geolevel] = st_cty_ordering
            else:
                query_ordering[geolevel] = subCounty_ordering
        return query_ordering


class Strategy1b_St_Cty_BG_optSpine_ppmfCandidate:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,512), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(17,1024), Fr(990,1024))
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(678,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                            Fr(1,1024),Fr(1,1024),Fr(2,1024),Fr(2,1024),
                                                            Fr(1,1024),Fr(6,1024),Fr(330,1024))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(342,1024), Fr(1,1024), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(3,1024), Fr(3,1024), Fr(1,1024), Fr(11,1024), Fr(659,1024))
            elif level == "Block_Group":
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(572,1024), Fr(1,1024), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(3,1024), Fr(3,1024), Fr(1,1024), Fr(8,1024), Fr(432,1024))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024), Fr(1,512), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(17,1024), Fr(989,1024))
        return geos_qs_props_dict


class Strategy1b_St_Cty_B_optSpine_ppmfCandidate:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,512), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(17,1024), Fr(990,1024))
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(678,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                            Fr(1,1024),Fr(1,1024),Fr(2,1024),Fr(2,1024),
                                                            Fr(1,1024),Fr(6,1024),Fr(330,1024))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(342,1024), Fr(1,1024), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(3,1024), Fr(3,1024), Fr(1,1024), Fr(11,1024), Fr(659,1024))
            elif level == "Block":
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(160,1024), Fr(2,1024), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(15,1024), Fr(832,1024))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "cenrace", "hispanic", "votingage", "hhinstlevels",
                                                            "hhgq", "hispanic * cenrace", "votingage * cenrace",
                                                            "votingage * hispanic", "votingage * hispanic * cenrace", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024), Fr(1,512), Fr(1,1024), Fr(1,1024), Fr(1,1024),
                                                        Fr(1,1024), Fr(5,1024), Fr(5,1024), Fr(1,1024), Fr(17,1024), Fr(989,1024))
        return geos_qs_props_dict


class Strategy1b_ST_CTY_B_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hispanic * cenrace', 'votingage * cenrace',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hispanic * cenrace', 'votingage * cenrace',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_b_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace',
                        'detailed'),
                },
            },

            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        default_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County", "Block"):
                query_ordering[geolevel] = st_cty_b_ordering
            else:
                query_ordering[geolevel] = default_ordering
        return query_ordering


class Strategy1b_ST_CTY_BG_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hispanic * cenrace', 'votingage * cenrace',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hispanic * cenrace', 'votingage * cenrace',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_bg_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace',
                        'detailed'),
                },
            },

            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        default_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels', 'hhgq', 'votingage * hispanic',
                        'hhgq', 'hispanic * cenrace', 'votingage * cenrace', 'votingage * hispanic',
                        'votingage * hispanic * cenrace', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County", "Block_Group"):
                query_ordering[geolevel] = st_cty_bg_ordering
            else:
                query_ordering[geolevel] = default_ordering
        return query_ordering



class Strategy2a_St_Cty_isoTot:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("hispanic * cenrace11cats", "votingage", "hhinstlevels", "hhgq",
                                                        "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = tuple([Fr(1, 6)] * 6)
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(509,512),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1,1024))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,7),Fr(1,7),Fr(1,7),Fr(1,7),
                                                        Fr(1,7),Fr(1,7),Fr(1,7))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,7),Fr(1,7),Fr(1,7),Fr(1,7),
                                                        Fr(1,7),Fr(1,7),Fr(1,7))
        return geos_qs_props_dict


class Strategy2a_St_Cty_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq'),
                    1: ('hhgq',),
                    2: ('hispanic * cenrace11cats * votingage',),
                    3: ('detailed',),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels'),
                    1: ('hhgq',),
                    2: ('hispanic * cenrace11cats * votingage',),
                    3: ('detailed',),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq'),
                    2: ('hhgq',),
                    3: ('hispanic * cenrace11cats * votingage',),
                    4: ('detailed',),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels'),
                    2: ('hhgq',),
                    3: ('hispanic * cenrace11cats * votingage',),
                    4: ('detailed',),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        subCounty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq'),
                    1: ('hhgq',),
                    2: ('hispanic * cenrace11cats * votingage',),
                    3: ('detailed',),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels'),
                    1: ('hhgq',),
                    2: ('hispanic * cenrace11cats * votingage',),
                    3: ('detailed',),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County"):
                query_ordering[geolevel] = st_cty_ordering
            else:
                query_ordering[geolevel] = subCounty_ordering
        return query_ordering


class Strategy2b_St_Cty_isoTot:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("hispanic * cenrace11cats", "votingage", "hhinstlevels", "hhgq",
                                                    "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1019,1024))
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(905,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(57,512))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1018,1024))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1018,1024))
        return geos_qs_props_dict

class Strategy2b_St_Cty_B_optSpine_ppmfCandidate:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("hispanic * cenrace11cats", "votingage", "hhinstlevels", "hhgq",
                                                    "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1019,1024))
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(815,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(204,1024))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(342,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(677,1024))
            elif level == "Block":
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(190,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(829,1024))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1018,1024))
        return geos_qs_props_dict


class Strategy2b_St_Cty_B_aianSpine_ppmfCandidate:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("hispanic * cenrace11cats", "votingage", "hhinstlevels", "hhgq",
                                                    "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1019,1024))
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(815,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(204,1024))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(342,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(677,1024))
            elif level == "Block":
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(208,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(811,1024))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1018,1024))
        return geos_qs_props_dict


class Strategy2b_St_Cty_BG_optSpine_ppmfCandidate:
    @staticmethod
    def make(levels):
        geos_qs_props_dict = defaultdict(lambda: defaultdict(dict))
        geos_qs_props_dict.update({
            CC.GEODICT_GEOLEVELS: levels,
        })
        for level in geos_qs_props_dict[CC.GEODICT_GEOLEVELS]:
            if level == "US": # No 'total' query
                geos_qs_props_dict[CC.DPQUERIES][level] = ("hispanic * cenrace11cats", "votingage", "hhinstlevels", "hhgq",
                                                    "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1019,1024))
            elif level == "State": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(815,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(204,1024))
            elif level == "County": # In Redistricting, separately tuned rho on 'total'
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(342,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(677,1024))
            elif level == "Block_Group":
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(530,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(489,1024))
            else: # Only per-geolevel rho actively tuned in other geolevels; query allocations left at default
                geos_qs_props_dict[CC.DPQUERIES][level] = ("total", "hispanic * cenrace11cats", "votingage", "hhinstlevels",
                                                        "hhgq", "hispanic * cenrace11cats * votingage", "detailed")
                geos_qs_props_dict[CC.QUERIESPROP][level] = (Fr(1,1024),Fr(1,1024),Fr(1,1024),Fr(1,1024),
                                                        Fr(1,1024),Fr(1,1024),Fr(1018,1024))
        return geos_qs_props_dict



class Strategy2b_ST_CTY_B_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                            'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING:{
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                            'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_b_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        default_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County", "Block"):
                query_ordering[geolevel] = st_cty_b_ordering
            else:
                query_ordering[geolevel] = default_ordering
        return query_ordering


class Strategy2b_ST_CTY_BG_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                            'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING:{
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                            'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_bg_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        default_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County", "Block_Group"):
                query_ordering[geolevel] = st_cty_bg_ordering
            else:
                query_ordering[geolevel] = default_ordering
        return query_ordering


class Strategy2b_St_Cty_isoTot_Ordering:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        us_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                            'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING:{
                0: {
                    0: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                            'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        st_cty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total',),
                    1: ('hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }
        subCounty_ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq',
                        'hispanic * cenrace11cats * votingage', 'detailed'),
                },
            },
            CC.ROUNDER_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hhgq', 'hhgq * hispanic', 'hhgq * hispanic * cenrace', 'hhgq * votingage * hispanic * cenrace',
                        'detailed'),
                },
            },
        }

        query_ordering = {}
        for geolevel in levels:
            if geolevel == "US":
                query_ordering[geolevel] = us_ordering
            elif geolevel in ("State", "County"):
                query_ordering[geolevel] = st_cty_ordering
            else:
                query_ordering[geolevel] = subCounty_ordering
        return query_ordering


class Strategy2b:
    @staticmethod
    def make(levels):
        strategy2b = defaultdict(lambda: defaultdict(dict))
        strategy2b.update({
            CC.GEODICT_GEOLEVELS: levels,
            CC.DPQUERIES + "default": Strategies2.getDPQNames(),

            CC.QUERIESPROP + "default": tuple(Fr(num, 1024) for num in (1,) * 6 + (1018,)),
        })

        for level in strategy2b[CC.GEODICT_GEOLEVELS]:
            strategy2b[CC.DPQUERIES][level] = strategy2b[CC.DPQUERIES + "default"]
            strategy2b[CC.QUERIESPROP][level] = strategy2b[CC.QUERIESPROP + "default"]

        return strategy2b


class RedistrictingStrategiesRegularOrdering1a:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        ordering = {
            CC.L2_QUERY_ORDERING: {
                0: ('total',
                        'cenrace',
                        'hispanic',
                        'votingage',
                        'hhinstlevels',
                        'hhgq'),
                1: ("detailed",),
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: ('total', 'cenrace', 'hispanic', 'votingage', 'hhinstlevels'),
                1: ("detailed",),
            },
            CC.ROUNDER_QUERY_ORDERING: StandardRedistrictingRounderOrdering.get()
        }

        query_ordering = {}
        for geolevel in levels:
            query_ordering[geolevel] = {
                CC.L2_QUERY_ORDERING: ordering[CC.L2_QUERY_ORDERING],
                CC.L2_CONSTRAIN_TO_QUERY_ORDERING: ordering[CC.L2_CONSTRAIN_TO_QUERY_ORDERING],
                CC.ROUNDER_QUERY_ORDERING: ordering[CC.ROUNDER_QUERY_ORDERING]
            }
        return query_ordering


class RedistrictingStrategiesRegularOrdering1b:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: Strategies1.getDPQNames()
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: None,
            CC.ROUNDER_QUERY_ORDERING: StandardRedistrictingRounderOrdering.get()
        }

        query_ordering = {}
        for geolevel in levels:
            query_ordering[geolevel] = {
                CC.L2_QUERY_ORDERING: ordering[CC.L2_QUERY_ORDERING],
                CC.L2_CONSTRAIN_TO_QUERY_ORDERING: ordering[CC.L2_CONSTRAIN_TO_QUERY_ORDERING],
                CC.ROUNDER_QUERY_ORDERING: ordering[CC.ROUNDER_QUERY_ORDERING]
            }
        return query_ordering


class RedistrictingStrategiesRegularOrdering2a:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: Strategies2.getDPQNames()
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: None,
            CC.ROUNDER_QUERY_ORDERING: StandardRedistrictingRounderOrdering.get()
        }

        query_ordering = {}
        for geolevel in levels:
            query_ordering[geolevel] = {
                CC.L2_QUERY_ORDERING: ordering[CC.L2_QUERY_ORDERING],
                CC.L2_CONSTRAIN_TO_QUERY_ORDERING: ordering[CC.L2_CONSTRAIN_TO_QUERY_ORDERING],
                CC.ROUNDER_QUERY_ORDERING: ordering[CC.ROUNDER_QUERY_ORDERING]
            }
        return query_ordering


class RedistrictingStrategiesRegularOrdering2b:
    @staticmethod
    def make(levels):
        # levels = USGeolevelsNoTractGroup.getLevels()
        ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels', 'hhgq'),
                    1: ('hhgq', ),
                    2: ("hispanic * cenrace11cats * votingage",),
                    3: ("detailed",),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: {
                0: {
                    0: ('total', 'hispanic * cenrace11cats', 'votingage', 'hhinstlevels'),
                    1: ('hhgq',),
                    2: ("hispanic * cenrace11cats * votingage",),
                    3: ("detailed",),
                },

            },
            CC.ROUNDER_QUERY_ORDERING: StandardRedistrictingRounderOrdering.get()
        }

        query_ordering = {}
        for geolevel in levels:
            query_ordering[geolevel] = {
                CC.L2_QUERY_ORDERING: ordering[CC.L2_QUERY_ORDERING],
                CC.L2_CONSTRAIN_TO_QUERY_ORDERING: ordering[CC.L2_CONSTRAIN_TO_QUERY_ORDERING],
                CC.ROUNDER_QUERY_ORDERING: ordering[CC.ROUNDER_QUERY_ORDERING]
            }
        return query_ordering


class DetailedOnly:
    @staticmethod
    def make(levels):
        test_strategy = defaultdict(lambda: defaultdict(dict))  # So as to avoid having to specify empty dicts and defaultdicts
        test_strategy.update({
            CC.GEODICT_GEOLEVELS: levels,
            CC.DPQUERIES + "default": (
                "detailed",),

            CC.QUERIESPROP + "default": (1,),
        })

        for level in test_strategy[CC.GEODICT_GEOLEVELS]:
            test_strategy[CC.DPQUERIES][level] = test_strategy[CC.DPQUERIES + "default"]
            test_strategy[CC.QUERIESPROP][level] = test_strategy[CC.QUERIESPROP + "default"]

        return test_strategy


class DetailedOnlyQueryOrderingOuterPass:
    @staticmethod
    def make(levels):
        ordering = {
            CC.L2_QUERY_ORDERING: {
                0: {
                    0: ("detailed",),
                },
            },
            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: None,
            CC.ROUNDER_QUERY_ORDERING:  {
                0: {
                    0: ("detailed",),
                },
            }
        }

        query_ordering = {}
        for geolevel in levels:
            query_ordering[geolevel] = {
                CC.L2_QUERY_ORDERING: ordering[CC.L2_QUERY_ORDERING],
                CC.L2_CONSTRAIN_TO_QUERY_ORDERING: ordering[CC.L2_CONSTRAIN_TO_QUERY_ORDERING],
                CC.ROUNDER_QUERY_ORDERING: ordering[CC.ROUNDER_QUERY_ORDERING]
            }

        return query_ordering


class DetailedOnlyQueryOrdering:
    @staticmethod
    def make(levels):
        ordering = {
            CC.L2_QUERY_ORDERING: {0: ("detailed",)},

            CC.L2_CONSTRAIN_TO_QUERY_ORDERING: None,
            CC.ROUNDER_QUERY_ORDERING:  {0: ("detailed",)},
        }

        query_ordering = {}
        for geolevel in levels:
            query_ordering[geolevel] = {
                CC.L2_QUERY_ORDERING: ordering[CC.L2_QUERY_ORDERING],
                CC.L2_CONSTRAIN_TO_QUERY_ORDERING: ordering[CC.L2_CONSTRAIN_TO_QUERY_ORDERING],
                CC.ROUNDER_QUERY_ORDERING: ordering[CC.ROUNDER_QUERY_ORDERING]
            }

        return query_ordering

class StrategySelector:
    strategies = {
        'strategy1a': Strategy1a,
        'strategy1b': Strategy1b,
        'strategy2a': Strategy2a,
        'strategy2b': Strategy2b,
        'test_strategy': TestStrategy,
        'DetailedOnly': DetailedOnly,
        'Strategy1a_St_Cty_isoTot'                      : Strategy1a_St_Cty_isoTot,
        'Strategy1b_St_Cty_isoTot'                      : Strategy1b_St_Cty_isoTot,
        'Strategy2a_St_Cty_isoTot'                      : Strategy2a_St_Cty_isoTot,
        'Strategy2b_St_Cty_isoTot'                      : Strategy2b_St_Cty_isoTot,
        'Strategy1b_St_Cty_BG_optSpine_ppmfCandidate'   : Strategy1b_St_Cty_BG_optSpine_ppmfCandidate,
        'Strategy1b_St_Cty_B_optSpine_ppmfCandidate'    : Strategy1b_St_Cty_B_optSpine_ppmfCandidate,
        'Strategy2b_St_Cty_B_optSpine_ppmfCandidate'    : Strategy2b_St_Cty_B_optSpine_ppmfCandidate,
        'Strategy2b_St_Cty_B_aianSpine_ppmfCandidate'   : Strategy2b_St_Cty_B_aianSpine_ppmfCandidate,
        'Strategy2b_St_Cty_BG_optSpine_ppmfCandidate'   : Strategy2b_St_Cty_BG_optSpine_ppmfCandidate,
    }

class QueryOrderingSelector:
    query_orderings = {
        'test_strategy_regular_ordering': SingleStateTestStrategyRegularOrdering,
        'DetailedOnly_Ordering': DetailedOnlyQueryOrdering,
        'DetailedOnly_OrderingOuterPass': DetailedOnlyQueryOrderingOuterPass,
        'redistricting_regular_ordering_1a'     : RedistrictingStrategiesRegularOrdering1a,
        'redistricting_regular_ordering_1b'     : RedistrictingStrategiesRegularOrdering1b,
        'redistricting_regular_ordering_2a'     : RedistrictingStrategiesRegularOrdering2a,
        'redistricting_regular_ordering_2b'     : RedistrictingStrategiesRegularOrdering1b,
        'Strategy1a_St_Cty_isoTot_Ordering'     : Strategy1a_St_Cty_isoTot_Ordering,
        'Strategy1b_St_Cty_isoTot_Ordering'     : Strategy1b_St_Cty_isoTot_Ordering,
        'Strategy2a_St_Cty_isoTot_Ordering'     : Strategy2a_St_Cty_isoTot_Ordering,
        'Strategy2b_St_Cty_isoTot_Ordering'     : Strategy2b_St_Cty_isoTot_Ordering,
        'Strategy1b_ST_CTY_B_isoTot_Ordering'   : Strategy1b_ST_CTY_B_isoTot_Ordering,
        'Strategy1b_ST_CTY_BG_isoTot_Ordering'  : Strategy1b_ST_CTY_BG_isoTot_Ordering,
        'Strategy2b_ST_CTY_B_isoTot_Ordering'   : Strategy2b_ST_CTY_B_isoTot_Ordering,
        'Strategy2b_ST_CTY_BG_isoTot_Ordering'  : Strategy2b_ST_CTY_BG_isoTot_Ordering,
    }
