from binascii import crc32
from collections import deque, namedtuple
from sys import argv
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

def Edit_to_bytes(edit: Edit) -> bytes:
    val = edit.command.encode()
    val = val + len(edit.args).to_bytes(1, 'big')
    for arg in edit.args:
        val = val + arg.to_bytes(2, 'big')
    if edit.old_line:
        val = val + edit.old_line.encode()
    if edit.new_line:
        val = val + edit.new_line.encode()
    return val


def cat(fname: str) -> str:
    """Returns the str contents of a file. Intended to be used with
        `print` or another utility function from this library.
    """
    with open(fname, 'r') as f:
        return f.read()

def to_lines(data: str) -> list[str]:
    return data.split('\n')

def from_lines(data: list[str]) -> str:
    return '\n'.join(data)

def number_lines(data: str|list[str]) -> str:
    """Prepends each line with its line number."""
    data = to_lines(data) if type(data) is str else data
    max_i = len(data)
    for i in range(len(data)):
        data[i] = f'[{pad_line_no(i, max_i)}]: {data[i]}'
    return from_lines(data)

def page(data: str|list[str], index: int = 0, offset: int = 0, size: int = 46, linenos: bool = False) -> str:
    """Given file contents, return a specific page. If linenos=True,
        each line will have its line number prepended. Intended to be
        used with `print` on output from `cat`.
    """
    data = to_lines(data) if type(data) is str else data

    if index * size + offset < len(data):
        if len(data) > size * (index + 1) + offset:
            data = data[size*index+offset:size*(index+1)+offset]
        else:
            data = data[size*index+offset:]
    elif size + offset < len(data):
        data = data[offset:offset+size]
    elif size < len(data):
        data = data = data[:size]

    if linenos:
        max_i = len(data)
        for i in range(len(data)):
            data[i] = f'[{pad_line_no(i, max_i)}]: {data[i]}'
    return from_lines(data)

def grep(data: str|list[str], search: str|list[str]) -> str:
    """Searches the given data for the search term[s]. Returns all
        matched lines; each matching line will be prepended with its
        line number. Intended to be used with `print` on output from
        `cat`.
    """
    data = to_lines(data) if type(data) is str else data
    matches = []
    max_i = len(data) - 1

    for i, line in enumerate(data):
        if type(search) is str and search in line:
            matches.append(f'{pad_line_no(i, max_i)}: {line}')
        elif type(search) is list:
            for s in search:
                if s in line:
                    matches.append(f'{pad_line_no(i, max_i)}: {line}')
                    break

    return from_lines(matches)

def read_file(fpath: str) -> list[str]:
    try:
        with open(fpath, 'r') as f:
            return f.read().split('\n')
    except:
        return []

def write_file(fpath: str, lines: list[str]):
    with open(fpath, 'w') as f:
        f.write('\n'.join(lines))

def pad_line_no(i: int, max_i: int) -> str:
    i = str(i)
    max_i = str(max_i)
    while len(max_i) > len(i):
        i = f'0{i}'
    return i

def checksum(edit_buffer: deque[Edit] = None, lines: list[str] = None) -> int:
    """Calculate a checksum for an edit buffer and/or lines of text."""
    val = 0
    if edit_buffer:
        for i in range(len(edit_buffer)):
            val = crc32(Edit_to_bytes(edit_buffer[i]), val)
    if lines:
        for i in range(len(lines)):
            val = crc32(lines[i].encode(), val)
    return val

def edit(fpath: str, page_size: int = 42, history_buffer_size: int = 100):
    """Edit a file. This is the main function for this library."""
    applied_edits: deque[Edit] = deque([], history_buffer_size)
    undone_edits: deque[Edit] = deque([], history_buffer_size)
    original_page_size = page_size

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
            del lines[ed.args[0]]
        elif ed.command == 'a':
            if lines[-1] != ed.new_line:
                return
        del lines[-1]
        undone_edits.append(ed)

    def redo():
        if not len(undone_edits):
            return
        ed = undone_edits.pop()
        if ed.command == 'e':
            if ed.args[0] >= len(lines) or lines[ed.args[0]] != ed.old_line:
                return
            lines[ed.args[0]] = ed.new_line
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
    check = checksum(applied_edits)
    page = 0
    error = ''
    offset = 0
    while True:
        if hasattr(os, 'system') and hasattr(os, 'name'):
            try:
                os.system('cls' if os.name == 'nt' else 'clear')
            except:
                ...

        start = page * page_size + offset
        stop = min((page + 1) * page_size + offset, len(lines))
        print(f"Displaying lines {start}-{stop-1}")

        for i in range(start, stop):
            line = lines[i]
            spaces = len(line) - len(line.lstrip())
            line = ''.join([' ' if i % 4 else '_' for i in range(spaces)]) + line.lstrip()
            print(f"[{pad_line_no(i, stop-1)}]: {line}")

        print("\nCommands: [r]e[place] {lineno} {count=1}|d[elete] {lineno} {count=1}|i[nsert] {lineno} {count=1}|a[ppend] {count=1}\n" + \
            "          c[hange] {pagesize=42}|o[ffset] {lines}|n[ext]|p[revious]|s[elect] {pageno}\n" + \
            "          u[ndo] {count=1}|r[edo] {count=1}|w[rite]|q[uit]")
        if error:
            print(error)
            error = None

        command = input("? ").lower().split(' ')
        index = int(f"0{command[1]}") if len(command) > 1 else 0
        index = 0 if index < 0 else index
        count = int(f"0{command[2]}") if len(command) > 2 else 1
        count = 1 if count < 0 else count

        if command[0] in ('e', 'replace'):
            if len(command) < 2:
                error = 'Must specify a line index for replace'
                continue
            end = index + count
            while index < end:
                line = input('')
                if line:
                    ed = Edit('e', [index], lines[index], line)
                    lines[index] = line
                    applied_edits.append(ed)
                index += 1

        elif command[0] in ('d', 'delete'):
            if len(command) < 2:
                error = 'Must specify a line index for delete'
                continue
            while count > 0:
                applied_edits.append(Edit('d', [index], lines[index], None))
                del lines[index]
                count -= 1

        elif command[0] in ('i', 'insert'):
            if len(command) < 2:
                error = 'Must specify a line index for insert'
                continue
            end = index + count
            while index < end:
                line = input('')
                lines.insert(index, line)
                applied_edits.append(Edit('i', [index], None, line))
                index += 1

        elif command[0] in ('a', 'append'):
            if index > 0:
                count = index
            while count > 0:
                line = input('')
                lines.append(line)
                applied_edits.append(Edit('a', [], None, line))
                count -= 1

        elif command[0] in ('u', 'undo'):
            undo()
            while index > 1:
                index -= 1
                undo()

        elif command[0] in ('r', 'redo'):
            redo()
            while index > 1:
                index -= 1
                redo()

        elif command[0] in ('c', 'change'):
            if len(command) < 2:
                index = original_page_size
            page_size = index

        elif command[0] in ('o', 'offset'):
            if len(command) < 2:
                error = 'Must specify a line count for offset'
                continue
            offset = index

        elif command[0] in ('n', 'next'):
            page = 0 if (page + 1) * page_size >= len(lines) else page + 1

        elif command[0] in ('p', 'previous'):
            page = len(lines) // page_size if page == 0 else page - 1

        elif command[0] in ('s', 'select'):
            if len(command) < 2:
                error = 'Must specify a page index to select a page'
                continue
            if index * page_size < len(lines):
                page = index

        elif command[0] in ('w', 'write'):
            write_file(fpath, lines)
            check = checksum(applied_edits)

        elif command[0] in ('q', 'quit'):
            if check != checksum(applied_edits):
                print('Unsaved edits detected. Are you sure you want to quit?')
                confirm = input('[y/N]: ')
                if confirm.lower() in ('y', 'yes'):
                    break
            else:
                break


if __name__ == '__main__':
    if len(argv) > 1:
        filename = argv[1]
        page_size = int(f"0{argv[2]}") if len(argv) > 2 else 0
        if page_size:
            edit(filename, page_size)
        else:
            edit(filename)

