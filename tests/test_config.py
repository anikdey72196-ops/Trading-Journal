import os
import unittest

def get_debug():
    # This simulates the logic now in app.py
    return os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")

class TestConfig(unittest.TestCase):
    def test_debug_default_off(self):
        if "FLASK_DEBUG" in os.environ:
            del os.environ["FLASK_DEBUG"]
        self.assertFalse(get_debug(), "Debug should be False by default")

    def test_debug_on(self):
        os.environ["FLASK_DEBUG"] = "true"
        self.assertTrue(get_debug(), "Debug should be True when FLASK_DEBUG is 'true'")

        os.environ["FLASK_DEBUG"] = "1"
        self.assertTrue(get_debug(), "Debug should be True when FLASK_DEBUG is '1'")

    def test_debug_off(self):
        os.environ["FLASK_DEBUG"] = "false"
        self.assertFalse(get_debug(), "Debug should be False when FLASK_DEBUG is 'false'")

if __name__ == "__main__":
    unittest.main()
