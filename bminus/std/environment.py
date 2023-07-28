from typing import Callable, Concatenate, Never, Any, get_args
from types import UnionType
from inspect import Parameter, signature
from dataclasses import dataclass
from bminus.parse import LiteralString
from bminus.environment import AbstractEnvironment, AbstractEnvironmentBuilder, AbstractInterpreter, Function, Value, Integer, Float, Array, String, Statement
from bminus.evaluate import BMinusRuntimeError


class Block(Value):
    val: Statement


def check_type(obj: type, typ: UnionType | type[Value]) -> bool:
    if isinstance(typ, UnionType):
        for arg in get_args(typ):
            if issubclass(obj, arg):
                return True
        return False
    else:
        return issubclass(obj, typ)


def check_type_superclass(obj: UnionType | Any, typ: type[Value]) -> bool:
    if isinstance(obj, UnionType):
        for arg in get_args(typ):
            if issubclass(obj, arg):
                return True
        return False
    else:
        return issubclass(obj, typ)


@dataclass
class StdFunction(Function):
    wrapped: Callable
    params: list[Parameter]
    env_param: Parameter | None
    var_param: Parameter | None

    def call(self, environment: "StdEnvironment", this: Statement, args: list[Statement]) -> Value:
        if self.var_param is None and len(args) != len(self.params):
            environment.raise_exception(f"expected {len(self.params)} parameters, got {len(args)}")
        
        call_params = list()
        
        for param in self.params:
            arg = args.pop(0)

            if self.env_param == param:
                call_params.append(environment)
                continue
            
            if self.var_param == param:
                continue

            if param.annotation == Block:
                block = Block()
                block.val = arg
                call_params.append(block)
            else:
                val = environment.evaluate(arg)

                if not check_type(type(val), param.annotation):
                    environment.raise_exception(f"expected {param.annotation.fmt_error()} got {val.fmt_error()}")
                
                call_params.append(val)
        
        if self.var_param:
            for arg in args:
                val = environment.evaluate(arg)

                if check_type(type(val), self.var_param.annotation):
                    environment.raise_exception(f"expected {self.var_param.annotation.fmt_error()} got {val.fmt_error()}")
                
                call_params.append(val)
        
        return self.wrapped(*call_params)


def function(wraps: Callable) -> StdFunction:
    sig = signature(wraps, eval_str=True)
    params = list(sig.parameters.values())
    env_param: Parameter | None = None
    var_param: Parameter | None = None

    for param in params:
        if param.kind not in [Parameter.POSITIONAL_OR_KEYWORD, Parameter.VAR_KEYWORD, Parameter.POSITIONAL_ONLY]:
            raise ValueError(f"invalid parameter type {param.kind}")
        
        if check_type_superclass(param.annotation, Value):
            if param.kind == Parameter.VAR_POSITIONAL:
                var_param = param
            
            continue

        if param.annotation is StdEnvironment and env_param is None:
            env_param = param
            continue

        raise ValueError(f"invalid annotation {param.annotation} on {param.name}")
    
    if isinstance(sig.return_annotation, UnionType):
        types = get_args(sig.return_annotation)
    else:
        types = [sig.return_annotation]

    for arg in types:
        if not (arg is Parameter.empty or issubclass(arg, Value)):
            raise ValueError(f"invalid return annotation {arg}")
    
    return StdFunction(
        wrapped=wraps,
        params=list(params),
        env_param=env_param,
        var_param=var_param
    )


class StdEnvironmentBuilder(AbstractEnvironmentBuilder):
    functions: dict[str, StdFunction]

    def __init__(self):
        self.functions = dict()
    
    def add_function(self, name: str, fn: Function):
        self.functions[name] = fn

    def __call__(self, interpreter: AbstractInterpreter):
        return StdEnvironment(interpreter, self.functions)


@dataclass
class StdEnvironment(AbstractEnvironment):
    interpreter: AbstractInterpreter
    functions: dict[str, Function]

    def raise_exception(self, message: str) -> Never:
        self.interpreter.raise_exception(message)
    
    def evaluate(self, statement: Statement) -> Value:
        return self.interpreter.evaluate(statement)

    def resolve_function(self, name: str) -> Function:
        function = self.functions.get(name)

        if function is None:
            self.raise_exception(f"function {name} is not defined")
        
        return function
