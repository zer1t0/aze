import sys

def read_text_targets(
    targets,
    use_stdin_if_none=True,
    use_stdin_if_minus=True,
    try_read_file=True,
    strip=True,
    remove_comments=True,
    remove_empty=True,
):
    yield from _read_text_lines(
        _read_targets(
            targets,
            use_stdin_if_none=use_stdin_if_none,
            use_stdin_if_minus=use_stdin_if_minus,
            try_read_file=try_read_file,
        ),
        strip_lines=strip,
        remove_comments=remove_comments,
        remove_empty=remove_empty,
    )

def _read_targets(
        targets, use_stdin_if_none, use_stdin_if_minus, try_read_file
):
    """Function to process the program ouput that allows to read an array
    of strings or lines of a file in a standard way. In case nothing is
    provided, input will be taken from stdin.
    """
    if not targets:
        if use_stdin_if_none:
            yield from sys.stdin
        else:
            return

    for target in targets:
        if try_read_file:
            try:
                with open(target) as fi:
                    yield from fi
                continue
            except FileNotFoundError:
                pass

        if target == "-" and use_stdin_if_minus:
            yield from sys.stdin
        else:
            yield target


def _read_text_lines(fd, strip_lines, remove_comments, remove_empty):
    """To read lines from a file and skip empty lines or those commented
    (starting by #)
    """
    for line in fd:
        if strip_lines:
            line = line.strip()
        if remove_empty and line == "":
            continue
        if remove_comments and line.startswith("#"):
            continue

        yield line
