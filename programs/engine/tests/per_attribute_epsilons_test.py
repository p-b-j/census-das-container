from configparser import ConfigParser
import pytest
import numpy as np

from programs.engine.topdown_engine import TopdownEngine

from programs.schema.schemas.schemamaker import SchemaMaker
from programs.schema.attributes.sex import SexAttr as SEX
from programs.schema.attributes.hhgq_person_simple import HHGQPersonSimpleAttr as HHGQ
from programs.schema.attributes.votingage import VotingAgeAttr as VOTING_AGE
from programs.schema.attributes.hisp import HispAttr as HISPANIC
from programs.schema.attributes.cenrace import CenraceAttr as CENRACE

import programs.das_setup as ds
from fractions import Fraction

from constants import CC

class TestPerAttributeEpsilons:

    class MFURSetup(ds.DASDecennialSetup):
        """
        Setup module just for this test. Only what is needed.
        """
        def __init__(self):
            self.privacy_framework = "zcdp"
            self.schema = "PL94"
            self.hist_shape = (8,2,2,63)
            self.unit_hist_shape = (2,)
            self.hist_vars = ("hhgq","votingage", "hisp", "cenrace")
            self.schema_obj = SchemaMaker.fromAttlist("PL94", [HHGQ, VOTING_AGE, HISPANIC, CENRACE])
            self.unit_schema_obj = SchemaMaker.fromAttlist("justsex", [SEX])
            self.validate_input_data_constraints = False
            self.spine_type = 'non_aian_spine'
            self.plb_allocation = None
            self.geocode_dict = {5: "Block", 4:"Block_Group", 3:"Tract", 2:"County", 1:"State", 0:"US"}
            self.dp_mechanism_name = CC.GEOMETRIC_MECHANISM
            self.inv_con_by_level = {
                'Block': {
                    'invar_names': (),
                    'cons_names': (),
                },
                'Block_Group': {
                    'invar_names': (),
                    'cons_names': (),
                },
                'Tract': {
                    'invar_names': (),
                    'cons_names': (),
                },
                'County': {
                    'invar_names': (),
                    'cons_names': ()
                },
                'State': {
                    'invar_names': (),
                    'cons_names': ()
                },
                'US': {
                    'invar_names': (),
                    'cons_names': ()
                }
            }
            self.levels = list(self.inv_con_by_level.keys())
            self.geo_bottomlevel = 'Block'
            self.geolevel_prop_budgets = (Fraction(44,1024), Fraction(44,1024), Fraction(44/1024),
                                            Fraction(44,1024), Fraction(127,1024), Fraction(721,1024))
            self.postprocess_only = False
            self.only_dyadic_rationals = False

        @staticmethod
        def makeInvariants(raw, raw_housing, invariant_names):
            inv_dict = {}
            if 'tot' in invariant_names:
                inv_dict.update({'tot': np.sum(raw.toDense())})
            return inv_dict

        @staticmethod
        def makeConstraints(hist_shape, invariants, constraint_names):
            cons_dict = {}
            return cons_dict

    def getEngine(self, engine, setup_instance, use_spark, das_stub):
        engine_s_config = """
                  [gurobi]
                  seq_optimization_approach = L2PlusRounderWithBackup_interleaved

                  [budget]
                  print_per_attr_epsilons= True
                  global_scale: 343/256
                  strategy: strategy1a
                  query_ordering: redistricting_regular_ordering_1a

                  #budget in topdown order (e.g. US, State, .... , Block)
                  geolevel_budget_prop: 44/1024, 44/1024, 44/1024, 44/1024, 127/1024, 721/1024

                  [engine]
                  use_spark: False
                  """
        engine_config = ConfigParser()
        engine_config.read_string(engine_s_config)
        engine_config.set(section='engine', option='spark', value=str(use_spark))
        engine_instance = engine(config=engine_config, setup=setup_instance, name='engine', das=das_stub)
        return engine_instance

    @pytest.mark.parametrize("framework, expected_per_attr_eps, expected_per_geolevel_eps", [
        ("zcdp",
         dict([('hhgq', 3.5980860888957977),
               ('votingage', 4.729195237159729),
               ('hispanic', 4.729195237159729),
               ('cenrace', 4.729195237159729)]),
         dict([('US', 7.083721309900284),
               ('State', 6.907723397016525),
               ('County', 6.72818124294281),
               ('Tract', 6.544831171631813),
               ('Block_Group', 5.991352275013924)])
         ),
        ("pure_dp",
         dict([('hhgq', 0.20355155049032597),
               ('votingage', 0.3392525841505434),
               ('hispanic', 0.3392525841505434),
               ('cenrace', 0.3392525841505434)]),
         dict([('US', 0.7142857142857141),
               ('State', 0.682215743440233),
               ('County', 0.650145772594752),
               ('Tract', 0.6180758017492709),
               ('Block_Group', 0.5255102040816325)])
         ),
    ])
    def test_per_attribute_epsilons(self, framework, expected_per_attr_eps, expected_per_geolevel_eps, dd_das_stub):

        # zCDP per-attribute epsilon checks
        setup_instance = self.MFURSetup()
        setup_instance.use_spark = False
        use_spark = False

        engine_instance = self.getEngine(TopdownEngine, setup_instance, use_spark, dd_das_stub)
        engine_instance.setup.privacy_framework = framework
        engine_instance.config.set(CC.ENGINE, CC.CHECK_BUDGET, "off")
        engine_instance.initializeAndCheckParameters()

        for attr_name, attr_eps in engine_instance.budget.per_attr_epsilons.items():
            np.testing.assert_approx_equal(attr_eps, expected_per_attr_eps[attr_name], significant=5)
        for geolevel_name, geolevel_eps in engine_instance.budget.per_geolevel_epsilons.items():
            np.testing.assert_approx_equal(geolevel_eps, expected_per_geolevel_eps[geolevel_name], significant=5)
