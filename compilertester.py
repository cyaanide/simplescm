from interpreter import Interpreter

class InterpreterTester():
    def test_token_production(self):

        def pretty_print_test_case(data, tokens):
            pretty_print_code = False
            func = str if pretty_print_code else repr
            return "Tokenization fail\ncode:\n" + func(data["code"]) + "\n" + "expected: " + str(data["result"]) + "\n" + "actual:   " + str(tokens) + "\n"

        test_data = [
            {"code":"khilan\n9999\n", "result":["khilan", 9999.0]},
            {"code":"khilan\n9999 ", "result":["khilan", 9999.0]},
            {"code":"khilan\n9999", "result":["khilan", 9999.0]},
            {"code":"9999\nkhilan\n", "result":[9999.0, "khilan"]},
            {"code":"9999\nkhilan ", "result":[9999.0, "khilan"]},
            {"code":"9999\nkhilan", "result":[9999.0, "khilan"]},
            {"code":"9999\nkhilan\n\"string\"\n", "result":[9999.0, "khilan", '"string"']},
            {"code":"9999\nkhilan\n\"string\" ", "result":[9999.0, "khilan", '"string"']},
            {"code":"9999\nkhilan\n\"string\"", "result":[9999.0, "khilan", '"string"']},
            {"code":"9999\nkhilan\n\"string\"\n'(1 2 3)\n", "result":[9999.0, "khilan", '"string"', "'(1 2 3)"]},
            {"code":"'((1 2 3) 4 5)", "result":["'((1 2 3) 4 5)"]},
        ]

        for data in test_data:
            interpreter = Interpreter(data["code"])
            tokens = interpreter.produce_tokens()
            assert tokens == data["result"], pretty_print_test_case(data, tokens) 

if __name__ == "__main__":
    tester = InterpreterTester()
    tester.test_token_production()