"""
This class implements obtaining (via config parsing or otherwise) the values for Privacy Loss Budget (PLB)
allocations over queries and geolevels and storing them, along with relevant parameters, such as privacy framework (pure DP, zCPD),
global noise scale, delta etc.
"""

from fractions import Fraction
from typing import Tuple, List, Dict, Iterable, Callable, Generator, Any, Union
from configparser import NoOptionError, NoSectionError
from collections import defaultdict
import numpy as np

from programs.engine.curve import zCDPEpsDeltaCurve
from programs.engine.discrete_gaussian_utility import limit_denominator as dg_limit_denominator
from programs.das_setup import DASDecennialSetup
import programs.queries.querybase as querybase
from programs.schema.schema import sortMarginalNames
from programs.strategies.strategies import StrategySelector

from das_utils import checkDyadic

from exceptions import DASConfigError, DASConfigValdationError

from das_framework.driver import AbstractDASModule

from constants import CC

DENOM_MAX_POWER = np.ceil(np.log2(CC.PRIMITIVE_FRACTION_DENOM_LIMIT) / 2)


class Budget(AbstractDASModule):

    def __init__(self, levels, setup: DASDecennialSetup, **kwargs):
        super().__init__(name=CC.BUDGET, **kwargs)

        self.levels = levels
        self.levels_reversed = tuple(reversed(self.levels))
        self.privacy_framework = setup.privacy_framework
        self.only_dyadic_rationals = setup.only_dyadic_rationals

        self.global_scale = self.getfraction(CC.GLOBAL_SCALE)   # DP noise scale. just 1/epsilon, for pure DP methods, For eps, delta-DP more complicated

        self.delta: Fraction = self.getfraction(CC.APPROX_DP_DELTA, default=Fraction(1, int(1e10)))  # Delta for (eps, delta)- like mechanisms
        assert 0. < self.delta <= 1., "Approximate DP delta is outside of (0,1]!"

        # Fractions of how the total <engine> privacy budget is split between geolevels (for pure DP; more complicated allocation for zCDP)
        self.geolevel_prop_budgets: tuple = setup.geolevel_prop_budgets                                      # Shares of budget designated to each geolevel
        self.geolevel_prop_budgets_dict: dict = dict(zip(self.levels_reversed, self.geolevel_prop_budgets))
        self.checkAndPrintGeolevelBudgets()

        # Optimized allocations -- sometimes a geounit can get more budget
        # Spark broadcast dict with geocodes as keys and PLB to each geonode as values
        self.plb_allocation = setup.plb_allocation

        self.schema_obj = setup.schema_obj
        self.unit_schema_obj = setup.unit_schema_obj

        self.query_budget = self.QueryBudget(self)

        self.total_budget = self.computeTotal()

        if self.getboolean(CC.PRINT_PER_ATTR_EPSILONS, default=False):
            self.per_attr_epsilons, self.per_geolevel_epsilons = self.computeAndPrintPerAttributeEpsilon()

    def computeTotal(self):
        """
            Computes global epsilon in use, based on global_scale, delta (if applicable), & query, geolevel proportions.
        """
        dp_query_prop = self.query_budget.dp_query_prop
        self.log_and_print(f"Computing total budget using privacy (accounting) framework {self.privacy_framework}")
        if self.privacy_framework in (CC.ZCDP,):
            print(f"Sending geolevel_prop_budgets to Curve: {self.geolevel_prop_budgets}")
            print(f"Sending dp_query_prop to Curve: {dp_query_prop}")
            positive_error_geolevel_props = [prop for prop in self.geolevel_prop_budgets if prop != 0.0]  # TODO: Make less brittle
            gaussian_mechanism_curve = zCDPEpsDeltaCurve(geo_props=positive_error_geolevel_props, query_props_dict=dp_query_prop)
            total_budget = Fraction(gaussian_mechanism_curve.get_epsilon(float(self.delta), self.global_scale, bounded=True,
                                                                         tol=1e-7, zcdp=True))
            total_budget_n, total_budget_d = dg_limit_denominator((total_budget.numerator, total_budget.denominator),
                                                                  max_denominator=CC.PRIMITIVE_FRACTION_DENOM_LIMIT,
                                                                  mode="upper")
            total_budget = Fraction(total_budget_n, total_budget_d)
            for geolevel, prop in self.geolevel_prop_budgets_dict.items():
                geolevel_noise_precision = 2 * prop / (self.global_scale ** 2)
                self.log_and_print(f"Noise 'precision' for {geolevel}: {geolevel_noise_precision}")

            self.log_and_print(f"Delta: {self.delta}")
        elif self.privacy_framework in (CC.PURE_DP,):
            total_budget = 1 / self.global_scale
        else:
            raise NotImplementedError(f"DP primitives/composition rules for {self.privacy_framework} not implemented.")
        self.log_and_print(f"Denominator limit: {CC.PRIMITIVE_FRACTION_DENOM_LIMIT}")
        self.log_and_print(f"Total budget: {total_budget}")
        self.log_and_print(f"Global scale: {self.global_scale}")

        return total_budget

    def checkAndPrintGeolevelBudgets(self):
        """
        For engines infusing noise at each geolevel (e.g. topdown, hdmm*)
        Check that the by-geolevel privacy budget distribution sums to 1, and print allocations
        """

        budget_names = {CC.PURE_DP: "epsilon", CC.ZCDP: "rho"}
        if self.privacy_framework in (CC.PURE_DP, CC.ZCDP):
            budget_msg = f"{self.privacy_framework} {budget_names[self.privacy_framework]} is split between geolevels"
            budget_msg += f" with proportions: {self.geolevel_prop_budgets}"
            self.log_and_print(budget_msg)
        else:
            raise NotImplementedError(f"Formal privacy primitives/composition rules for {self.privacy_framework} not implemented.")

        # check that geolevel_budget_prop adds to 1, if not raise exception
        assertSumTo(self.geolevel_prop_budgets, msg="Across-geolevels Budget Proportion")
        assertEachPositive(self.geolevel_prop_budgets, "across-geolevel")

    def computeAndPrintPerAttributeEpsilon(self):
        """
            Ignoring zero-error geolevels, computes and prints per-histogram-attribute (as well as geography) epsilon
            expended. Uses query kronFactors to determine histogram attributes that are relevant; only implemented for
            SumOverGroupedQuery from querybase. In the case of zCDP, an implied per-attribute epsilon, delta-DP is reported.
        """
        msg = f"Computing per-attribute epsilon for each of "
        msg += f"{self.schema_obj.dimnames}, and for Block-in-Geolevel for each Geolevel in "
        msg += f"{list(self.geolevel_prop_budgets_dict.keys())[:-1]}"
        msg += f"\n(NOTE: geolevels with proportion of budget 0 assigned to them are ignored)"
        self.log_and_print(msg)

        # TODO: add support for Bottomup? No geolevel calculations, then; attr calculations the same
        #       before then, throw an exception if Bottomup used?

        dp_query_prop = self.query_budget.dp_query_prop  # Only iterate over keys below, should be able to use just self.levels? Or the ones filtered to non-zero

        attr_query_props: Dict[str, Dict[str, Dict[str, Fraction]]] = defaultdict(lambda: defaultdict(dict))
        for i, dimname in enumerate(self.schema_obj.dimnames):
            for geolevel in dp_query_prop:
                for query, qprop in self.query_budget.queryPropPairs(geolevel):
                    assert isinstance(query, querybase.SumOverGroupedQuery), f"query {query.name} is of unsupported type {type(query)}"
                    q_kron_facs = query.kronFactors()
                    if q_kron_facs[i].shape[1] >= 2:  # Need at least two kron_factors for a record change in this dim to affect query
                        if (q_kron_facs[i].sum(axis=1) > 0).sum() >= 2:  # At least two kron_facs require at least 1 True for sens>0
                            # TODO: this assumes mutually exclusive kron_fracs; keep SumOverGroupedQuery assert until this is lifted
                            attr_query_props[dimname][query.name][geolevel] = qprop

        for dimname in attr_query_props:
            # This list query proportions by geolevel and then by query. Loops should be switched for doing the other way
            for geolevel in dp_query_prop:
                self.log_and_print(f"Found queries for dim {dimname} in {geolevel}:")
                for qname in attr_query_props[dimname]:
                    self.log_and_print(f"{geolevel}\t{qname} : {attr_query_props[dimname][qname][geolevel]}\n")

        if self.privacy_framework in (CC.ZCDP,):

            def getAttrBudgetFromCurve(gaussian_mechanism_curve):
                return Fraction(gaussian_mechanism_curve.get_epsilon(float(self.delta), self.global_scale, bounded=True, tol=1e-7, zcdp=True))

            per_attr_epsilons, per_geolevel_epsilons, msg = self.zCDPgetPerAttrEpsilonFromProportions(attr_query_props,
                                                        getAttrBudgetFromCurve, self.geolevel_prop_budgets_dict,
                                                        self.schema_obj.dimnames, self.geolevel_prop_budgets, dp_query_prop)
            msg += f" in eps, {self.delta}-DP)\n"
        elif self.privacy_framework in (CC.PURE_DP,):
            per_attr_epsilons, per_geolevel_epsilons, msg = self.pureDPgetPerAttrEpsilonFromProportions(attr_query_props,
                                                        self.schema_obj.dimnames, self.geolevel_prop_budgets_dict, self.total_budget)
        else:
            raise NotImplementedError(f"DP primitives/composition rules for {self.privacy_framework} not implemented.")
        self.log_and_print(msg)
        return per_attr_epsilons, per_geolevel_epsilons

    @staticmethod
    def zCDPgetPerAttrEpsilonFromProportions(attr_query_props, getAttrBudgetFromCurve: Callable, geolevel_prop_budgets_dict, dimnames, geolevel_prop_budgets, dp_query_prop):
        per_attr_epsilons = {}
        per_geolevel_epsilons = {}

        positive_error_geolevel_props = [prop for prop in geolevel_prop_budgets if prop != 0.0]

        msg = ""
        for i, dimname in enumerate(dimnames):

            # attr_query_props is dict with key=queryname, value=dict with key=geolevel, value=proportion
            # convert it to a dict with key=geolevel, value = list of proportions
            query_props_geolevel_dict = defaultdict(list)
            for d in attr_query_props[dimname].values():
                for geolevel, prop in d.items():
                    query_props_geolevel_dict[geolevel].append(prop)

            gaussian_mechanism_curve = zCDPEpsDeltaCurve(geo_props=positive_error_geolevel_props,
                                                         query_props_dict=query_props_geolevel_dict,
                                                         verbose=False)
            attr_budget = getAttrBudgetFromCurve(gaussian_mechanism_curve)
            per_attr_epsilons[dimname] = attr_budget
            msg += f"For single attr/dim {dimname} semantics, zCDP-implied epsilon: {attr_budget} (approx {float(attr_budget)}, "

        bottom_geolevel = list(geolevel_prop_budgets_dict.keys())[-1]  # TODO This is only correct because of the way the dict is built. Make less brittle.
        for i, cur_geolevel in enumerate(geolevel_prop_budgets_dict.keys()):
            if cur_geolevel != bottom_geolevel:
                # The following seems to assume order within a dict? Maybe we should take the list of levels, and iterate over that as keys, and access the dict
                # Although this dict if formed from that list, in that order, so this is fine but not clean
                float_nz_gprops_below_curlevel = [gprop for gprop in list(geolevel_prop_budgets_dict.values())[i + 1:] if gprop != 0.0]
                gaussian_mechanism_curve = zCDPEpsDeltaCurve(geo_props=float_nz_gprops_below_curlevel,
                                                             query_props_dict=dp_query_prop,
                                                             verbose=False)
                attr_budget = getAttrBudgetFromCurve(gaussian_mechanism_curve)

                per_geolevel_epsilons[cur_geolevel] = attr_budget
                msg += f"For geolevel semantics protecting {bottom_geolevel} within {cur_geolevel}, \nzCDP-implied epsilon: "
                msg += f"{attr_budget} (approx {float(attr_budget)}, "

        return per_attr_epsilons, per_geolevel_epsilons, msg

    @staticmethod
    def pureDPgetPerAttrEpsilonFromProportions(attr_query_props, dim_names, geolevel_prop_budgets_dict, total_budget):
        per_attr_epsilons = {}
        per_geolevel_epsilons = {}
        msg = ""

        for i, dimname in enumerate(dim_names):
            attr_budget = 0.
            for qname in attr_query_props[dimname].keys():
                for geolevel, qprop in attr_query_props[dimname][qname].items():
                    attr_budget += qprop * geolevel_prop_budgets_dict[geolevel]
            attr_budget *= float(total_budget)
            per_attr_epsilons[dimname] = attr_budget
            msg += f"For single attr/dim {dimname} semantics, pure-DP epsilon: {attr_budget}\n"
        bottom_geolevel = list(geolevel_prop_budgets_dict.keys())[-1]
        for i, cur_geolevel in enumerate(geolevel_prop_budgets_dict.keys()):
            if cur_geolevel != bottom_geolevel:
                # The following seems to assume order within a dict? Maybe we should take the list of levels, and iterate over that as keys, and access the dict
                # Although this dict if formed from that list, in that order, so this is fine but not clean
                relevant_geoprops = [gprop for gprop in list(geolevel_prop_budgets_dict.values())[i + 1:] if gprop != 0.0]
                attr_budget = float(total_budget) * sum(relevant_geoprops)
                per_geolevel_epsilons[cur_geolevel] = attr_budget
                msg += f"For geolevel semantics protecting {bottom_geolevel} within {cur_geolevel}, pure-DP epsilon: {attr_budget}\n"

        return per_attr_epsilons, per_geolevel_epsilons, msg

    def checkDyadic(self, *args, **kwargs):
        """ Wrapper that adds denom_max_power"""
        if self.only_dyadic_rationals:
            checkDyadic(*args, **kwargs, denom_max_power=DENOM_MAX_POWER)

    class QueryBudget:
        """
        For engines with queries set in config (e.g. topdown, bottomup)
        Read the queries from config, and set their budget allocations. Check that allocation proportions sum to one
        """

        dp_query_prop: Dict[str, Union[Tuple[Fraction], List[Fraction]]]               # Per geolevel, shares of within-geolevel budgets dedicated to each query
        dp_query_names: Dict[str, Union[Tuple[Fraction], List[str]]]                   # Queries by name, per geolevel
        unit_dp_query_names: Dict[str, Union[Tuple[Fraction], List[str]]]              # Queries for unit histogram by name, per geolevel
        unit_dp_query_prop: Dict[str, Union[Tuple[Fraction], List[Fraction]]]          # Per geolevel, shares of within-geolevel budgets dedicated to each query
        vacancy_dp_query_names: Dict[str, Union[Tuple[Fraction], List[str]]]           # Queries for unit histogram that use separate (vacancy) budget by name, per geolevel
        vacancy_dp_query_prop: Dict[str, Union[Tuple[Fraction], List[Fraction]]]       # Per geolevel, shares of within-geolevel budgets dedicated to each query
        queries_dict: Dict[str, querybase.AbstractLinearQuery]                         # Dictionary with actual query objects

        def __init__(self, budget, **kwargs):
            super().__init__(**kwargs)

            try:
                strategy = StrategySelector.strategies[budget.getconfig("strategy")].make(budget.levels)
                self.dp_query_names = strategy[CC.DPQUERIES]
                self.dp_query_prop = strategy[CC.QUERIESPROP]
                self.unit_dp_query_names = strategy[CC.UNITDPQUERIES]
                self.unit_dp_query_prop = strategy[CC.UNITQUERIESPROP]
                self.vacancy_dp_query_names = strategy[CC.VACANCYDPQUERIES]
                self.vacancy_dp_query_prop = strategy[CC.VACANCYQUERIESPROP]

            except (NoOptionError, NoSectionError):
                raise DASConfigError("DPQuery strategy has to be set", section=CC.BUDGET, option="strategy")

            # ### GETTING
            #
            # try:
            #     dp_query_names = budget.gettuple(CC.DPQUERIES, sep=CC.REGEX_CONFIG_DELIM)
            # except (NoOptionError, NoSectionError):
            #     msg = f"For manual workload setup, [{CC.BUDGET}]/{CC.DPQUERIES} has to be set, but it is empty."
            #     raise DASConfigError(msg, section=CC.BUDGET, option=f"{CC.DPQUERIES}")
            #
            # unit_dp_query_names = budget.gettuple(CC.UNITDPQUERIES, sep=CC.REGEX_CONFIG_DELIM, default=())
            # vacancy_dp_query_names = budget.gettuple(CC.VACANCYDPQUERIES, sep=CC.REGEX_CONFIG_DELIM, default=())
            #
            # self.dp_query_names = defaultdict(list)
            # self.unit_dp_query_names = defaultdict(list)
            # self.vacancy_dp_query_names = defaultdict(list)
            # for geolevel in budget.geolevel_prop_budgets_dict:
            #     self.dp_query_names[geolevel] = dp_query_names
            #     self.unit_dp_query_names[geolevel] = unit_dp_query_names
            #     self.vacancy_dp_query_names[geolevel] = vacancy_dp_query_names
            #
            # self.dp_query_prop = {}
            # self.unit_dp_query_prop = {}
            # self.vacancy_dp_query_prop = {}
            #
            # for geolevel in budget.geolevel_prop_budgets_dict:
            #
            #
            #     budget.log_and_print(f"Finding budget for geolevel {geolevel}...")
            #     if budget.config.has_option(CC.BUDGET, CC.QUERIESPROP + '|' + geolevel):
            #         self.dp_query_prop[geolevel] = budget.gettuple_of_fractions(f"{CC.QUERIESPROP}|{geolevel}", section=CC.BUDGET,
            #                                                                     sep=CC.REGEX_CONFIG_DELIM)
            #     elif budget.config.has_option(CC.BUDGET, CC.QUERIESPROP):
            #         self.dp_query_prop[geolevel] = budget.gettuple_of_fractions(CC.QUERIESPROP, section=CC.BUDGET, sep=CC.REGEX_CONFIG_DELIM)
            #     else:
            #         raise NoOptionError(f"{CC.QUERIESPROP + '|' + geolevel} or {CC.QUERIESPROP}", section=CC.BUDGET)
            #
            #     print(f"{geolevel} DPquery names: {self.dp_query_names[geolevel]}")
            #
            #     budget_split_log_msg = f"The sequential-composition budget allocation between queries in a geolevel is:"
            #     budget_split_log_msg += f"{geolevel} \nDPQueries: {self.dp_query_prop[geolevel]} "
            #     budget_split_log_msg += f"({','.join(map(str, map(float, self.dp_query_prop[geolevel])))})"
            #
            #     if self.unit_dp_query_names[geolevel]:
            #         self.unit_dp_query_prop[geolevel] = budget.gettuple_of_fractions(CC.UNITQUERIESPROP, section=CC.BUDGET, sep=CC.REGEX_CONFIG_DELIM)
            #         print(f"Unit DPquery names: {self.unit_dp_query_names[geolevel]}")
            #
            #     if self.vacancy_dp_query_names[geolevel]:
            #         self.vacancy_dp_query_prop[geolevel] = budget.gettuple_of_fractions(CC.VACANCYQUERIESPROP, section=CC.BUDGET, sep=CC.REGEX_CONFIG_DELIM)
            #         print(f"Unit DPquery names (Vacancy): {self.vacancy_dp_query_names}")
            #
            #     budget.log_and_print(budget_split_log_msg)

            # FILL QUERY DICT
            self.queries_dict = {}
            for geolevel in budget.geolevel_prop_budgets_dict:
                self.queries_dict.update(budget.schema_obj.getQueries(self.dp_query_names[geolevel]))
                self.queries_dict.update(budget.unit_schema_obj.getQueries(self.unit_dp_query_names[geolevel]))
                self.queries_dict.update(budget.unit_schema_obj.getQueries(self.vacancy_dp_query_names[geolevel]))

            ## CHECKING

            for geolevel in budget.geolevel_prop_budgets_dict:

                # Make a list to check later if it sums up to 1.
                budget_per_each_query: list = []

                # Vacancy query have separate budget
                budget_per_each_vacancy_query: list = []

                budget_per_each_query.extend(list(self.dp_query_prop[geolevel]))

                self.checkUnique(self.dp_query_names[geolevel], CC.DPQUERIES)
                self.checkUnique(self.unit_dp_query_names[geolevel], CC.UNITDPQUERIES)
                self.checkUnique(self.vacancy_dp_query_names[geolevel], CC.VACANCYDPQUERIES)

                # Print all levels, on which the measurements are taken:
                self.printLevelsOfMarginals(budget, self.dp_query_names[geolevel], budget.schema_obj, 'main histogram')
                self.printLevelsOfMarginals(budget, self.unit_dp_query_names[geolevel], budget.unit_schema_obj, 'unit histogram')
                self.printLevelsOfMarginals(budget, self.vacancy_dp_query_names[geolevel], budget.unit_schema_obj, 'vacancy')

                budget.checkDyadic(self.dp_query_prop[geolevel], msg="queries")
                self.checkQueryImpactGaps(budget, self.queryPropPairs(geolevel), f"{geolevel} {CC.DPQUERIES}")

                if self.unit_dp_query_names[geolevel]:
                    # Add the fractions of per-geolevel budgets dedicated to each query to the list that should sum up to 1.
                    budget_per_each_query.extend(list(self.unit_dp_query_prop[geolevel]))
                    budget.checkDyadic(self.unit_dp_query_prop[geolevel], msg="unit queries")
                    self.checkQueryImpactGaps(budget, self.unitQueryPropPairs(geolevel), CC.UNITDPQUERIES)

                if self.vacancy_dp_query_names[geolevel]:
                    # Add the fractions of per-geolevel budgets dedicated to each query to the list that should sum up to 1.
                    budget_per_each_vacancy_query.extend(list(self.vacancy_dp_query_prop[geolevel]))
                    budget.checkDyadic(self.vacancy_dp_query_prop[geolevel], msg="vacancy queries")
                    self.checkQueryImpactGaps(budget, self.vacancyQueryPropPairs(geolevel), CC.VACANCYDPQUERIES)

                assertSumTo(budget_per_each_query, msg="Within-geolevel Budget Proportion")
                assertEachPositive(budget_per_each_query, "queries")

                if len(budget_per_each_vacancy_query) > 0:
                    assertSumTo(budget_per_each_vacancy_query, msg="Within-geolevel Budget Proportion (Vacancy budget)")
                    assertEachPositive(budget_per_each_vacancy_query, "vacancy queries")

        def queryPropPairs(self, geolevel):
            """ Generator of query and it's proportion tuples within geolevel"""
            assert len(self.dp_query_names[geolevel]) == len(self.dp_query_prop[geolevel]), f"Lengths of DPquery and their PLB vectors not equal, geolevel {geolevel}"
            for qname, qprop in zip(self.dp_query_names[geolevel], self.dp_query_prop[geolevel]):  # Change to self.query_budget.dp_query_names[geolevel] when we allow different queries in geolevels
                query = self.queries_dict[qname]
                yield query, qprop

        def unitQueryPropPairs(self, geolevel):
            """ Generator of query and it's proportion tuples within geolevel"""
            if self.unit_dp_query_names[geolevel]:
                assert len(self.unit_dp_query_names[geolevel]) == len(self.unit_dp_query_prop[geolevel]), f"Lengths of Unit DPquery and their PLB vectors not equal, geolevel {geolevel}"
                for qname, qprop in zip(self.unit_dp_query_names[geolevel], self.unit_dp_query_prop[geolevel]):  # Change to self.query_budget.dp_query_names[geolevel] when we allow different queries in geolevels
                    query = self.queries_dict[qname]
                    yield query, qprop

        def vacancyQueryPropPairs(self, geolevel):
            """ Generator of query and it's proportion tuples within geolevel"""
            if self.vacancy_dp_query_names[geolevel]:
                assert len(self.vacancy_dp_query_names[geolevel]) == len(self.vacancy_dp_query_prop[geolevel]), f"Lengths of Vacancy DPquery and their PLB vectors not equal, geolevel {geolevel}"
                for qname, qprop in zip(self.vacancy_dp_query_names[geolevel], self.vacancy_dp_query_prop[geolevel]):  # Change to self.query_budget.dp_query_names[geolevel] when we allow different queries in geolevels
                    query = self.queries_dict[qname]
                    yield query, qprop

        @staticmethod
        def checkUnique(querynames, option_name):
            sorted_marginals_names = sortMarginalNames(querynames)
            if len(sorted_marginals_names) > len(set(sorted_marginals_names)):
                raise DASConfigValdationError(f"Some of the queries {sorted_marginals_names} are slated to be measured more than once",
                                              section=CC.BUDGET, options=(option_name,))

        @staticmethod
        def checkQueryImpactGaps(das_module, queries: Generator[Tuple[querybase.AbstractLinearQuery, Any], None, None], config_option):
            """Calculates impact of query on each cell of the histogram. Raises errors if there are impact gaps."""
            das_module.log_and_print(f"###\nImpact of DP queries ([{CC.BUDGET}]/{config_option}) to be measured:")
            # total_impact = 0
            # for qname, prop in zip(das_module.dp_query_names, das_module.dp_query_prop):  # WARNING: names and prop vectors should be passed as arguments if total is used
            #     query = das_module.queries_dict[qname]
            for query, _ in queries:
                qname = query.name
                # This is just the sum
                # impact = (np.ones(query.numAnswers()) @ np.abs(query.matrixRep()))  # factor of eps/sens doesn't matter here
                impact = np.abs(query.matrixRep()).sum(axis=0)
                # total_impact += impact * prop  # to do this, need to do composition, multiplying by proportion, like here,  only works for pure, epsilon-DP
                impmin, impmax = impact.min(), impact.max()
                das_module.log_and_print(f"{qname} ~ Impact\n {'':50} Min: {impmin}, Max: {impmax}, All: {impact}", cui=False)

                if abs(impmin - impmax) > 1e-7:
                    das_module.log_and_print(query, cui=False)
                    raise DASConfigValdationError(f"There is an impact gap underutilizing parallel composition in query {qname}", section=CC.BUDGET,
                                                  options=(config_option,))

                # Having both below is redundant, but for clarity and future flexibility including both
                if impmin != 1:
                    das_module.log_and_print(query, cui=False)
                    raise DASConfigValdationError(f"Some histogram cells are under-measured in query {qname}", section=CC.BUDGET,
                                                  options=(config_option,))
                if impmax != 1:
                    das_module.log_and_print(query, cui=False)
                    raise DASConfigValdationError(f"Some histogram cells are measured more than once in query {qname}", section=CC.BUDGET,
                                                  options=(config_option,))

            # das_module.log_and_print(f"TOTAL ~ Impact\n {'':50} Min: {total_impact.min()}, Max: {total_impact.max()}, All: {total_impact}", cui=False)
            # if abs(total_impact.min() != total_impact.max()) > 1e-7:
            #     raise DASConfigValdationError(f"There is an impact gap underutilizing parallel composition in DP queries", section=CC.BUDGET,
            #                                   options=(config_option,))

        @staticmethod
        def printLevelsOfMarginals(das_module, queries, schema, qset_name):
            """Print levels of every marginal of the queries"""
            dpq_marginals = set()
            for qname in queries:
                dpq_marginals = dpq_marginals.union(qname.split(CC.SCHEMA_CROSS_JOIN_DELIM))
            das_module.log_and_print(f"###\nLevels of the marginals of {qset_name} DP queries to be measured:")
            for qname in dpq_marginals:
                if qname != 'detailed':
                    das_module.log_and_print(f"{qname} levels:\n------------------------\n" +
                                       "\n".join(schema.getQueryLevel(qname)) +
                                       "\n---------------------------------", cui=False)


def assertSumTo(values: Iterable, sumto=1., dec_place=CC.BUDGET_DEC_DIGIT_TOLERANCE, msg="The ") -> None:
    """
    Assert that sum of the values in the iterable is equal to the desired value with set tolerance
    :param values: iterable, sum of which is to be checked
    :param sumto: float, what it should sum to, default=1.
    :param dec_place: int, tolerance of the sum check, defined by decimal place (approximately, calculated by powers of 2)
    :param msg: Custom error message prefix
    :return:
    """
    error_msg = f"{msg} values {values} sum to {sum(values)} instead of {sumto}"
    assert(abs(sum(values) - sumto)) < 2 ** (-dec_place * 10. / 3.), error_msg    # f-string won't evaluate properly if is in assert


def assertEachPositive(values: Iterable, msg=""):
    """ Assert that each element of values iterable is positive"""
    error_msg = f"Negative proportion factor present in {msg} budget allocation: {values}"
    assert np.all(np.array(values) >= 0), error_msg  # f-string won't evaluate properly if is in assert
