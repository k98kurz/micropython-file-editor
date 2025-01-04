import os


def read_file(fpath: str) -> list[str]:
    try:
        with open(fpath, 'r') as f:
            return f.read().split('\\n')
    except:
        return []

def write_file(fpath: str, lines: list[str]):
    with open(fpath, 'w') as f:
        f.write('\\n'.join(lines))

def pad_line_no(i: int, max_i: int) -> str:
    if len(str(max_i)) > len(str(i)):
        return f'0{i}'
    return str(i)

def edit(fpath: str, page_size: int = 43):
    lines = read_file(fpath)
    page = 0
    error = ''
    offset = 0
    while True:
        start = page * page_size + offset
        stop = min((page + 1) * page_size + offset, len(lines))
        if hasattr(os, 'system') and hasattr(os, 'name'):
            try:
                os.system('cls' if os.name == 'nt' else 'clear')
            except:
                ...
        print(f"Displaying lines {start}-{stop-1}")

        for i in range(start, stop):
            line = lines[i]
            spaces = len(line) - len(line.lstrip())
            line = ''.join([' ' if i % 4 else '_' for i in range(spaces)]) + line.lstrip()
            print(f"[{pad_line_no(i, stop-1)}]: {line}")

        print("\\nCommands: r[eplace] {lineno}|d[elete] {lineno}|i[nsert] {lineno}|a[ppend]\\n" + \\
            "          o[ffset] {lines}|n[ext]|p[revious]|s[elect] {pageno}|w[rite]|q[uit]")
        if error:
            print(error)
            error = None

        command = input("? ").split(' ')
        index = int(command[1]) if len(command) > 1 else 0

        if command[0] in ('r', 'replace'):
            if len(command) != 2:
                error = 'Must specify a line index for replace'
            line = input('')
            lines[index] = line if line else lines[index]

        if command[0] in ('d', 'delete'):
            if len(command) != 2:
                error = 'Must specify a line index for delete'
            del lines[index]

        if command[0] in ('i', 'insert'):
            if len(command) != 2:
                error = 'Must specify a line index for insert'
            line = input('')
            lines.insert(index, line)

        if command[0] in ('a', 'append'):
            line = input('')
            lines.append(line)

        if command[0] in ('o', 'offset'):
            if len(command) != 2:
                error = 'Must specify a line count for offset'
            offset = index

        if command[0] in ('n', 'next'):
            page = 0 if (page + 1) * page_size >= len(lines) else page + 1

        if command[0] in ('p', 'previous'):
            page = len(lines) // page_size if page == 0 else page - 1

        if command[0] in ('s', 'select'):
            if len(command) != 2:
                error = 'Must specify a page index to select a page'
            if index * page_size < len(lines):
                page = index

        if command[0] in ('w', 'write'):
            write_file(fpath, lines)

        if command[0] in ('q', 'quit'):
            break


