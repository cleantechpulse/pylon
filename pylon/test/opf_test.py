#------------------------------------------------------------------------------
# Copyright (C) 2010 Richard Lincoln
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------

""" Defines a test case for AC power flow.
"""

#------------------------------------------------------------------------------
#  Imports:
#------------------------------------------------------------------------------

import unittest

from os.path import join, dirname

from scipy import alltrue
from scipy.io.mmio import mmread

from pylon import Case, OPF
from pylon.opf import DCOPFSolver, PIPSSolver
from pylon.util import mfeq2

#------------------------------------------------------------------------------
#  Constants:
#------------------------------------------------------------------------------

DATA_DIR = join(dirname(__file__), "data")

#------------------------------------------------------------------------------
#  "DCOPFTest" class:
#------------------------------------------------------------------------------

class DCOPFTest(unittest.TestCase):
    """ Defines a test case for DC OPF.
    """

    def __init__(self, methodName='runTest'):
        super(DCOPFTest, self).__init__(methodName)

        self.case_name = "case30pwl"
        self.case = None
        self.opf = None


    def setUp(self):
        """ The test runner will execute this method prior to each test.
        """
        self.case = Case.load(join(DATA_DIR, self.case_name, "case.pkl"))
        self.opf = OPF(self.case, dc=True)


    def testVa(self):
        """ Test voltage angle variable.
        """
        bs, _, _ = self.opf._remove_isolated(self.case)
        _, refs = self.opf._ref_check(self.case)
        Va = self.opf._get_voltage_angle_var(refs, bs)

        mpVa0 = mmread(join(DATA_DIR, self.case_name, "opf", "Va0.mtx"))
        mpVal = mmread(join(DATA_DIR, self.case_name, "opf", "Val.mtx"))
        mpVau = mmread(join(DATA_DIR, self.case_name, "opf", "Vau.mtx"))

        self.assertTrue(alltrue(Va.v0 == mpVa0.flatten()))
        self.assertTrue(alltrue(Va.vl == mpVal.flatten()))
        self.assertTrue(alltrue(Va.vu == mpVau.flatten()))


    def testVm(self):
        """ Test voltage magnitude variable.
        """
        bs, _, gn = self.opf._remove_isolated(self.case)
        Vm = self.opf._get_voltage_magnitude_var(bs, gn)

        mpVm0 = mmread(join(DATA_DIR, self.case_name, "opf", "Vm0.mtx"))

        self.assertTrue(alltrue(Vm.v0 == mpVm0.flatten()))


    def testPg(self):
        """ Test active power variable.
        """
        self.case.sort_generators() # ext2int
        _, _, gn = self.opf._remove_isolated(self.case)
        Pg = self.opf._get_pgen_var(gn, self.case.base_mva)

        mpPg0 = mmread(join(DATA_DIR, self.case_name, "opf", "Pg0.mtx"))
        mpPmin = mmread(join(DATA_DIR, self.case_name, "opf", "Pmin.mtx"))
        mpPmax = mmread(join(DATA_DIR, self.case_name, "opf", "Pmax.mtx"))

        self.assertTrue(alltrue(Pg.v0 == mpPg0.flatten()))
        self.assertTrue(alltrue(Pg.vl == mpPmin.flatten()))
        self.assertTrue(alltrue(Pg.vu == mpPmax.flatten()))


    def testQg(self):
        """ Test reactive power variable.
        """
        self.case.sort_generators() # ext2int
        _, _, gn = self.opf._remove_isolated(self.case)
        Qg = self.opf._get_qgen_var(gn, self.case.base_mva)

        mpQg0 = mmread(join(DATA_DIR, self.case_name, "opf", "Qg0.mtx"))
        mpQmin = mmread(join(DATA_DIR, self.case_name, "opf", "Qmin.mtx"))
        mpQmax = mmread(join(DATA_DIR, self.case_name, "opf", "Qmax.mtx"))

        self.assertTrue(alltrue(Qg.v0 == mpQg0.flatten()))
        self.assertTrue(alltrue(Qg.vl == mpQmin.flatten()))
#        self.assertTrue(alltrue(Qg.vu == mpQmax.flatten()))
        self.assertTrue(max(abs(Qg.vu - mpQmax.flatten())) < 1e-12)


    def testPmis(self):
        """ Test active power mismatch constraints.
        """
        case = self.case
        case.sort_generators() # ext2int
        B, _, Pbusinj, _ = case.Bdc
        bs, _, gn = self.opf._remove_isolated(case)
        Pmis = self.opf._power_mismatch_dc(bs, gn, B, Pbusinj, case.base_mva)

        mpAmis = mmread(join(DATA_DIR, self.case_name, "opf", "Amis.mtx"))
        mpbmis = mmread(join(DATA_DIR, self.case_name, "opf", "bmis.mtx"))

        self.assertTrue(mfeq2(Pmis.A, mpAmis.tocsr()))
#        self.assertTrue(alltrue(Pmis.l == mpbmis.flatten()))
        self.assertTrue(max(abs(Pmis.l - mpbmis.flatten())) < 1e-12)
#        self.assertTrue(alltrue(Pmis.u == mpbmis.flatten()))
        self.assertTrue(max(abs(Pmis.u - mpbmis.flatten())) < 1e-12)


    def testPfPt(self):
        """ Test branch flow limit constraints.
        """
        _, ln, _ = self.opf._remove_isolated(self.case)
        _, Bf, _, Pfinj = self.case.Bdc
        Pf, Pt = self.opf._branch_flow_dc(ln, Bf, Pfinj, self.case.base_mva)

        lpf = mmread(join(DATA_DIR, self.case_name, "opf", "lpf.mtx"))
        upf = mmread(join(DATA_DIR, self.case_name, "opf", "upf.mtx"))
        upt = mmread(join(DATA_DIR, self.case_name, "opf", "upt.mtx"))

        self.assertTrue(alltrue(Pf.l == lpf.flatten()))
        self.assertTrue(alltrue(Pf.u == upf.flatten()))
        self.assertTrue(alltrue(Pt.l == lpf.flatten()))
        self.assertTrue(alltrue(Pt.u == upt.flatten()))


    def testVang(self):
        """ Test voltage angle difference limit constraint.
        """
        self.opf.ignore_ang_lim = False
        bs, ln, _ = self.opf._remove_isolated(self.case)
        ang = self.opf._voltage_angle_diff_limit(bs, ln)

        if ang.A.shape[0] != 0:
            Aang = mmread(join(DATA_DIR, self.case_name, "opf", "Aang.mtx"))
        else:
            Aang = None
        lang = mmread(join(DATA_DIR, self.case_name, "opf", "lang.mtx"))
        uang = mmread(join(DATA_DIR, self.case_name, "opf", "uang.mtx"))

        if Aang is not None:
            self.assertTrue(mfeq2(ang.A, Aang.tocsr()))
        self.assertTrue(alltrue(ang.l == lang.flatten()))
        self.assertTrue(alltrue(ang.u == uang.flatten()))


    def testVLConstPF(self):
        """ Test dispatchable load, constant power factor constraints.
        """
        _, _, gn = self.opf._remove_isolated(self.case)
        vl = self.opf._const_pf_constraints(gn, self.case.base_mva)

        if vl.A.shape[0] != 0:
            Avl = mmread(join(DATA_DIR, self.case_name, "opf", "Avl.mtx"))
            self.assertTrue(mfeq2(vl.A, Avl.tocsr()))

        lvl = mmread(join(DATA_DIR, self.case_name, "opf", "lang.mtx"))
        self.assertTrue(alltrue(vl.l == lvl.flatten()))

        uvl = mmread(join(DATA_DIR, self.case_name, "opf", "uang.mtx"))
        self.assertTrue(alltrue(vl.u == uvl.flatten()))


#    def testPQ(self):
#        """ Test generator PQ capability curve constraints.
#        """
##        Apqh = mmread(join(DATA_DIR, self.case_name, "opf", "Apqh.mtx"))
##        ubpqh = mmread(join(DATA_DIR, self.case_name, "opf", "ubpqh.mtx"))
##        Apql = mmread(join(DATA_DIR, self.case_name, "opf", "Apql.mtx"))
##        ubpql = mmread(join(DATA_DIR, self.case_name, "opf", "ubpql.mtx"))
#        self.fail("Generator PQ capability curve constraints not implemented.")


    def testAy(self):
        """ Test basin constraints for piece-wise linear gen cost variables.
        """
        self.case.sort_generators() # ext2int
        _, _, gn = self.opf._remove_isolated(self.case)
        _, ycon = self.opf._pwl_gen_costs(gn, self.case.base_mva)

        if ycon is not None:
            Ay = mmread(join(DATA_DIR, self.case_name, "opf", "Ay_DC.mtx"))
            by = mmread(join(DATA_DIR, self.case_name, "opf", "by_DC.mtx"))

            self.assertTrue(mfeq2(ycon.A, Ay.tocsr()))
            self.assertTrue(alltrue(ycon.u == by.flatten()))

#------------------------------------------------------------------------------
#  "DCOPFSolverTest" class:
#------------------------------------------------------------------------------

class DCOPFSolverTest(unittest.TestCase):
    """ Defines a test case for the DC OPF solver.
    """

    def __init__(self, methodName='runTest'):
        super(DCOPFSolverTest, self).__init__(methodName)

        self.case_name = "case6ww"
        self.case = None
        self.opf = None
        self.om = None
        self.solver = None


    def setUp(self):
        """ The test runner will execute this method prior to each test.
        """
        self.case = Case.load(join(DATA_DIR, self.case_name, "case.pkl"))
        self.opf = OPF(self.case, dc=True)
        self.om = self.opf._construct_opf_model(self.case)
        self.solver = DCOPFSolver(self.om)


    def test_constraints(self):
        """ Test equality and inequality constraints.
        """
        AA, ll, uu = self.solver._linear_constraints(self.om)

        mpA = mmread(join(DATA_DIR, self.case_name, "opf", "A_DC.mtx"))
        mpl = mmread(join(DATA_DIR, self.case_name, "opf", "l_DC.mtx"))
        mpu = mmread(join(DATA_DIR, self.case_name, "opf", "u_DC.mtx"))

        self.assertTrue(mfeq2(AA, mpA.tocsr()))
        self.assertTrue(alltrue(ll == mpl.flatten()))
        self.assertTrue(alltrue(uu == mpu.flatten()))


    def test_var_bounds(self):
        """ Test bounds on optimisation variables.
        """
        _, xmin, xmax = self.solver._var_bounds()

#        mpx0 = mmread(join(DATA_DIR, self.case_name, "opf", "x0_DC.mtx"))
        mpxmin = mmread(join(DATA_DIR, self.case_name, "opf", "xmin_DC.mtx"))
        mpxmax = mmread(join(DATA_DIR, self.case_name, "opf", "xmax_DC.mtx"))

#        self.assertTrue(alltrue(x0 == mpx0.flatten()))
        self.assertTrue(alltrue(xmin == mpxmin.flatten()))
        self.assertTrue(alltrue(xmax == mpxmax.flatten()))


    def test_initial_point(self):
        """ Test selection of an initial interior point.
        """
        b, l, g, _ = self.solver._unpack_model(self.om)
        _, LB, UB = self.solver._var_bounds()
        _, _, _, _, _, ny, _ = self.solver._dimension_data(b, l, g)
        x0 = self.solver._initial_interior_point(b, g, LB, UB, ny)

        mpx0 = mmread(join(DATA_DIR, self.case_name, "opf", "x0_DC.mtx"))

        self.assertTrue(alltrue(x0 == mpx0.flatten()))


    def test_pwl_costs(self):
        """ Test piecewise linear costs.
        """
        b, l, g, _ = self.solver._unpack_model(self.om)
        _, ipwl, _, _, _, ny, nxyz = self.solver._dimension_data(b, l, g)
        Npwl, Hpwl, Cpwl, fparm_pwl, _ = \
            self.solver._pwl_costs(ny, nxyz, ipwl)

        if Npwl is not None:
            mpNpwl = mmread(join(DATA_DIR, self.case_name, "opf", "Npwl.mtx"))
        mpHpwl = mmread(join(DATA_DIR, self.case_name, "opf", "Hpwl.mtx"))
        mpCpwl = mmread(join(DATA_DIR, self.case_name, "opf", "Cpwl.mtx"))
        mpfparm = mmread(join(DATA_DIR, self.case_name, "opf","fparm_pwl.mtx"))

        if Npwl is not None:
            self.assertTrue(alltrue(Npwl == mpNpwl.flatten()))
        if Hpwl is not None:
            self.assertTrue(alltrue(Hpwl == mpHpwl.flatten()))
        self.assertTrue(alltrue(Cpwl == mpCpwl.flatten()))
#        self.assertTrue(alltrue(fparm_pwl == mpfparm.flatten()))


    def test_poly_costs(self):
        """ Test quadratic costs.
        """
        base_mva = self.om.case.base_mva
        b, l, g, _ = self.solver._unpack_model(self.om)
        ipol, _, _, _, _, _, nxyz = self.solver._dimension_data(b, l, g)
        Npol, Hpol, Cpol, fparm_pol, _, _ = \
            self.solver._quadratic_costs(g, ipol, nxyz, base_mva)

        mpNpol = mmread(join(DATA_DIR, self.case_name, "opf", "Npol.mtx"))
        mpHpol = mmread(join(DATA_DIR, self.case_name, "opf", "Hpol.mtx"))
        mpCpol = mmread(join(DATA_DIR, self.case_name, "opf", "Cpol.mtx"))
        mpfparm = mmread(join(DATA_DIR, self.case_name, "opf","fparm_pol.mtx"))

        self.assertTrue(mfeq2(Npol, mpNpol.tocsr()))
        self.assertTrue(mfeq2(Hpol, mpHpol.tocsr()))
        self.assertTrue(alltrue(Cpol == mpCpol.flatten()))
        self.assertTrue(alltrue(fparm_pol == mpfparm))


    def test_combine_costs(self):
        """ Test combination of pwl and poly costs.
        """
        base_mva = self.om.case.base_mva
        b, l, g, _ = self.solver._unpack_model(self.om)
        ipol, ipwl, _, _, nw, ny, nxyz = self.solver._dimension_data(b, l, g)
        Npwl, Hpwl, Cpwl, fparm_pwl, any_pwl = self.solver._pwl_costs(ny, nxyz,
                                                                      ipwl)
        Npol, Hpol, Cpol, fparm_pol, _, npol = \
            self.solver._quadratic_costs(g, ipol, nxyz, base_mva)
        NN, HHw, CCw, ffparm = \
            self.solver._combine_costs(Npwl, Hpwl, Cpwl, fparm_pwl, any_pwl,
                                       Npol, Hpol, Cpol, fparm_pol, npol, nw)

        mpNN = mmread(join(DATA_DIR, self.case_name, "opf", "NN.mtx"))
        mpHHw = mmread(join(DATA_DIR, self.case_name, "opf", "HHw.mtx"))
        mpCCw = mmread(join(DATA_DIR, self.case_name, "opf", "CCw.mtx"))
        mpffparm = mmread(join(DATA_DIR, self.case_name, "opf", "ffparm.mtx"))

        self.assertTrue(mfeq2(NN, mpNN.tocsr()))
        self.assertTrue(mfeq2(HHw, mpHHw.tocsr()))
        self.assertTrue(alltrue(CCw == mpCCw.flatten()))
        self.assertTrue(alltrue(ffparm == mpffparm))


    def test_coefficient_transformation(self):
        """ Test transformation of quadratic coefficients for w into
            coefficients for X.
        """
        base_mva = self.om.case.base_mva
        b, l, g, _ = self.solver._unpack_model(self.om)
        ipol, ipwl, _, _, nw, ny, nxyz = self.solver._dimension_data(b, l, g)
        Npwl, Hpwl, Cpwl, fparm_pwl, any_pwl = \
            self.solver._pwl_costs(ny, nxyz, ipwl)
        Npol, Hpol, Cpol, fparm_pol, polycf, npol = \
            self.solver._quadratic_costs(g, ipol, nxyz, base_mva)
        NN, HHw, CCw, ffparm = \
            self.solver._combine_costs(Npwl, Hpwl, Cpwl, fparm_pwl, any_pwl,
                                       Npol, Hpol, Cpol, fparm_pol, npol, nw)
        HH, CC, _ = \
            self.solver._transform_coefficients(NN, HHw, CCw, ffparm, polycf,
                                                any_pwl, npol, nw)

        mpHH = mmread(join(DATA_DIR, self.case_name, "opf", "HH.mtx"))
        mpCC = mmread(join(DATA_DIR, self.case_name, "opf", "CC.mtx"))

        self.assertTrue(mfeq2(HH, mpHH.tocsr()))
        self.assertTrue(alltrue(CC == mpCC.flatten()))


    def test_solution(self):
        """ Test DC OPF solution.
        """
        solution = self.solver.solve()
        lmbda = solution["lmbda"]

        mpf = mmread(join(DATA_DIR, self.case_name, "opf", "f_DC.mtx"))
        mpx = mmread(join(DATA_DIR, self.case_name, "opf", "x_DC.mtx"))
        mpmu_l = mmread(join(DATA_DIR, self.case_name, "opf", "mu_l_DC.mtx"))
        mpmu_u = mmread(join(DATA_DIR, self.case_name, "opf", "mu_u_DC.mtx"))
        mpmuLB = mmread(join(DATA_DIR, self.case_name, "opf", "muLB_DC.mtx"))
        mpmuUB = mmread(join(DATA_DIR, self.case_name, "opf", "muUB_DC.mtx"))

        self.assertAlmostEqual(solution["f"], mpf[0], places=12)
        self.assertTrue(abs(max(solution["x"] - mpx.flatten())) < 1e-12)
        self.assertTrue(abs(max(lmbda["mu_l"] - mpmu_l.flatten())) < 1e-12)
        self.assertTrue(abs(max(lmbda["mu_u"] - mpmu_u.flatten())) < 1e-12)
        self.assertTrue(abs(max(lmbda["lower"] - mpmuLB.flatten())) < 1e-12)
        self.assertTrue(abs(max(lmbda["upper"] - mpmuUB.flatten())) < 1e-12)


    def test_integrate_solution(self):
        """ Test integration of DC OPF solution.
        """
        self.solver.solve()

        bus = mmread(join(DATA_DIR, self.case_name, "opf", "Bus_DC.mtx"))
        gen = mmread(join(DATA_DIR, self.case_name, "opf", "Gen_DC.mtx"))
        branch = mmread(join(DATA_DIR, self.case_name, "opf", "Branch_DC.mtx"))

        pl = 12

        # bus_i type Pd Qd Gs Bs area Vm Va baseKV zone Vmax Vmin lam_P lam_Q mu_Vmax mu_Vmin
        for i, bs in enumerate(self.case.buses):
            self.assertAlmostEqual(bs.v_magnitude, bus[i, 7], pl) # Vm
            self.assertAlmostEqual(bs.v_angle, bus[i, 8], pl) # Va
            self.assertAlmostEqual(bs.p_lmbda, bus[i, 13], pl) # lam_P
            self.assertAlmostEqual(bs.q_lmbda, bus[i, 14], pl) # lam_Q
            self.assertAlmostEqual(bs.mu_vmax, bus[i, 15], pl) # mu_Vmax
            self.assertAlmostEqual(bs.mu_vmin, bus[i, 16], pl) # mu_Vmin

        # bus Pg Qg Qmax Qmin Vg mBase status Pmax Pmin Pc1 Pc2 Qc1min Qc1max
        # Qc2min Qc2max ramp_agc ramp_10 ramp_30 ramp_q apf mu_Pmax mu_Pmin
        # mu_Qmax mu_Qmin
        for i, gn in enumerate(self.case.generators):
            self.assertAlmostEqual(gn.p, gen[i, 1], pl) # Pg
            self.assertAlmostEqual(gn.q, gen[i, 2], pl) # Qg
            self.assertAlmostEqual(gn.v_magnitude, gen[i, 5], pl) # Vg
            self.assertAlmostEqual(gn.mu_pmax, gen[i, 21], pl) # mu_Pmax
            self.assertAlmostEqual(gn.mu_pmin, gen[i, 22], pl) # mu_Pmin
            self.assertAlmostEqual(gn.mu_qmax, gen[i, 23], pl) # mu_Qmax
            self.assertAlmostEqual(gn.mu_qmin, gen[i, 24], pl) # mu_Qmin

        # fbus tbus r x b rateA rateB rateC ratio angle status angmin angmax
        # Pf Qf Pt Qt mu_Sf mu_St mu_angmin mu_angmax
        for i, ln in enumerate(self.case.branches):
            self.assertAlmostEqual(ln.p_from, branch[i, 13], pl) # Pf
            self.assertAlmostEqual(ln.q_from, branch[i, 14], pl) # Qf
            self.assertAlmostEqual(ln.p_to, branch[i, 15], pl) # Pt
            self.assertAlmostEqual(ln.q_to, branch[i, 16], pl) # Qt
            self.assertAlmostEqual(ln.mu_s_from, branch[i, 17], pl) # mu_Sf
            self.assertAlmostEqual(ln.mu_s_to, branch[i, 18], pl) # mu_St
            self.assertAlmostEqual(ln.mu_angmin, branch[i, 19], pl) # mu_angmin
            self.assertAlmostEqual(ln.mu_angmax, branch[i, 20], pl) # mu_angmax

#------------------------------------------------------------------------------
#  "PIPSSolverTest" class:
#------------------------------------------------------------------------------

class PIPSSolverTest(unittest.TestCase):
    """ Defines a test case for the PIPS AC OPF solver.
    """

    def __init__(self, methodName='runTest'):
        super(PIPSSolverTest, self).__init__(methodName)

        self.case_name = "case6ww"
        self.case = None
        self.opf = None
        self.om = None
        self.solver = None


    def setUp(self):
        """ The test runner will execute this method prior to each test.
        """
        self.case = Case.load(join(DATA_DIR, self.case_name, "case.pkl"))
        self.opf = OPF(self.case, dc=False)
        self.om = self.opf._construct_opf_model(self.case)
        self.solver = PIPSSolver(self.om)


    def test_constraints(self):
        """ Test equality and inequality constraints.
        """
        AA, ll, uu = self.solver._linear_constraints(self.om)

        if AA is not None:
            mpA = mmread(join(DATA_DIR, self.case_name, "opf", "A_AC.mtx"))
            mpl = mmread(join(DATA_DIR, self.case_name, "opf", "l_AC.mtx"))
            mpu = mmread(join(DATA_DIR, self.case_name, "opf", "u_AC.mtx"))

            self.assertTrue(mfeq2(AA, mpA.tocsr()))
            self.assertTrue(alltrue(ll == mpl.flatten()))
            self.assertTrue(alltrue(uu == mpu.flatten()))


    def test_var_bounds(self):
        """ Test bounds on optimisation variables.
        """
        _, xmin, xmax = self.solver._var_bounds()

        mpxmin = mmread(join(DATA_DIR, self.case_name, "opf", "xmin_AC.mtx"))
        mpxmax = mmread(join(DATA_DIR, self.case_name, "opf", "xmax_AC.mtx"))

        self.assertTrue(alltrue(xmin == mpxmin.flatten()))
        self.assertTrue(alltrue(xmax == mpxmax.flatten()))


    def test_initial_point(self):
        """ Test selection of an initial interior point.
        """
        b, l, g, _ = self.solver._unpack_model(self.om)
        _, LB, UB = self.solver._var_bounds()
        _, _, _, _, _, ny, _ = self.solver._dimension_data(b, l, g)
        x0 = self.solver._initial_interior_point(b, g, LB, UB, ny)

        mpx0 = mmread(join(DATA_DIR, self.case_name, "opf", "x0_AC.mtx"))

        self.assertTrue(alltrue(x0 == mpx0.flatten()))


    def test_solution(self):
        """ Test AC OPF solution.
        """
        solution = self.solver.solve()
        lmbda = solution["lmbda"]

        f = mmread(join(DATA_DIR, self.case_name, "opf", "f_AC.mtx"))
        x = mmread(join(DATA_DIR, self.case_name, "opf", "x_AC.mtx"))

        # FIXME: Improve accuracy.
        self.assertAlmostEqual(solution["f"], f[0], places=4)
        self.assertTrue(abs(max(solution["x"] - x.flatten())) < 1e-6)

        if len(lmbda["mu_l"]) > 0:
            mu_l = mmread(join(DATA_DIR, self.case_name, "opf", "mu_l_AC.mtx"))
            self.assertTrue(abs(max(lmbda["mu_l"] - mu_l.flatten())) < 1e-12)

        if len(lmbda["mu_u"]) > 0:
            mu_u = mmread(join(DATA_DIR, self.case_name, "opf", "mu_u_AC.mtx"))
            self.assertTrue(abs(max(lmbda["mu_u"] - mu_u.flatten())) < 1e-12)

        if len(lmbda["lower"]) > 0:
            muLB = mmread(join(DATA_DIR, self.case_name, "opf", "muLB_AC.mtx"))
            # FIXME: Improve accuracy.
            self.assertTrue(abs(max(lmbda["lower"] - muLB.flatten())) < 1e-4)

        if len(lmbda["upper"]) > 0:
            muUB = mmread(join(DATA_DIR, self.case_name, "opf", "muUB_AC.mtx"))
            self.assertTrue(abs(max(lmbda["upper"] - muUB.flatten())) < 1e-12)

#        if len(lmbda["nl_mu_l"]) > 0:
#            nl_mu_l = mmread(
#                join(DATA_DIR, self.case_name, "opf", "nl_mu_l.mtx"))
#            self.assertTrue(
#                abs(max(lmbda["nl_mu_l"] - nl_mu_l.flatten())) < 1e-12)
#
#        if len(lmbda["nl_mu_l"]) > 0:
#            nl_mu_u = mmread(
#                join(DATA_DIR, self.case_name, "opf", "nl_mu_u.mtx"))
#            self.assertTrue(
#                abs(max(lmbda["nl_mu_u"] - nl_mu_u.flatten())) < 1e-12)


    def test_integrate_solution(self):
        """ Test integration of AC OPF solution.
        """
        self.solver.solve()

        bus = mmread(join(DATA_DIR, self.case_name, "opf", "Bus_AC.mtx"))
        gen = mmread(join(DATA_DIR, self.case_name, "opf", "Gen_AC.mtx"))
        branch = mmread(join(DATA_DIR, self.case_name, "opf", "Branch_AC.mtx"))

        pl = 6

        # bus_i type Pd Qd Gs Bs area Vm Va baseKV zone Vmax Vmin lam_P lam_Q mu_Vmax mu_Vmin
        for i, bs in enumerate(self.case.buses):
            self.assertAlmostEqual(bs.v_magnitude, bus[i, 7], pl) # Vm
            self.assertAlmostEqual(bs.v_angle, bus[i, 8], pl) # Va
            self.assertAlmostEqual(bs.p_lmbda, bus[i, 13], pl) # lam_P
            self.assertAlmostEqual(bs.q_lmbda, bus[i, 14], pl) # lam_Q
            # FIXME: Improve accuracy
            self.assertAlmostEqual(bs.mu_vmax, bus[i, 15], places=4) # mu_Vmax
            self.assertAlmostEqual(bs.mu_vmin, bus[i, 16], places=4) # mu_Vmin

        # bus Pg Qg Qmax Qmin Vg mBase status Pmax Pmin Pc1 Pc2 Qc1min Qc1max
        # Qc2min Qc2max ramp_agc ramp_10 ramp_30 ramp_q apf mu_Pmax mu_Pmin
        # mu_Qmax mu_Qmin
        for i, gn in enumerate(self.case.generators):
            # FIXME: Improve accuracy
            self.assertAlmostEqual(gn.p, gen[i, 1], places=4) # Pg
            self.assertAlmostEqual(gn.q, gen[i, 2], places=4) # Qg
            self.assertAlmostEqual(gn.v_magnitude, gen[i, 5], pl) # Vg
            self.assertAlmostEqual(gn.mu_pmax, gen[i, 21], pl) # mu_Pmax
            self.assertAlmostEqual(gn.mu_pmin, gen[i, 22], pl) # mu_Pmin
            self.assertAlmostEqual(gn.mu_qmax, gen[i, 23], pl) # mu_Qmax
            self.assertAlmostEqual(gn.mu_qmin, gen[i, 24], pl) # mu_Qmin

        # fbus tbus r x b rateA rateB rateC ratio angle status angmin angmax
        # Pf Qf Pt Qt mu_Sf mu_St mu_angmin mu_angmax
        for i, ln in enumerate(self.case.branches):
            self.assertAlmostEqual(ln.p_from, branch[i, 13], pl) # Pf
            self.assertAlmostEqual(ln.q_from, branch[i, 14], pl) # Qf
            self.assertAlmostEqual(ln.p_to, branch[i, 15], pl) # Pt
            self.assertAlmostEqual(ln.q_to, branch[i, 16], pl) # Qt
            self.assertAlmostEqual(ln.mu_s_from, branch[i, 17], pl) # mu_Sf
            self.assertAlmostEqual(ln.mu_s_to, branch[i, 18], pl) # mu_St
            self.assertAlmostEqual(ln.mu_angmin, branch[i, 19], pl) # mu_angmin
            self.assertAlmostEqual(ln.mu_angmax, branch[i, 20], pl) # mu_angmax


if __name__ == "__main__":
    import logging, sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                        format="%(levelname)s: %(message)s")
    unittest.main()

# EOF -------------------------------------------------------------------------
