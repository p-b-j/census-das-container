"""
Module that acquires (extracts from config or otherwise) DP query orderings (both for use and to constrain) in the optimization passes
(both L2 and Rounder)
"""
from collections import defaultdict
from configparser import NoOptionError
from functools import reduce
from operator import add

import numpy as np

from exceptions import DASConfigValdationError, DASConfigError
from programs.schema.schema import sortMarginalNames
import programs.queries.querybase as querybase
import programs.queries.constraints_dpqueries as cons_dpq

from programs.strategies.strategies import QueryOrderingSelector

from das_framework.driver import AbstractDASModule
from constants import CC


class OptimizationQueryOrdering(AbstractDASModule):

    def __init__(self, budget, schema, unit_hist_shape, **kwargs):
        super().__init__(name=CC.GUROBI_SECTION, **kwargs)

        self.budget = budget
        self.schema_obj = schema
        self.unit_hist_shape = unit_hist_shape

        # TODO: Remove supposrt for Robert's Est and Qadd and opt_dict or make sure it works
        l2_approach = self.getconfig(CC.L2_OPTIMIZATION_APPROACH, default=CC.SINGLE_PASS_REGULAR)
        self.est_and_qadd_queries = (l2_approach == CC.DATA_IND_USER_SPECIFIED_QUERY_NPASS_PLUS)
        # multi-pass optimization, makes Optimization Dictionary
        self.opt_dict = self.setOptDict()

        self.optimizers, self.query_ordering, self.rounder_query_names = self.setOptimizersAndQueryOrderings(budget.levels)

    def setOptDict(self):
        """ Parses the Config for the multipass optimization steps"""

        if not self.est_and_qadd_queries:
            return None

        opt_dict = {}

        i = 0
        type_name = "Part"
        while True:
            try:
                ESTqs = self.gettuple(f"L2_DPquery{type_name}{i}_Est", section=CC.BUDGET, sep=',')
                Qadds = self.gettuple(f"L2_DPquery{type_name}{i}_Qadd", section=CC.BUDGET, sep=',')
            except NoOptionError:
                if i > 0:
                    self.log_and_print(
                        f"L2_DPquery{type_name}{i} not found in config. Assuming L2_DPquery{type_name}{i - 1} is end of queries partition.")
                else:
                    self.log_and_print(f"L2_DPquery{type_name}{i} not found in config. End of parts.")
                break

            # each ordering is a dictionary containing the two parts
            opt_dict[i] = {"Est": ESTqs, "Qadd": Qadds}
            self.log_and_print(f"Setting DPqueryOrdering[{i}] = {ESTqs} and {Qadds}")
            i += 1
        self.log_and_print("opt_dict", opt_dict)
        return opt_dict

    def setOptimizersAndQueryOrderings(self, levels):
        """
        For engines with queries set in config (e.g. topdown, bottomup)
        Read the queries from config, and set their budget allocations. Check that allocation proportions sum to one/
        :return:
        """

        # If a multipass approach was specified for L2 or Rounder, get the order in which it specifies to optimize queries
        l2_optimization_approach = self.getconfig(CC.L2_OPTIMIZATION_APPROACH, section=CC.GUROBI_SECTION, default=CC.SINGLE_PASS_REGULAR)
        rounder_optimization_approach = self.getconfig(CC.ROUNDER_OPTIMIZATION_APPROACH, section=CC.GUROBI_SECTION, default=CC.CELLWISE_ROUNDER)

        seq_opt_name = self.getconfig(CC.SEQ_OPT_OPTIMIZATION_APPROACH, section=CC.GUROBI_SECTION, default=CC.L2_PLUS_ROUNDER_WITH_BACKUP)
        outer_pass = seq_opt_name == CC.L2_PLUS_ROUNDER_WITH_BACKUP_INTERLEAVED

        optimizers = (seq_opt_name, l2_optimization_approach, rounder_optimization_approach)

        if self.config.has_option(CC.BUDGET, "query_ordering"):
            query_ordering = QueryOrderingSelector.query_orderings[self.getconfig("query_ordering", section=CC.BUDGET)].make(levels)
        else:
            # TODO: Uncomment this line to deprecate support to old configs. And remove or comment the code below, within "else"
            #  Or just return empty query_ordering?
            raise DASConfigError("", "query_ordering", CC.BUDGET)

            # ## GETTING
            # l2_optimizer_name = "L2" if l2_optimization_approach == CC.DATA_IND_USER_SPECIFIED_QUERY_NPASS else None
            # generic_l2_dp_query_ordering = self.getQueryOrdering(mode=(l2_optimizer_name, outer_pass))
            #
            # if seq_opt_name == CC.L2_PLUS_ROUNDER_WITH_BACKUP_INTERLEAVED:
            #     generic_l2_constrain_to_query_ordering = self.getQueryOrdering(mode=("ConstrainL2", outer_pass))
            #     if generic_l2_constrain_to_query_ordering == {}:
            #         generic_l2_constrain_to_query_ordering = generic_l2_dp_query_ordering
            # else:
            #     generic_l2_constrain_to_query_ordering = generic_l2_dp_query_ordering
            #
            # rounder_name = "Rounder" if rounder_optimization_approach in (CC.MULTIPASS_ROUNDER, CC.MULTIPASS_QUERY_ROUNDER) else None
            # generic_rounder_dp_query_ordering = self.getQueryOrdering(mode=(rounder_name, outer_pass))
            #
            # query_ordering = {}
            # for geolevel in self.budget.levels:
            #     query_ordering[geolevel] = {
            #         CC.L2_QUERY_ORDERING: generic_l2_dp_query_ordering,
            #         CC.L2_CONSTRAIN_TO_QUERY_ORDERING: generic_l2_constrain_to_query_ordering,
            #         CC.ROUNDER_QUERY_ORDERING: generic_rounder_dp_query_ordering,
            #     }

        # Fill rounder_queries
        rounder_query_names = {}
        for geolevel, qo_dict_geolevel in query_ordering.items():
            rounder_query_ordering = qo_dict_geolevel[CC.ROUNDER_QUERY_ORDERING]
            if rounder_query_ordering is None:
                continue
            if not outer_pass:
                rounder_query_names[geolevel] = reduce(add, rounder_query_ordering.values())
            else:
                rounder_query_names[geolevel] = reduce(add, map(lambda opd: reduce(add, opd.values()), rounder_query_ordering.values()))

        ### CHECKING
        assert len(query_ordering) == len(levels), "Query ordering geolevels lengths is different from engine/budget geolevels, check the strategy"
        for geolevel, qo_dict_geolevel in query_ordering.items():
            l2_dp_query_ordering = qo_dict_geolevel[CC.L2_QUERY_ORDERING]
            if l2_dp_query_ordering is None:
                continue
            l2_target_queries = []
            options_list = []

            if not outer_pass:
                for pn, qnames in l2_dp_query_ordering.items():
                    l2_target_queries.extend(qnames)
                    options_list.append(f"L2_DPqueryPart{pn}")
            else:
                for opn in l2_dp_query_ordering.keys():
                    for ipn, qnames in l2_dp_query_ordering[opn].items():
                        l2_target_queries.extend(qnames)
                        options_list.append(f"L2_DPqueryPart{opn}_{ipn}")
            l2_target_queries = sortMarginalNames(l2_target_queries)

            # if len(l2_target_queries) > len(set(l2_target_queries)):
            #    raise DASConfigValdationError(f"Some queries {l2_target_queries} are targeted in L2 optimization more than once",
            #                                  section=CC.BUDGET, options=options_list)
            # # NOTE: this is no longer a requirement with constrain-to config specification.
            # l2_target_queries = sortMarginalNames(l2_target_queries)

            measured_dp_queries = sortMarginalNames(self.budget.query_budget.dp_query_names[geolevel])

            if len(set(measured_dp_queries) - set(l2_target_queries)) > 0:
                raise DASConfigValdationError(
                    f"Some of the measured DP queries ({measured_dp_queries}) are not targeted in L2 optimization {l2_target_queries}",
                    section=CC.BUDGET, options=options_list)

            print(f"Detected {geolevel} l2_dp_query_ordering: {query_ordering[geolevel][CC.L2_QUERY_ORDERING]}")
            print(f"Detected {geolevel} l2_ConstrainTo_dp_query_ordering: {query_ordering[geolevel][CC.L2_CONSTRAIN_TO_QUERY_ORDERING]}")
            print(f"Detected {geolevel} rounder_dp_query_ordering: {query_ordering[geolevel][CC.ROUNDER_QUERY_ORDERING]}")

        return optimizers, query_ordering, rounder_query_names

    def getQueryOrdering(self, mode=None):
        """
            If a multipass optimization approach was specified, this fxn is used to build a dictionary mapping query names to
            the pass number in which they should be optimized

            Inputs:
                mode : string (current options are "L2" or "Rounder")
        """
        optimizer_name, outer_pass = mode
        if optimizer_name is None:
            return None

        dp_query_ordering = {} if not outer_pass else defaultdict(dict)

        outer_pass_found = True
        outer = 0
        while outer_pass_found:
            inner = 0
            while True:
                match_str = f"{optimizer_name}_DPqueryPart{inner}" if not outer_pass else f"{optimizer_name}_DPqueryPart{outer}_{inner}"
                try:
                    current_pass_dpqs = self.gettuple(match_str, section=CC.BUDGET)
                except NoOptionError:
                    msg = f"{match_str} not in config. Concluding search for inner DPquery passes."
                    print(msg)
                    if inner == 0 or not outer_pass:
                        outer_pass_found = False  # If we failed to find even a single inner pass, abort outer pass search
                    break
                if not outer_pass:
                    dp_query_ordering[inner] = current_pass_dpqs
                    print(f"Setting {optimizer_name}_DPqueryOrdering[{inner}] = {dp_query_ordering[inner]}")
                else:
                    dp_query_ordering[outer][inner] = current_pass_dpqs
                    print(f"Setting {optimizer_name}_DPqueryOrdering[{outer}][{inner}] = {dp_query_ordering[outer][inner]}")
                inner += 1
            outer += 1
        return dp_query_ordering

    def makeOptQueries(self, dp_geounit_node):
        """
        Makes the query objects from what is in the opt_dict
        """
        # NOTES: This works only on main histogram queries
        opt_dict = self.opt_dict.copy()   # To keep "Qadd" query names in every node
        constraints = {}
        for npass, npass_queries in self.opt_dict.items():
            # This will throw error if qname is not valid in main histogram schema, so ok. ("total" and "detailed" are valid for anything, so they always mean main)
            est_queries_dict = self.setup.schema_obj.getQueries(npass_queries["Est"])
            for qname, query in est_queries_dict.items():
                n_ans = query.numAnswers()
                query_shape = int(np.prod(self.unit_hist_shape)), n_ans
                rhs = np.zeros(n_ans)
                new_query = querybase.MultiHistQuery((query, querybase.StubQuery(query_shape, "stub")), (1, 0), name=qname)
                constraints[qname] = cons_dpq.Constraint(new_query, rhs=rhs, sign="ge", name=qname)
            opt_dict[npass]["Est"] = est_queries_dict   # Replace "Est" query names with queries themselves

        # add to the node
        dp_geounit_node.setOptDict({"npass_info": opt_dict, "Cons": constraints})

        return dp_geounit_node
