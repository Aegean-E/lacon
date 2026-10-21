"""Code understanding tests: Python source becomes meaningful sentences."""

import unittest

from lacon.code_understanding import (
    code_to_sentences,
    extract_code_elements,
    is_code_context,
)

SOURCE = '''import os
from typing import List


class DataProcessor:
    """Process data."""

    def process(self, values: List[int]) -> int:
        return sum(values)


def process_data(data: list[str], flag: bool = False) -> str:
    """Process a list of strings."""
    return " ".join(data)
'''


class ExtractTests(unittest.TestCase):
    """The AST reader finds the elements a question can ask about."""

    def test_functions_classes_and_imports_are_found(self) -> None:
        kinds = {(element.kind, element.name) for element in extract_code_elements(SOURCE)}
        self.assertIn(("function", "process_data"), kinds)
        self.assertIn(("function", "process"), kinds)
        self.assertIn(("class", "DataProcessor"), kinds)
        self.assertIn(("import", "os"), kinds)
        self.assertIn(("import", "List"), kinds)

    def test_a_function_carries_its_signature_and_docstring(self) -> None:
        element = next(e for e in extract_code_elements(SOURCE)
                       if e.name == "process_data")
        self.assertEqual(element.kind, "function")
        self.assertIn("process_data", element.signature)
        self.assertIn("data", element.signature)
        self.assertEqual(element.docstring, "Process a list of strings.")

    def test_a_syntax_error_yields_no_elements(self) -> None:
        self.assertEqual(extract_code_elements("def broken("), [])

    def test_code_to_sentences_labels_each_kind(self) -> None:
        rendered = code_to_sentences(SOURCE)
        self.assertTrue(any(line.startswith("Function") for line in rendered))
        self.assertTrue(any(line.startswith("Class") for line in rendered))
        self.assertTrue(any(line.startswith("Import") for line in rendered))


class DetectionTests(unittest.TestCase):
    """Code is recognized by strong line-leading markers, not by prose."""

    def test_python_source_is_code(self) -> None:
        self.assertTrue(is_code_context(SOURCE))

    def test_natural_language_is_not_code(self) -> None:
        self.assertFalse(is_code_context("Paint keeps the bridge from rust."))

    def test_an_indented_definition_is_still_code(self) -> None:
        self.assertTrue(is_code_context("    def nested():\n        pass"))


if __name__ == "__main__":
    unittest.main()
