import unittest

from app import ValidationUtils


class ValidationUtilsTests(unittest.TestCase):
    def test_get_level_from_duration_accepts_numeric_strings(self):
        self.assertEqual(ValidationUtils.get_level_from_duration("2.5"), ("Level 1", 1))
        self.assertEqual(ValidationUtils.get_level_from_duration("5"), ("Level 2", 2))

    def test_get_level_from_duration_handles_blank_or_invalid_values(self):
        self.assertEqual(ValidationUtils.get_level_from_duration(""), ("Level 1", 1))
        self.assertEqual(ValidationUtils.get_level_from_duration(None), ("Level 1", 1))
        self.assertEqual(ValidationUtils.get_level_from_duration("abc"), ("Level 1", 1))


if __name__ == "__main__":
    unittest.main()
