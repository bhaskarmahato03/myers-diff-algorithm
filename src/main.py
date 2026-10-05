import sys


def read_lines(path: str) -> list[bytes]:
    with open(path, "rb") as file:
        data = file.read()

    if data == b"":
        return []

    lines = data.split(b"\n")

    if lines[-1] == b"":
        lines.pop()

    return lines


def myers_diff(a: list[bytes], b: list[bytes]) -> list[tuple[str, bytes]]:
    n = len(a)
    m = len(b)

    v = {1: 0}
    trace = []
    distance = 0

    # Find shortest edit path
    for d in range(n + m + 1):
        trace.append(v.copy())

        for k in range(-d, d + 1, 2):

            if k == -d or (
                k != d and v.get(k - 1, -1) < v.get(k + 1, -1)
            ):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1

            y = x - k

            # Snake
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x

            if x >= n and y >= m:
                distance = d
                break
        else:
            continue

        break

    # Reconstruct the path
    x = n
    y = m
    reversed_ops = []

    for d in range(distance, 0, -1):
        previous_v = trace[d]
        k = x - y

        if k == -d or (
            k != d
            and previous_v.get(k - 1, -1)
            < previous_v.get(k + 1, -1)
        ):
            previous_k = k + 1
        else:
            previous_k = k - 1

        previous_x = previous_v.get(previous_k, 0)
        previous_y = previous_x - previous_k

        # Matching part
        while x > previous_x and y > previous_y:
            reversed_ops.append((" ", a[x - 1]))
            x -= 1
            y -= 1

        # Edit
        if x == previous_x:
            reversed_ops.append(("+", b[y - 1]))
            y -= 1
        else:
            reversed_ops.append(("-", a[x - 1]))
            x -= 1

    # Remaining matching prefix
    while x > 0 and y > 0:
        reversed_ops.append((" ", a[x - 1]))
        x -= 1
        y -= 1

    while x > 0:
        reversed_ops.append(("-", a[x - 1]))
        x -= 1

    while y > 0:
        reversed_ops.append(("+", b[y - 1]))
        y -= 1

    reversed_ops.reverse()

    # Deletions must come before insertions
    # inside every change block.
    result = []
    deletions = []
    insertions = []

    def flush_changes():
        for line in deletions:
            result.append(("-", line))

        for line in insertions:
            result.append(("+", line))

        deletions.clear()
        insertions.clear()

    for op, line in reversed_ops:

        if op == "-":
            deletions.append(line)

        elif op == "+":
            insertions.append(line)

        else:
            flush_changes()
            result.append((" ", line))

    flush_changes()

    return result


def myers_generic(a, b):
    """
    Myers diff for any sequence.

    Returns:
        " " = keep
        "-" = delete
        "+" = insert
    """

    n = len(a)
    m = len(b)

    v = {1: 0}
    trace = []
    distance = 0

    # Find shortest edit path
    for d in range(n + m + 1):
        trace.append(v.copy())

        for k in range(-d, d + 1, 2):

            if k == -d or (
                k != d and v.get(k - 1, -1) < v.get(k + 1, -1)
            ):
                x = v.get(k + 1, 0)
            else:
                x = v.get(k - 1, 0) + 1

            y = x - k

            # Snake
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1

            v[k] = x

            if x >= n and y >= m:
                distance = d
                break
        else:
            continue

        break

    # Reconstruct
    x = n
    y = m
    reversed_ops = []

    for d in range(distance, 0, -1):
        previous_v = trace[d]
        k = x - y

        if k == -d or (
            k != d
            and previous_v.get(k - 1, -1)
            < previous_v.get(k + 1, -1)
        ):
            previous_k = k + 1
        else:
            previous_k = k - 1

        previous_x = previous_v.get(previous_k, 0)
        previous_y = previous_x - previous_k

        while x > previous_x and y > previous_y:
            reversed_ops.append((" ", a[x - 1]))
            x -= 1
            y -= 1

        if x == previous_x:
            reversed_ops.append(("+", b[y - 1]))
            y -= 1
        else:
            reversed_ops.append(("-", a[x - 1]))
            x -= 1

    while x > 0 and y > 0:
        reversed_ops.append((" ", a[x - 1]))
        x -= 1
        y -= 1

    while x > 0:
        reversed_ops.append(("-", a[x - 1]))
        x -= 1

    while y > 0:
        reversed_ops.append(("+", b[y - 1]))
        y -= 1

    reversed_ops.reverse()

    return reversed_ops


def merge_ranges(
    ranges: list[tuple[int, int]]
) -> list[tuple[int, int]]:

    if not ranges:
        return []

    ranges.sort()

    merged = [ranges[0]]

    for start, end in ranges[1:]:
        old_start, old_end = merged[-1]

        # Merge overlapping or touching ranges.
        if start <= old_end:
            merged[-1] = (
                old_start,
                max(old_end, end)
            )
        else:
            merged.append((start, end))

    return merged


def character_ranges(
    old: bytes,
    new: bytes
) -> tuple[
    list[tuple[int, int]],
    list[tuple[int, int]]
]:

    old_chars = list(old.decode("utf-8"))
    new_chars = list(new.decode("utf-8"))

    operations = myers_generic(
        old_chars,
        new_chars
    )

    old_ranges = []
    new_ranges = []

    old_pos = 0
    new_pos = 0

    for op, char in operations:

        if op == " ":
            old_pos += 1
            new_pos += 1

        elif op == "-":
            old_ranges.append(
                (old_pos, old_pos + 1)
            )
            old_pos += 1

        elif op == "+":
            new_ranges.append(
                (new_pos, new_pos + 1)
            )
            new_pos += 1

    return (
        merge_ranges(old_ranges),
        merge_ranges(new_ranges)
    )


def format_ranges(
    ranges: list[tuple[int, int]]
) -> str:

    if not ranges:
        return "."

    return ",".join(
        f"{start}-{end}"
        for start, end in ranges
    )


def print_lines_diff(operations):
    for op, line in operations:
        sys.stdout.buffer.write(
            op.encode("ascii")
            + line
            + b"\n"
        )


def print_highlight_diff(operations):

    i = 0

    while i < len(operations):

        # Unchanged line
        if operations[i][0] == " ":

            op, line = operations[i]

            sys.stdout.buffer.write(
                b" " + line + b"\n"
            )

            i += 1
            continue

        # Change block
        deletions = []
        insertions = []

        while (
            i < len(operations)
            and operations[i][0] != " "
        ):

            op, line = operations[i]

            if op == "-":
                deletions.append(line)

            elif op == "+":
                insertions.append(line)

            i += 1

        # Print deletions first.
        for line in deletions:
            sys.stdout.buffer.write(
                b"-" + line + b"\n"
            )

        # Pair deletions and insertions.
        pair_count = min(
            len(deletions),
            len(insertions)
        )

        # Print insertions.
        for index, line in enumerate(insertions):

            # Print + line.
            sys.stdout.buffer.write(
                b"+" + line + b"\n"
            )

            # If this insertion has a matching
            # deletion, print ? immediately after it.
            if index < pair_count:

                old_line = deletions[index]

                old_ranges, new_ranges = character_ranges(
                    old_line,
                    line
                )

                old_text = format_ranges(
                    old_ranges
                )

                new_text = format_ranges(
                    new_ranges
                )

                question = (
                    f"? {old_text} | {new_text}\n"
                )

                # IMPORTANT:
                # Use the same binary output stream
                # as the + line so ordering is guaranteed.
                sys.stdout.buffer.write(
                    question.encode("utf-8")
                )


def main() -> int:

    if len(sys.argv) != 4 or sys.argv[1] not in (
        "lines",
        "highlight"
    ):
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr
        )
        return 2

    command, a_path, b_path = sys.argv[1:]

    try:
        a_lines = read_lines(a_path)
        b_lines = read_lines(b_path)

    except OSError as error:
        print(error, file=sys.stderr)
        return 2

    try:

        operations = myers_diff(
            a_lines,
            b_lines
        )

        if command == "lines":

            print_lines_diff(
                operations
            )

        else:

            print_highlight_diff(
                operations
            )

    except (
        UnicodeDecodeError,
        ValueError
    ) as error:

        print(error, file=sys.stderr)
        return 2

    return 0


raise SystemExit(main())