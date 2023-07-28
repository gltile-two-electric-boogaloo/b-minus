from bminus.std.environment import function, Integer, Float

@function
def add(x: Integer, y: Integer):
    return x.val + y.val