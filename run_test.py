"""
The test function executes the "run" function of a test module from the "test" directory.
Define the test module as input to this modules test function.
E.g. to run test "test_electrolyzer.py", the input for the test function has to be "electrolyzer".
"""
import importlib


def test(test_name):
    test_module = importlib.import_module(".test_" + test_name, "testcase")
    test_module.run()


if __name__ == "__main__":
    test("electrolyzer")



