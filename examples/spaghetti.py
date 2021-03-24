def good(num, name=None):
    b = bad(num)
    u = ugly(name)
    return f"The GOOD({num}, name={name}), The BAD->{b}, and The UGLY->{u}"


def bad(num):
    u = ugly(num)
    return f"The BAD({num}) got UGLY->{u}"


def ugly(num):
    return 42 / num
