import functools


def string_to(to_type, to_be_converted: tuple, convert_all=False):
    """Convert every argument at the to_be_converted position to int."""

    def wrapper(func):
        """Return wrapped."""

        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            """Parse and convert."""
            args = list(args)
            it = to_be_converted if not convert_all else range(to_be_converted[0], len(args))
            for pos in it:
                try:
                    args[pos] = to_type(args[pos])
                except ValueError:
                    raise ValueError(f"Error : Invalid argument for {args[pos]}, it must be a {to_type.__name__}.")
            return await func(*args, **kwargs)

        return wrapped

    return wrapper


def apply_predicate(predicate, to_be_tested, error_desc):
    """Convert every argument at the to_be_converted position to int."""

    def wrapper(func):
        """Return wrapped."""

        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            """Parse and convert."""

            for pos in to_be_tested:
                if not predicate(args[pos]):
                    raise ValueError(f"Error : arg at pos {pos} {error_desc}")
            return await func(*args, **kwargs)

        return wrapped

    return wrapper
