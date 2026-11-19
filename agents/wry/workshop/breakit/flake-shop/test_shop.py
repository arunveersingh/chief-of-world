import datetime
import time
import unittest

import shop


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        time.sleep(0.5)  # stands in for a suite that takes half a second

    def test_total(self):
        self.assertEqual(shop.total([100, 200]), 300)
        self.assertEqual(shop.total([100, 200], 10), 270)

    def test_label(self):
        self.assertEqual(shop.label(1), "1 item")
        self.assertEqual(shop.label(3), "3 items")

    def test_deadline_same_minute(self):
        # written at 10:00:12 and never run near the end of a minute
        self.assertEqual(shop.deadline().minute, datetime.datetime.now().minute)


if __name__ == "__main__":
    unittest.main()
