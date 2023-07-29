import bminus.parse as parse
import bminus.error as error
import bminus.std.math as math
import bminus.std.j as j
import bminus.std.environment as environment
import bminus.evaluate as evaluate

to_parse = """
"hellooo!!
[ADD 1 2]
"""


@environment.function("debug")
def debug(x: environment.Integer) -> environment.String:
    return environment.String(f"Integer {x.val}")


@debug.overload
def debug(x: environment.String) -> environment.String:
    return environment.String(f"String \"{x.val}\"")


try:
    statements = parse.parse(to_parse)
    environment_builder = (environment.StdEnvironmentBuilder()
        .add_functions(math.math)
        .add_function(j.j)
        .add_function(debug))

    interpreter = evaluate.Interpreter(environment_builder)
    for statement in statements:
        if (ret := interpreter.evaluate(statement)) is not None:
            print(ret.val)
except error.BMinusException as e:
    print(f"{e.message} at {e.start}:{e.end}:\n{to_parse[e.start:e.end]}")