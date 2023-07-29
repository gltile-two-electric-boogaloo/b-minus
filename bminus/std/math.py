from bminus.std.environment import function, Integer, Float

@function("add")
def add(x: Integer | Float, y: Integer | Float):
    v = x.val + y.val

    if type(v) is int:
        return Integer(v)
    elif type(v) is float:
        return Float(v)


math = [add]