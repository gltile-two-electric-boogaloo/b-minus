import typing
from bminus.parse import LiteralString
from enum import Enum


class Statement:
    start: int
    end: int


class Value:
    _error_name = "value"
    val: any

    def __init__(self, val=None):
        self.val = val

    @classmethod
    def fmt_error(self):
        return self._error_name


T = typing.TypeVar('T', bound=Value)


class Integer(Value):
    _error_name = "integer"
    val: int


class Float(Value):
    _error_name = "float"
    val: float


class Array(Value, typing.Generic[T]):
    inner: type[T]
    val: list[T]

    @classmethod
    def fmt_error(self):
        return f"array of {self.inner.fmt_error()}"


class String(Array[str]):
    inner: str
    val: str
    
    @classmethod
    def fmt_error(self):
        return "string"


Any = Integer | Float | String


class Function(typing.Protocol):
    def call(self, environment: "AbstractEnvironment", this: Statement, args: list[Statement]) -> Value | None: ...


class AbstractInterpreter(typing.Protocol):
    def evaluate(self, statement: Statement) -> Value | None: ...
    def raise_exception(self, message: str) -> typing.Never: ...


class AbstractEnvironment(typing.Protocol):
    def resolve_function(self, name: str) -> Function: ...


class AbstractEnvironmentBuilder(typing.Protocol):
    def __call__(interpreter: AbstractInterpreter) -> AbstractEnvironment: ...