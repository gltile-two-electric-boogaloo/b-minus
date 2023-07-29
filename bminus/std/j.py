from bminus.std.environment import function, Integer, String

@function("j")
def j(j: Integer):
    return String("j" * j.val)