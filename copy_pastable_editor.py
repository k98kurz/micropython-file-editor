from collections import deque, namedtuple
import os


"""
ISC License

Copyleft (c) 2025 Jonathan Voss (k98kurz)

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyleft notice and this permission notice appear in
all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""


Edit = namedtuple('Edit', ['command', 'args', 'old_line', 'new_line'])


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

def edit(fpath: str, page_size: int = 43, history_buffer_size: int = 100):
    applied_edits: deque[Edit] = deque([], history_buffer_size)
    undone_edits: deque[Edit] = deque([], history_buffer_size)

    def undo():
        if not len(applied_edits):
            return
        ed = applied_edits.pop()
        if ed.command == 'e':
            if ed.args[0] >= len(lines) or lines[ed.args[0]] != ed.new_line:
                return
            lines[ed.args[0]] = ed.old_line
        elif ed.command == 'd':
            if ed.args[0] > len(lines):
                lines.append(ed.old_line)
            else:
                lines.insert(ed.args[0], ed.old_line)
        elif ed.command == 'i':
            if ed.args[0] >= len(lines) or lines[ed.args[0]] != ed.new_line:
                return
            lines[ed.args[0]] = ed.old_line
        elif ed.command == 'a':
            if lines[-1] != ed.new_line:
                return
        undone_edits.append(ed)

    def redo():
        if not len(undone_edits):
            return
        ed = undone_edits.pop()
        if ed.command == 'e':
            if ed.args[0] >= len(lines) or lines[ed.args[0]] != ed.old_line:
                return
            lines[ed.args[0]] = ed.new_ilne
        elif ed.command == 'd':
            if ed.args[0] >= len(lines) or lines[ed.args[0]] != ed.old_line:
                return
            del lines[ed.args[0]]
        elif ed.command == 'i':
            if ed.args[0] >= len(lines):
                return
            lines[ed.args[0]] = ed.new_line
        elif ed.command == 'a':
            lines.append(ed.new_line)
        applied_edits.append(ed)

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

        print("\\nCommands: [r]e[place] {lineno}|d[elete] {lineno}|i[nsert] {lineno}|a[ppend]|u[ndo]{count=1}\\n" + \\
            "          r[edo] {count=1}|o[ffset] {lines}|n[ext]|p[revious]|s[elect] {pageno}|w[rite]|q[uit]")
        if error:
            print(error)
            error = None

        command = input("? ").split(' ')
        index = int(command[1]) if len(command) > 1 else 0

        if command[0] in ('e', 'replace'):
            if len(command) != 2:
                error = 'Must specify a line index for replace'
                continue
            line = input('')
            if line:
                ed = Edit('e', [index], lines[index], line)
                lines[index] = line
                applied_edits.append(ed)

        elif command[0] in ('d', 'delete'):
            if len(command) != 2:
                error = 'Must specify a line index for delete'
                continue
            applied_edits.append(Edit('d', [index], lines[index], None))
            del lines[index]

        elif command[0] in ('i', 'insert'):
            if len(command) != 2:
                error = 'Must specify a line index for insert'
                continue
            line = input('')
            lines.insert(index, line)
            applied_edits.append(Edit('i', [index], None, line))

        elif command[0] in ('a', 'append'):
            line = input('')
            lines.append(line)
            applied_edits.append(Edit('a', [], None, line))

        elif command[0] in ('u', 'undo'):
            undo()
            while index > 1:
                index -= 1
                undo

        elif command[0] in ('r', 'redo'):
            redo()
            while index > 1:
                index -= 1
                redo()

        elif command[0] in ('o', 'offset'):
            if len(command) != 2:
                error = 'Must specify a line count for offset'
                continue
            offset = index

        elif command[0] in ('n', 'next'):
            page = 0 if (page + 1) * page_size >= len(lines) else page + 1

        elif command[0] in ('p', 'previous'):
            page = len(lines) // page_size if page == 0 else page - 1

        elif command[0] in ('s', 'select'):
            if len(command) != 2:
                error = 'Must specify a page index to select a page'
                continue
            if index * page_size < len(lines):
                page = index

        elif command[0] in ('w', 'write'):
            write_file(fpath, lines)

        elif command[0] in ('q', 'quit'):
            break


