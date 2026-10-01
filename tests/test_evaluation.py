import math
import unittest
from maidionis_education.evaluation import percentile,rate
class StatisticalAccounting(unittest.TestCase):
    def test_zero_support_and_imbalance_keep_actual_denominators(self):
        empty=rate('empty',0,0);self.assertIsNone(empty['value']);self.assertEqual(empty['warning'],'zero_support')
        imbalanced=rate('majority',9,10);self.assertEqual(imbalanced['value'],.9);self.assertEqual(imbalanced['support'],10)
        with self.assertRaises(ValueError):rate('bad',2,1)
    def test_registered_percentile_and_nonfinite_rejection(self):
        self.assertIsNone(percentile([],.5));self.assertEqual(percentile([30,0,20,10],.25),7.5)
        for x in ([math.nan],[math.inf]):
            with self.assertRaises(ValueError):percentile(x,.5)
if __name__=='__main__':unittest.main()
