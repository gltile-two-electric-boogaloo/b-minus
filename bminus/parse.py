import io
from dataclasses import dataclass
from textwrap import wrap

from bminus.error import BMinusException


class BMinusSyntaxError(BMinusException):
    pass


class Statement:
    start: int
    end: int

    def __repr__(self):
        ret = f"{self.__class__.__name__}(\n"
        
        for k, v in self.__dict__.items():
            reprs: list[str] = []

            for line in repr(v).splitlines():
                reprs.append(f"    {line}")
            
            reprs[0] = reprs[0].strip()
            formatted_repr = '\n'.join(reprs)

            ret += f"    {k}={formatted_repr},\n"
        
        return f"{ret})"
    
    def fmt_err(self):
        return "statement"


class Literal(Statement):
    pass


class LiteralString(Literal):
    value: str

    def fmt_err(self):
        return f"literal string \"{self.value}\""


class LiteralInt(Literal):
    value: int

    def fmt_err(self):
        return f"literal int {self.value}"


class Function(Statement):
    ident: LiteralString
    params: list[Statement]

    def fmt_err(self):
        return "function call"


def read_until(input: io.TextIOBase, chars: [str]) -> (str, str):
    """
    :return: tuple of (text that was read, character in chars that matched)
    """

    ret = ""

    while (c := input.read(1)) not in chars and c != "":
        ret += c
    else:
        input.seek(input.tell() - 1, io.SEEK_SET)
        return (ret, c)


def peek(input: io.TextIOBase, n: int | None = None) -> str:
    initial_cur = input.tell()
    ret = input.read(n)
    input.seek(initial_cur, io.SEEK_SET)

    return ret


def read_statement(input: io.TextIOBase, top_level=False) -> Statement:
    c = " "
    while c.isspace():
        initial_pos = input.tell()
        c = input.read(1)

    match c:
        case "[": 
            params: list[Statement] = list()
            node = Function()

            while True:
                c = peek(input, 1)

                match c:
                    case "]":
                        input.read(1)

                        params = [
                            x for x in params if (type(x) is not LiteralString or x.value != "")
                        ]

                        try:
                            if type(params[0]) is not LiteralString:
                                raise BMinusSyntaxError(
                                    start=params[0].start,
                                    end=params[0].end,
                                    message=f"Expected literal string, got {params[0].fmt_err()}"                          
                                )
                        except IndexError:
                            raise BMinusSyntaxError(
                                start=initial_pos,
                                end=input.tell(),
                                message=f"Expected literal string, got nothing"
                            )

                        node.start = initial_pos
                        node.end = input.tell()
                        node.ident = params.pop(0)
                        node.params = params

                        return node
                    case "":
                        raise BMinusSyntaxError(
                            start=input.tell(),
                            end=input.tell(),
                            message=f"Unexpected eof"
                        )
                    case _:
                        params.append(read_statement(input))
        case "":
            raise BMinusSyntaxError(
                start=input.tell(),
                end=input.tell(),
                message=f"Unexpected eof"
            )
        case _:
            if top_level:
                (read, _) = read_until(input, ["["])

                node = LiteralString()
                node.value = (c + read).strip()
                return node

            if c == "\"":
                (read, _) = read_until(input, ["\""])

                node = LiteralString()
                node.value = c + read
            elif c.isnumeric() and c.isascii():
                (read, _) = read_until(input, [" ", "\n", "[", "]"])

                node = LiteralInt()

                try:
                    node.value = int(c + read)
                except ValueError:
                    raise BMinusSyntaxError(
                        start=initial_pos,
                        end=input.tell(),
                        message=f"Expected literal int, got \"{c + read}\""
                    )
            else:
                (read, _) = read_until(input, [" ", "\n" "[", "]"])
                
                node = LiteralString()
                node.value = c + read
            
            node.start = initial_pos
            node.end = input.tell()

            return node


def parse(input: str) -> list[Statement]:
    buf = io.StringIO(input)
    statements: list[Statement] = []

    while True:
        statements.append(read_statement(buf, top_level=True))

        while (c := peek(buf, 1)).isspace():
            buf.read(1)
        
        if c == "":
            return statements