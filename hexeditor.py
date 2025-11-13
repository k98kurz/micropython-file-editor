#!/bin/python

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


HexEdit = namedtuple('HexEdit', ['command', 'start_offset', 'end_offset', 'old_bytes', 'new_bytes'])

def HexEdit_to_bytes(hex_edit: HexEdit) -> bytes:
    val = hex_edit.command.encode()
    val = val + hex_edit.start_offset.to_bytes(4, 'big')
    val = val + hex_edit.end_offset.to_bytes(4, 'big')
    val = val + len(hex_edit.old_bytes).to_bytes(4, 'big')
    val = val + hex_edit.old_bytes
    val = val + len(hex_edit.new_bytes).to_bytes(4, 'big')
    val = val + hex_edit.new_bytes
    return val


def bat(fname: str) -> bytes:
    """Returns the bytes contents of a file. Similar to cat."""
    with open(fname, 'rb') as f:
        return f.read()

def read_binary_file(fpath: str) -> bytes:
    """Read a file as binary data."""
    try:
        with open(fpath, 'rb') as f:
            return f.read()
    except:
        return b''

def write_binary_file(fpath: str, data: bytes):
    """Write binary data to a file."""
    with open(fpath, 'wb') as f:
        f.write(data)

def parse_hex_input(hex_str: str) -> bytes:
    """Parse hex digits (e.g., "FF00AB") into bytes. Returns bytes
        object, or raises ValueError if input is invalid. Whitespace is
        stripped and ignored.
    """
    if not hex_str.strip():
        return b''

    hex_str = hex_str.strip().replace(' ', '')
    if len(hex_str) % 2:
        raise ValueError('Invalid hex string: must be even length')
    return bytes.fromhex(hex_str)

def pad_offset(offset: int, max_offset: int) -> str:
    """Pad offset numbers similar to pad_line_no."""
    offset_str = str(offset)
    max_str = str(max_offset)
    while len(max_str) > len(offset_str):
        offset_str = f'0{offset_str}'
    return offset_str

def format_hex_line(offset: int, data: bytes, bytes_per_line: int, max_offset: int) -> str:
    """Format one hex line as [offset]: XX XX ... | ASCII"""
    line_data = data[:bytes_per_line]
    hex_part = ' '.join([f'{b:02X}' for b in line_data])
    # Pad hex_part to ensure consistent width
    hex_part = hex_part.ljust(bytes_per_line * 3 - 1)

    # ASCII representation: printable chars or dots
    ascii_part = ''.join([chr(b) if 32 <= b < 127 else '.' for b in line_data])

    offset_str = pad_offset(offset, max_offset)
    return f'[{offset_str}]: {hex_part} | {ascii_part}'

def format_hex_header(bytes_per_line: int, max_offset: int) -> str:
    """Generate a header row with column numbers 1 through bytes_per_line.
    The header aligns with the hex bytes portion of each line.
    """
    offset_placeholder = 'Offset' + ' ' * (len(str(max_offset)) - 2)
    # Generate column numbers, each right-aligned in 3-character field to match "XX " format
    column_numbers = ' '.join([f'{i:>2}' for i in range(bytes_per_line)])
    return f'{offset_placeholder}{column_numbers}'

def format_hex_display(data: bytes, start_byte: int, bytes_per_line: int, page_size: int) -> list[str]:
    """Generate a list of hex lines for display starting from start_byte."""
    lines = []
    max_offset = len(data) - 1 if len(data) > 0 else 0
    total_bytes = len(data)

    byte_offset = start_byte
    for i in range(page_size):
        if byte_offset >= total_bytes:
            break

        line_data = data[byte_offset:byte_offset + bytes_per_line]
        lines.append(format_hex_line(byte_offset, line_data, bytes_per_line, max_offset))
        byte_offset += bytes_per_line

    return lines

def hex_checksum(edit_buffer: deque[HexEdit] = None, data: bytes = None) -> int:
    """Calculate a checksum for hex edit buffer and/or binary data."""
    val = 0
    if edit_buffer:
        for i in range(len(edit_buffer)):
            val = crc32(HexEdit_to_bytes(edit_buffer[i]), val)
    if data:
        val = crc32(data, val)
    return val

def hexedit(fpath: str, page_size: int = 35, bytes_per_line: int = 40, history_buffer_size: int = 100):
    """Edit a binary file in hex mode. This is the main function for hex editing."""
    applied_edits: deque[HexEdit] = deque([], history_buffer_size)
    undone_edits: deque[HexEdit] = deque([], history_buffer_size)
    original_bytes_per_line = bytes_per_line

    def undo():
        if not len(applied_edits):
            return
        ed = applied_edits.pop()
        if ed.command == 'e':
            # Replace: restore old_bytes
            if ed.start_offset >= len(data):
                return
            # Check if current state matches what we expect
            # After replace, the data at start_offset should be new_bytes
            current_end = min(ed.start_offset + len(ed.new_bytes), len(data))
            current_bytes = bytes(data[ed.start_offset:current_end])
            if current_bytes != ed.new_bytes:
                return
            # Restore old_bytes - always reconstruct since lengths may differ
            new_data = data[:ed.start_offset] + ed.old_bytes + data[current_end:]
            data.clear()
            data.extend(new_data)
        elif ed.command == 'd':
            # Delete: restore old_bytes
            if ed.start_offset > len(data):
                data.extend(ed.old_bytes)
            else:
                # Insert old_bytes back at start_offset
                new_data = data[:ed.start_offset] + ed.old_bytes + data[ed.start_offset:]
                data.clear()
                data.extend(new_data)
        elif ed.command == 'i':
            # Insert: remove new_bytes
            if ed.start_offset >= len(data) or data[ed.start_offset:ed.start_offset+len(ed.new_bytes)] != ed.new_bytes:
                return
            new_data = data[:ed.start_offset] + data[ed.start_offset+len(ed.new_bytes):]
            data.clear()
            data.extend(new_data)
        elif ed.command == 'a':
            # Append: remove new_bytes from end
            if len(data) < len(ed.new_bytes) or data[-len(ed.new_bytes):] != ed.new_bytes:
                return
            new_data = data[:-len(ed.new_bytes)]
            data.clear()
            data.extend(new_data)
        undone_edits.append(ed)

    def redo():
        if not len(undone_edits):
            return
        ed = undone_edits.pop()
        if ed.command == 'e':
            # Replace: apply new_bytes
            if ed.start_offset >= len(data):
                return
            # Check if current state matches what we expect
            # Before replace, the data at start_offset should be old_bytes
            # Use len(old_bytes) instead of end_offset since data structure may have changed
            current_end = min(ed.start_offset + len(ed.old_bytes), len(data))
            current_bytes = bytes(data[ed.start_offset:current_end])
            if current_bytes != ed.old_bytes:
                return
            # Apply new_bytes - always reconstruct since lengths may differ
            new_data = data[:ed.start_offset] + ed.new_bytes + data[current_end:]
            data.clear()
            data.extend(new_data)
        elif ed.command == 'd':
            # Delete: remove old_bytes
            if ed.start_offset >= len(data):
                return
            current_end = min(ed.start_offset + len(ed.old_bytes), len(data))
            current_bytes = bytes(data[ed.start_offset:current_end])
            if current_bytes != ed.old_bytes:
                return
            new_data = data[:ed.start_offset] + data[current_end:]
            data.clear()
            data.extend(new_data)
        elif ed.command == 'i':
            # Insert: add new_bytes
            if ed.start_offset > len(data):
                return
            new_data = data[:ed.start_offset] + ed.new_bytes + data[ed.start_offset:]
            data.clear()
            data.extend(new_data)
        elif ed.command == 'a':
            # Append: add new_bytes
            data.extend(ed.new_bytes)
        applied_edits.append(ed)

    data = bytearray(read_binary_file(fpath))
    check = hex_checksum(applied_edits, data)
    page = 0
    error = ''
    offset = 0

    while True:
        if hasattr(os, 'system') and hasattr(os, 'name'):
            try:
                os.system('cls' if os.name == 'nt' else 'clear')
            except:
                ...

        # Calculate display range
        total_bytes = len(data)

        # Calculate which byte range we're displaying
        # offset is now a byte offset, page advances by page_size * bytes_per_line bytes
        start_byte = offset + (page * page_size * bytes_per_line)
        if start_byte > total_bytes:
            start_byte = total_bytes
        end_byte = min(start_byte + (page_size * bytes_per_line), total_bytes)

        print(f"Displaying bytes {start_byte}-{end_byte-1 if end_byte > 0 else 0}")

        # Display header with column numbers
        max_offset = len(data) - 1 if len(data) > 0 else 0
        print(format_hex_header(bytes_per_line, max_offset))

        # Display hex lines
        hex_lines = format_hex_display(bytes(data), start_byte, bytes_per_line, page_size)
        for line in hex_lines:
            print(line)

        print("\nCommands: [r]e[place] {offset} {count}|d[elete] {offset} {count=1}|i[nsert] {offset} {count}|a[ppend] {count}\n" + \
            "          c[hange] {bytes_per_line=40} {page_size=35}|o[ffset] {bytes}|n[ext]|p[revious]|s[elect] {pageno}\n" + \
            "          u[ndo] {count=1}|r[edo] {count=1}|w[rite]|q[uit]")
        if error:
            print(error)
            error = ''

        command = input("? ").lower().lstrip().split(' ')

        try:
            byte_offset = int(f"0{command[1]}") if len(command) > 1 else 0
            byte_offset = 0 if byte_offset < 0 else byte_offset
            count = int(f"0{command[2]}") if len(command) > 2 else None
        except Exception as e:
            error = str(e)
            continue

        if count is not None:
            count = 1 if count < 0 else count

        if command[0] in ('e', 'replace'):
            if len(command) < 2:
                error = 'Must specify a byte offset for replace'
                continue
            if byte_offset >= len(data):
                error = f'Offset {byte_offset} is beyond end of file (length: {len(data)})'
                continue

            # Get hex input
            hex_input = input('')
            try:
                new_bytes = parse_hex_input(hex_input)
            except ValueError as e:
                error = str(e)
                continue

            # Validate count if provided
            if count is not None:
                if len(new_bytes) != count:
                    error = f'Expected {count} byte(s), but got {len(new_bytes)} byte(s)'
                    continue
            else:
                count = len(new_bytes)

            if count == 0:
                error = 'Cannot replace with zero bytes (use delete instead)'
                continue

            end_offset = min(byte_offset + count, len(data))
            old_bytes = bytes(data[byte_offset:end_offset])

            # Perform replace - handle different lengths properly
            # Store end_offset as the ORIGINAL end (before edit) for proper undo/redo
            if len(new_bytes) == len(old_bytes):
                # Same length: simple replacement
                data[byte_offset:end_offset] = new_bytes
            else:
                # Different length: need to reconstruct
                new_data = data[:byte_offset] + new_bytes + data[end_offset:]
                data.clear()
                data.extend(new_data)

            applied_edits.append(HexEdit('e', byte_offset, end_offset, old_bytes, new_bytes))

        elif command[0] in ('d', 'delete'):
            if len(command) < 2:
                error = 'Must specify a byte offset for delete'
                continue
            if byte_offset >= len(data):
                error = f'Offset {byte_offset} is beyond end of file (length: {len(data)})'
                continue

            if count is None:
                count = 1
            if count <= 0:
                error = 'Count must be positive'
                continue

            end_offset = min(byte_offset + count, len(data))
            old_bytes = bytes(data[byte_offset:end_offset])

            # Perform delete
            new_data = data[:byte_offset] + data[end_offset:]
            data.clear()
            data.extend(new_data)

            applied_edits.append(HexEdit('d', byte_offset, end_offset, old_bytes, b''))

        elif command[0] in ('i', 'insert'):
            if len(command) < 2:
                error = 'Must specify a byte offset for insert'
                continue
            if byte_offset > len(data):
                error = f'Offset {byte_offset} is beyond end of file (length: {len(data)})'
                continue

            # Get hex input
            hex_input = input('')
            try:
                new_bytes = parse_hex_input(hex_input)
            except ValueError as e:
                error = str(e)
                continue

            # Validate count if provided
            if count is not None:
                if len(new_bytes) != count:
                    error = f'Expected {count} byte(s), but got {len(new_bytes)} byte(s)'
                    continue
            else:
                count = len(new_bytes)

            if count == 0:
                error = 'Cannot insert zero bytes'
                continue

            # Perform insert
            new_data = data[:byte_offset] + new_bytes + data[byte_offset:]
            data.clear()
            data.extend(new_data)

            applied_edits.append(HexEdit('i', byte_offset, byte_offset, b'', new_bytes))

        elif command[0] in ('a', 'append'):
            # Get hex input
            hex_input = input('')
            try:
                new_bytes = parse_hex_input(hex_input)
            except ValueError as e:
                error = str(e)
                continue

            # Validate count if provided
            count = byte_offset
            if count is not None:
                if len(new_bytes) != count:
                    error = f'Expected {count} byte(s), but got {len(new_bytes)} byte(s)'
                    continue
            else:
                count = len(new_bytes)

            if count == 0:
                error = 'Cannot append zero bytes'
                continue

            # Perform append
            start_pos = len(data)
            data.extend(new_bytes)

            applied_edits.append(HexEdit('a', start_pos, start_pos, b'', new_bytes))

        elif command[0] in ('u', 'undo'):
            undo()
            undo_count = count if count is not None else 1
            while undo_count > 1:
                undo_count -= 1
                undo()

        elif command[0] in ('r', 'redo'):
            redo()
            redo_count = count if count is not None else 1
            while redo_count > 1:
                redo_count -= 1
                redo()

        elif command[0] in ('c', 'change'):
            if len(command) < 2:
                byte_offset = original_bytes_per_line
            bytes_per_line = byte_offset
            if bytes_per_line <= 0:
                bytes_per_line = original_bytes_per_line
                error = f'Bytes per line must be positive; set to {original_bytes_per_line}.'
            if count:
                if count > 0:
                    page_size = count
                else:
                    error = f'{error} Page size must be positive.'

        elif command[0] in ('o', 'offset'):
            if len(command) < 2:
                error = 'Must specify a byte offset'
                continue
            offset = byte_offset
            page = 0

        elif command[0] in ('n', 'next'):
            total_bytes = len(data)
            next_start = offset + ((page + 1) * page_size * bytes_per_line)
            if next_start >= total_bytes:
                page = 0
            else:
                page = page + 1

        elif command[0] in ('p', 'previous'):
            if page == 0:
                # Calculate max page based on offset
                total_bytes = len(data)
                max_bytes_from_offset = max(0, total_bytes - offset)
                max_page = (max_bytes_from_offset + page_size * bytes_per_line - 1) // (page_size * bytes_per_line) - 1
                if max_page < 0:
                    max_page = 0
                page = max_page
            else:
                page = page - 1

        elif command[0] in ('s', 'select'):
            if len(command) < 2:
                error = 'Must specify a page index to select a page'
                continue
            total_bytes = len(data)
            selected_start = offset + (byte_offset * page_size * bytes_per_line)
            if selected_start < total_bytes:
                page = byte_offset

        elif command[0] in ('w', 'write'):
            write_binary_file(fpath, bytes(data))
            check = hex_checksum(applied_edits, data)

        elif command[0] in ('q', 'quit'):
            if check != hex_checksum(applied_edits, data):
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
        bytes_per_line = int(f"0{argv[3]}") if len(argv) > 3 else 0
        if page_size:
            if bytes_per_line:
                hexedit(filename, page_size, bytes_per_line)
            else:
                hexedit(filename, page_size)
        else:
            hexedit(filename)
    else:
        print(f'Usage: {argv[0]} /path/to/file [page_size] [bytes_per_line]')
        print('       The page_size parameter is optional; default is 35')
        print('       The bytes_per_line parameter is optional; default is 40')

