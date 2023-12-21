
from langchain_community.chat_models import ChatOpenAI
from langchain.llms import OpenAI
import unittest
import os

#custom imports
from Lang2Logic.generator import Generator


"""



class TestGenerator(unittest.TestCase):
    def setUp(self):
        api_key = "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"
        self.test_gen = Generator(api_key)

    def test_generate_integers(self):
        schema = self.test_gen.generate("return a list of the integers 1-5")
        expected = [1, 2, 3, 4, 5]  # Define the expected output
        self.assertEqual(schema, expected, "The generated list does not match the expected list.")

    # If there's any teardown needed (usually not necessary for simple cases)
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
"""