import functools


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(*new_args)
                except Exception as e:
                    e.args = e.args + ('Test case: %s has been failed' % str(c),)
                    raise

        return wrapper

    return decorator
