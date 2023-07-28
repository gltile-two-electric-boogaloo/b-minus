from dataclasses import dataclass
from typing import Never
from bminus.error import BMinusException
from bminus.environment import AbstractInterpreter, AbstractEnvironmentBuilder, AbstractEnvironment, Value, Integer, String
from bminus.parse import Statement, Function, Literal, LiteralInt, LiteralString

class BMinusRuntimeError(BMinusException):
    pass


@dataclass
class _BMinusRuntimeError(BaseException):
    message: str


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

            val.val = statement.value
            return val
        elif isinstance(statement, Function):
            try:
                function = self.environment.resolve_function(statement.ident.value)
                return function.call(self.environment, statement, statement.params)
            except _BMinusRuntimeError as e:
                raise BMinusRuntimeError(
                    start=statement.start,
                    end=statement.end,
                    message=e.message
                )
            except BaseException as e:
                raise BMinusRuntimeError(
                    start=statement.start,
                    end=statement.end,
                    message=f"INTERPRETER ERROR: Uncaught exception {e}"
                )
        raise Exception
    
    def raise_exception(self, message: str) -> Never:
        raise _BMinusRuntimeError(message)