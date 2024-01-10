import os
from Lang2Logic.generator import Generator


class Lang2LogicTests:

    def __init__(self):
        self.test_gen = Generator(
            "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")

    def run_tests(self):
        self.test_basic_list_generation()
        self.test_dictionary_generation()
        self.test_nested_structure_generation()
        self.test_automatic_schema_generation()
        self.test_decision_classifying()
        self.test_custom_schema_use()
        self.test_error_handling()

    def test_basic_list_generation(self):
        prompt = "return a list of numbers from 1 to 5"
        output = self.test_gen.generate(prompt)
        print(
            f"Test Basic List Generation\nPrompt: {prompt}\nOutput: {output}")

    def test_dictionary_generation(self):
        prompt = "return a dictionary with keys 'name' and 'age'"
        output = self.test_gen.generate(prompt)
        print(
            f"Test Dictionary Generation\nPrompt: {prompt}\nOutput: {output}")

    def test_nested_structure_generation(self):
        prompt = "return a list of dictionaries, each having 'color' and 'code'"
        output = self.test_gen.generate(prompt)
        print(
            f"Test Nested Structure Generation\nPrompt: {prompt}\nOutput: {output}"
        )

    def test_automatic_schema_generation(self):
        prompt = "return a list of strings with 3 fruits"
        output = self.test_gen.generate(prompt)
        print(
            f"Test Automatic Schema Generation\nPrompt: {prompt}\nOutput: {output}"
        )

    def test_decision_classifying(self):
        # Sample user data
        users_data_json = {
            "bios": [{
                "bio": "Enjoys mountaineering and hiking"
            }, {
                "bio": "Prefers programming and video games"
            }]
        }

        prompt = "classify if a user is interested in outdoor activities"
        for user in users_data_json["bios"]:
            output = self.test_gen.generate(
                f"{prompt}\nUser Bio:\n{user['bio']}")
            print(
                f"Test Decision Classifying\nPrompt: {prompt}\nUser Bio: {user['bio']}\nOutput: {output}"
            )

    def test_custom_schema_use(self):
        prompt = "generate a schedule schema for weekly activities"
        schema = self.test_gen.generate_schema(prompt)
        output = self.test_gen.generate("list activities for Monday", schema)
        print(f"Test Custom Schema Use\nPrompt: {prompt}\nOutput: {output}")

    def test_error_handling(self):
        prompt = "generate a blueprint for a time machine"
        output = self.test_gen.generate(prompt)
        print(f"Test Error Handling\nPrompt: {prompt}\nOutput: {output}")


if __name__ == "__main__":
    tests = Lang2LogicTests()
    tests.run_tests()
