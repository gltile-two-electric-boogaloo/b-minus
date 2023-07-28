import bminus.parse as parse
import bminus.error as error
import bminus.std.environment as environment
import bminus.evaluate as evaluate
from pprint import pprint

to_parse = """
Hello, world!
[J 10]
"""

@environment.function
def j(n: environment.Integer) -> environment.String:
    string = environment.String()
    string.val = "j" * n.val

    return string

try:
    statements = parse.parse(to_parse)
    environment_builder = environment.StdEnvironmentBuilder()
    environment_builder.add_function("J", j)

    interpreter = evaluate.Interpreter(environment_builder)
    for statement in statements:
        if (ret := interpreter.evaluate(statement)) is not None:
            print(ret.val)
except error.BMinusException as e:
    print(f"{e.message} at {e.start}:{e.end}:\n{to_parse[e.start:e.end]}")