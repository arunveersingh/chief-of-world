import datetime
import time
import unittest
import shop


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        time.sleep(0.5)  # stands in for a half-second test suite

    def test_total_plain(self):
        self.assertEqual(shop.total([100, 200]), 300)

    def test_deadline_same_minute(self):
        self.assertEqual(shop.deadline().minute, datetime.datetime.now().minute)


if __name__ == "__main__":
    unittest.main()
