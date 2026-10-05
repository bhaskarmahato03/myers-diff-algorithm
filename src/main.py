import sys


# ---------------------------------------------------------
# File reading
# ---------------------------------------------------------

def read_lines(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"error: cannot read input file: {e}", file=sys.stderr)
        return None

    # An empty file has no lines (b"".split() would give one empty line).
    if data == b"":
        return []

    lines = data.split(b"\n")

    # If file ends with '\n', split() creates one extra empty item.
    if data.endswith(b"\n"):
        lines.pop()

    return lines


# ---------------------------------------------------------
# Myers middle-snake implementation
# ---------------------------------------------------------

def middle_snake(a, a_start, a_end, b, b_start, b_end, equal):
    n = a_end - a_start
    m = b_end - b_start

    max_d = (n + m + 1) // 2
    delta = n - m

    offset = max_d + 1
    size = 2 * max_d + 3

    forward = [-1] * size
    backward = [-1] * size

    forward[offset + 1] = 0
    backward[offset + 1] = 0

    odd = (delta & 1) != 0

    for d in range(max_d + 1):

        # Forward search
        for k in range(-d, d + 1, 2):
            index = offset + k

            if k == -d or (
                k != d and forward[index - 1] < forward[index + 1]
            ):
                x = forward[index + 1]
            else:
                x = forward[index - 1] + 1

            y = x - k

            while (
                x < n
                and y < m
                and equal(a[a_start + x], b[b_start + y])
            ):
                x += 1
                y += 1

            forward[index] = x

            if odd:
                reverse_k = delta - k

                if (
                    -(d - 1) <= reverse_k <= d - 1
                    and backward[offset + reverse_k] != -1
                ):
                    backward_x = n - backward[offset + reverse_k]

                    if x >= backward_x:
                        return a_start + x, b_start + y

        # Backward search
        for k in range(-d, d + 1, 2):
            index = offset + k

            if k == -d or (
                k != d and backward[index - 1] < backward[index + 1]
            ):
                x = backward[index + 1]
            else:
                x = backward[index - 1] + 1

            y = x - k

            while (
                x < n
                and y < m
                and equal(
                    a[a_end - x - 1],
                    b[b_end - y - 1],
                )
            ):
                x += 1
                y += 1

            backward[index] = x

            if not odd:
                forward_k = delta - k

                if (
                    -d <= forward_k <= d
                    and forward[offset + forward_k] != -1
                ):
                    forward_x = forward[offset + forward_k]
                    backward_x = n - x

                    if forward_x >= backward_x:
                        return (
                            a_start + backward_x,
                            b_start + m - (x - k),
                        )

    return a_start, b_start


# ---------------------------------------------------------
# Generic recursive Myers diff
# ---------------------------------------------------------

def myers_recursive(a, a_start, a_end, b, b_start, b_end, equal, result):
    # Remove common prefix
    while (
        a_start < a_end
        and b_start < b_end
        and equal(a[a_start], b[b_start])
    ):
        result.append((" ", a[a_start]))
        a_start += 1
        b_start += 1

    # A is exhausted
    if a_start == a_end:
        while b_start < b_end:
            result.append(("+", b[b_start]))
            b_start += 1
        return

    # B is exhausted
    if b_start == b_end:
        while a_start < a_end:
            result.append(("-", a[a_start]))
            a_start += 1
        return

    # Find common suffix
    suffix_a = a_end
    suffix_b = b_end

    while (
        a_start < suffix_a
        and b_start < suffix_b
        and equal(a[suffix_a - 1], b[suffix_b - 1])
    ):
        suffix_a -= 1
        suffix_b -= 1

    # Only B has changed in the middle
    if a_start == suffix_a:
        while b_start < suffix_b:
            result.append(("+", b[b_start]))
            b_start += 1

        while suffix_a < a_end:
            result.append((" ", a[suffix_a]))
            suffix_a += 1

        return

    # Only A has changed in the middle
    if b_start == suffix_b:
        while a_start < suffix_a:
            result.append(("-", a[a_start]))
            a_start += 1

        while suffix_a < a_end:
            result.append((" ", a[suffix_a]))
            suffix_a += 1

        return

    # Find the middle snake.
    x, y = middle_snake(
        a,
        a_start,
        suffix_a,
        b,
        b_start,
        suffix_b,
        equal,
    )

    # Solve left half
    myers_recursive(
        a,
        a_start,
        x,
        b,
        b_start,
        y,
        equal,
        result,
    )

    # Solve right half
    myers_recursive(
        a,
        x,
        suffix_a,
        b,
        y,
        suffix_b,
        equal,
        result,
    )

    # Add the common suffix
    while suffix_a < a_end:
        result.append((" ", a[suffix_a]))
        suffix_a += 1


def myers_diff(a, b):
    result = []

    myers_recursive(
        a,
        0,
        len(a),
        b,
        0,
        len(b),
        lambda x, y: x == y,
        result,
    )

    return result


# ---------------------------------------------------------
# Part A
# ---------------------------------------------------------

def line_diff(a, b):
    diff = myers_diff(a, b)

    result = []
    i = 0

    while i < len(diff):

        # Keep
        if diff[i][0] == " ":
            result.append(diff[i])
            i += 1
            continue

        deletes = []
        inserts = []

        # Collect one contiguous change block
        while i < len(diff) and diff[i][0] != " ":
            op = diff[i]
            i += 1

            if op[0] == "-":
                deletes.append(op)
            else:
                inserts.append(op)

        # Assignment requires deletions first,
        # then insertions.
        result.extend(deletes)
        result.extend(inserts)

    return result


def print_lines(diff):
    out = sys.stdout.buffer

    for operation, line in diff:
        out.write(operation.encode("ascii"))
        out.write(line)
        out.write(b"\n")

    out.flush()


# ---------------------------------------------------------
# Character-level Myers
# ---------------------------------------------------------

def code_points(line):
    return [ord(ch) for ch in line.decode("utf-8")]


def character_diff(a, b):
    result = []

    myers_recursive(
        a,
        0,
        len(a),
        b,
        0,
        len(b),
        lambda x, y: x == y,
        result,
    )

    return result


# ---------------------------------------------------------
# Highlight ranges
# ---------------------------------------------------------

def format_ranges(ranges):
    if not ranges:
        return "."

    return ",".join(
        f"{start}-{end}"
        for start, end in ranges
    )


def character_ranges(old_line, new_line):
    old_cp = code_points(old_line)
    new_cp = code_points(new_line)

    ops = character_diff(old_cp, new_cp)

    old_ranges = []
    new_ranges = []

    old_pos = 0
    new_pos = 0

    old_start = None
    old_end = None

    new_start = None
    new_end = None

    for operation, value in ops:

        if operation == " ":

            if old_start is not None:
                old_ranges.append(
                    (old_start, old_end)
                )
                old_start = None

            if new_start is not None:
                new_ranges.append(
                    (new_start, new_end)
                )
                new_start = None

            old_pos += 1
            new_pos += 1

        elif operation == "-":

            if old_start is None:
                old_start = old_pos

            old_pos += 1
            old_end = old_pos

        else:
            if new_start is None:
                new_start = new_pos

            new_pos += 1
            new_end = new_pos

    if old_start is not None:
        old_ranges.append(
            (old_start, old_end)
        )

    if new_start is not None:
        new_ranges.append(
            (new_start, new_end)
        )

    return (
        format_ranges(old_ranges),
        format_ranges(new_ranges),
    )


# ---------------------------------------------------------
# Part B
# ---------------------------------------------------------

def print_highlight(diff):
    out = sys.stdout.buffer
    i = 0

    while i < len(diff):

        operation, line = diff[i]

        # Keep
        if operation == " ":
            out.write(b" ")
            out.write(line)
            out.write(b"\n")

            i += 1
            continue

        deletes = []
        inserts = []

        # One contiguous change block
        while i < len(diff) and diff[i][0] != " ":
            operation, line = diff[i]
            i += 1

            if operation == "-":
                deletes.append((operation, line))
            else:
                inserts.append((operation, line))

        # Print all deletions first
        for _, line in deletes:
            out.write(b"-")
            out.write(line)
            out.write(b"\n")

        # Then insertions
        for j, (_, line) in enumerate(inserts):

            out.write(b"+")
            out.write(line)
            out.write(b"\n")

            # Pair insertion j with deletion j
            if j < len(deletes):
                old_line = deletes[j][1]

                old_ranges, new_ranges = character_ranges(
                    old_line,
                    line,
                )

                question = (
                    "? "
                    + old_ranges
                    + " | "
                    + new_ranges
                    + "\n"
                )

                out.write(question.encode("ascii"))

    out.flush()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    if (
        len(sys.argv) != 4
        or sys.argv[1] not in ("lines", "highlight")
    ):
        print(
            "usage: main.py lines|highlight A_PATH B_PATH",
            file=sys.stderr,
        )
        return 2

    command, a_path, b_path = sys.argv[1:]

    file_a = read_lines(a_path)
    if file_a is None:
        return 2

    file_b = read_lines(b_path)
    if file_b is None:
        return 2

    diff = line_diff(file_a, file_b)

    if command == "lines":
        print_lines(diff)
    else:
        print_highlight(diff)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())