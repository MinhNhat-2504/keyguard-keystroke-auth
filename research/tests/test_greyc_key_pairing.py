import unittest
from scripts.greyc_key_pairing import pair_keys,parse


class PairingTests(unittest.TestCase):
    def test_regular_repeated_nonoverlapping_key(self):
        r=pair_keys('83 0\n69 20\n83 40','83 10\n69 30\n83 50')
        self.assertEqual(r['status'],'resolved');self.assertEqual([p['hold'] for p in r['pairs']],[10,10,10])

    def test_different_keys_release_out_of_press_order(self):
        r=pair_keys('65 0\n66 10','66 20\n65 30')
        self.assertEqual(r['status'],'resolved')
        self.assertEqual([p['release_index'] for p in r['pairs']],[1,0])

    def test_modifier_down_without_up_is_separate(self):
        r=pair_keys('16 0\n83 1','83 5')
        self.assertEqual(r['status'],'resolved');self.assertEqual(len(r['ignored_modifiers']),1)
        self.assertEqual(r['pairs'][0]['hold'],4)

    def test_unknown_255_is_not_silently_modifier(self):
        r=pair_keys('255 0\n83 1','83 5')
        self.assertEqual(r['status'],'unresolved');self.assertEqual(r['issues'][0]['code'],'255')

    def test_overlapping_same_key_has_multiple_solutions(self):
        r=pair_keys('83 0\n83 1','83 2\n83 3')
        self.assertEqual(r['issues'][0]['reason'],'ambiguous')

    def test_release_before_press(self):
        r=pair_keys('83 2','83 1')
        self.assertEqual(r['status'],'unresolved')

    def test_zero_hold_time_tie_allowed(self):
        self.assertEqual(pair_keys('83 1','83 1')['pairs'][0]['hold'],0)

    def test_missing_or_extra_release(self):
        for d,u in [('83 1',''),('','83 1')]:self.assertEqual(pair_keys(d,u)['status'],'unresolved')

    def test_bad_schema_nonfinite_and_unsorted(self):
        for text in ['83 nan','83 1 2','xx 1','83 2\n69 1']:
            with self.assertRaises(ValueError):parse(text)

    def test_no_mutation_of_raw_strings(self):
        d,u='83 0\n','83 10\n';before=(d,u)
        pair_keys(d,u);self.assertEqual((d,u),before)


if __name__=='__main__':unittest.main()
