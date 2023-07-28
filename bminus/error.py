from dataclasses import dataclass

@dataclass
class BMinusException(BaseException):
    start: int
    end: int
    message: str