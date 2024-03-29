import numpy as np

from programs.invariants.tests.invariant_test_generic_class import InvariantTestGenericNoUnits

from constants import CC


class TestInvariantsPL94(InvariantTestGenericNoUnits):

    schema_name = CC.SCHEMA_PL94

    d = np.array(
        [  # columns: 'hhgq', 'votingage', 'hispanic', 'cenrace', 'unique unitid' (shape 8,2,2,63 + unitUID)
            # each row is a person
            [0, 1, 1, 20, 0],
            [1, 1, 0, 1, 1],
            [2, 0, 0, 10, 2],
            [2, 0, 0, 10, 2]
        ]
    )

    invariant_names = ('tot', )


    def test_va(self):
        inv = self.get_inv_dict(self.p_h_data1(), ('va',))
        assert inv['va'] == 2

    def test_gqhh_vect(self):
        inv = self.get_inv_dict(self.p_h_data1(), ('gqhh_vect',))
        assert np.array_equal(inv['gqhh_vect'], np.array([1, 1, 1, 0, 0, 0, 0, 0]))

    def test_gq_vect(self):
        inv = self.get_inv_dict(self.p_h_data1(), ('gq_vect',))
        assert inv['gq_vect'] == 2

    def test_gqhh_tot(self):
        inv = self.get_inv_dict(self.p_h_data1(), ('gqhh_tot',))
        assert inv['gqhh_tot'] == 3

    def test_all_inv(self):
        inv = self.get_inv_dict(self.p_h_data1(), ('tot', 'va', 'gqhh_vect', 'gqhh_tot', 'gq_vect',))
        assert len(inv.items()) == 5
        assert inv['tot'] == 4
        assert inv['va'] == 2
        assert np.array_equal(inv['gqhh_vect'], np.array([1, 1, 1, 0, 0, 0, 0, 0]))
        assert inv['gq_vect'] == 2
        assert inv['gqhh_tot'] == 3
