from dataclasses import dataclass
from typing import Never
from bminus.error import BMinusException
from bminus.environment import AbstractInterpreter, AbstractEnvironmentBuilder, AbstractEnvironment, Value, Integer, String, Float
from bminus.parse import Statement, Function, Literal, LiteralInt, LiteralString, LiteralFloat

class BMinusRuntimeError(BMinusException):
    @classmethod
    def from_statement(cls, statement: Statement, message: str):
        return cls(
            start=statement.start,
            end=statement.end,
            message=message
        )


class Interpreter(AbstractInterpreter):
    environment: AbstractEnvironment

    def __init__(self, environment_builder: AbstractEnvironmentBuilder):
        self.environment = environment_builder(self)
    
    def evaluate(self, statement: Statement) -> Value:
        if isinstance(statement, Literal):
            if type(statement) is LiteralInt:
                val = Integer()
            elif type(statement) is LiteralString:
                val = String()
            elif type(statement) is LiteralFloat:
                val = Float()

            val.val = statement.value
            return val
        elif isinstance(statement, Function):
            try:
                function = self.environment.resolve_function(statement.ident.value.upper(), statement)
                return function.call(self.environment, statement, statement.params)
            except BMinusException as e:
                raise e
            except BaseException as e:
                raise BMinusRuntimeError.from_statement(statement, f"INTERPRETER ERROR: Uncaught exception {e}")
        raise Exception