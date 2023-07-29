from typing import Callable, Iterable, Never, Self, Any, get_args
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
            if not issubclass(obj, arg):
                return False
        return True
    else:
        return issubclass(obj, typ)


@dataclass
class WrappedFunction:
    wrapped: Callable
    params: list[Parameter]
    env_param: Parameter | None
    var_param: Parameter | None

    def fmt_signature(self):
        fmt_params = list()

        for param in self.params:
            if param == self.env_param:
                continue
            fmt_param = param.annotation.fmt_error()
            
            if param == self.var_param:
                fmt_param += "..."
            fmt_params.append(fmt_param)
        
        return f"[{', '.join(fmt_params)}]"


@dataclass
class _TypeMismatchException(Exception):
    message: str


@dataclass
class StdFunction(Function):
    name: str
    overloads: list[WrappedFunction]

    def overload(self, wraps: Callable) -> Self:
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
        
        self.overloads.append(WrappedFunction(
            wrapped=wraps,
            params=params,
            env_param=env_param,
            var_param=var_param
        ))

        return self


    def call(self, environment: "StdEnvironment", this: Statement, args: list[Statement]) -> Value:
        exceptions: list[tuple[WrappedFunction, str]] = list()

        for overload in self.overloads:
            try:
                cur_idx = 0

                if overload.var_param is None and len(args) != len(overload.params):
                    raise _TypeMismatchException(f"expected {len(overload.params)} parameters, got {len(args)}")
                
                call_params = list()
                
                for param in overload.params:
                    arg = args[cur_idx]
                    cur_idx += 1

                    if overload.env_param == param:
                        call_params.append(environment)
                        continue
                    
                    if overload.var_param == param:
                        continue

                    if param.annotation == Block:
                        block = Block()
                        block.val = arg
                        call_params.append(block)
                    else:
                        val = environment.evaluate(arg)

                        if not check_type(type(val), param.annotation):
                            raise _TypeMismatchException(f"expected {param.annotation.fmt_error()} got {val.fmt_error()}")
                        
                        call_params.append(val)
                
                if overload.var_param:
                    for arg in args[cur_idx:]:
                        val = environment.evaluate(arg)

                        if check_type(type(val), overload.var_param.annotation):
                            raise _TypeMismatchException(f"expected {overload.var_param.annotation.fmt_error()} got {val.fmt_error()}")
                        
                        call_params.append(val)
                
                return overload.wrapped(*call_params)
            except _TypeMismatchException as e:
                exceptions.append((overload, e.message))
        
        raise BMinusRuntimeError.from_statement(this,
            f"no overloads matched:\n" +
            '\n'.join(f"overload {overload.fmt_signature()}: {error}" for overload, error in exceptions)
        )


def function(name: str) -> Callable[[Callable], StdFunction]:
    fn = StdFunction(
        overloads=list(),
        name=name.upper()
    )

    return fn.overload


class StdEnvironmentBuilder(AbstractEnvironmentBuilder):
    functions: dict[str, StdFunction]

    def __init__(self):
        self.functions = dict()
    
    def add_function(self, fn: StdFunction):
        self.functions[fn.name] = fn

        return self
    
    def add_functions(self, fns: Iterable[StdFunction]):
        for fn in fns:
            self.add_function(fn)
        
        return self

    def __call__(self, interpreter: AbstractInterpreter):
        return StdEnvironment(interpreter, self.functions.copy())


@dataclass
class StdEnvironment(AbstractEnvironment):
    interpreter: AbstractInterpreter
    functions: dict[str, Function]
    
    def evaluate(self, statement: Statement) -> Value:
        return self.interpreter.evaluate(statement)

    def resolve_function(self, name: str, name_statement: Statement) -> Function:
        function = self.functions.get(name)

        if function is None:
            raise BMinusRuntimeError.from_statement(name_statement, f"function {name} is not defined")
        
        return function
