import unittest
from unittest.mock import patch
import numpy as np
from scripts import covariance_control_core as core
from keyguard.detectors import ScaledManhattan


class CovarianceTests(unittest.TestCase):
    def setUp(self):self.x=np.random.default_rng(71).normal(size=(20,21))

    def test_same_center_scale_diagonal_and_positive_eigenvalues(self):
        s=core.fit_metrics(self.x)
        np.testing.assert_allclose(np.diag(s['full_covariance']),np.diag(s['diagonal_covariance']))
        self.assertGreater(np.linalg.eigvalsh(s['full_covariance']).min(),0)

    def test_quadratic_formula(self):
        x=np.array([[1.,2.],[2.,-1.]])
        p=np.array([[2.,.5],[.5,1.]])
        np.testing.assert_allclose(core.quadratic_score(x,p),[np.sqrt(r@p@r) for r in x])

    def test_identity_covariance_diagonal_full_same(self):
        s=core.fit_metrics(self.x)
        s['full_precision']=s['diagonal_precision'].copy()
        np.testing.assert_allclose(core.score(s,self.x,'full_lw'),core.score(s,self.x,'diag_lw'))

    def test_constant_and_duplicate_columns_finite(self):
        for x in [np.ones((20,21)),np.repeat(self.x[:,:1],30,axis=1)]:
            profile=core.profiles(x)
            for a in core.ARMS:self.assertTrue(np.isfinite(core.z_scores(profile,x,a)).all())

    def test_manhattan_parity(self):
        s=core.fit_metrics(self.x)
        np.testing.assert_allclose(core.score(s,self.x,'scaled_manhattan'),ScaledManhattan().fit(self.x).score(self.x))

    def test_oof_only_fits_training_16_then_full20(self):
        seen=[];original=core.fit_metrics
        def traced(rows):seen.append(rows.copy());return original(rows)
        with patch.object(core,'fit_metrics',side_effect=traced):profile=core.profiles(self.x)
        self.assertEqual([len(x) for x in seen],[16,16,16,16,16,20])
        for i in range(5):np.testing.assert_array_equal(seen[i],np.delete(self.x,np.arange(4*i,4*i+4),axis=0))
        for a in core.ARMS:self.assertAlmostEqual(profile[1][a]['mean'],profile[2][a].mean())

    def test_no_mutation_and_affine_positive_feature_scaling(self):
        before=self.x.copy();s=core.fit_metrics(self.x)
        np.testing.assert_array_equal(self.x,before)
        transformed=self.x*np.arange(1,22)+5
        other=core.fit_metrics(transformed)
        for a in core.ARMS:np.testing.assert_allclose(core.score(s,self.x,a),core.score(other,transformed,a),rtol=1e-8)

    def test_invalid_inputs(self):
        for x in [np.ones(20),np.ones((1,21)),np.full((20,21),np.nan)]:
            with self.assertRaises(ValueError):core.fit_metrics(x)
        with self.assertRaises(ValueError):core.profiles(self.x[:19])
        with self.assertRaises(ValueError):core.score(core.fit_metrics(self.x),np.ones((2,3)),'full_lw')
        with self.assertRaises(ValueError):core.score(core.fit_metrics(self.x),self.x,'other')

    def test_dev_partition_rejects_original_test_and_duplicate(self):
        from scripts.run_covariance_control import partition
        cal,evaluation=partition(['a','b','c','d','e','f'],['test'])
        self.assertEqual(cal,['a','b','d','e']);self.assertEqual(evaluation,['c','f'])
        with self.assertRaises(ValueError):partition(['a','test'],['test'])
        with self.assertRaises(ValueError):partition(['a','a'],[])


if __name__=='__main__':unittest.main()
