# Micropython file editor(s)

The purpose of these tools is to allow users of micropython devices to edit
files through a tty serial terminal connection. There are now two tools: a text
editor and a binary file hex editor. Both operate exclusively in command mode.

## editor.py

It is simple, but it has some nice features:

1. Preceding spaces are displayed with an underscore at the beginning of every 4
spaces.
2. It uses a paging and offset system to scroll through a file, displaying only
what can be contained in your terminal (determined by the parameter passed to
the `edit` function).
3. There is an edit history buffer with up to 100 applied and undone edits, so
you can undo or redo edits.
4. It keeps a checksum of the `applied_edits` buffer on file read and write to
detect unsaved edits when the "quit" command is run, which then requires
confirmation to abandon those edits. This also detects when edits have been
undone after the last file write.

This can be used outside of micropython, but why would you use this when you can
use vim?

## hexeditor.py

This is much like the original editor, but instead of having lines of text, it
has lines of hexadecimal representations of binary data (with an ASCII
representation on the right side); instead of line numbers, it displays byte
offsets. Its features are the following:

1. Bytes are displayed in hexadecimal with spaces between each byte for clarity.
2. It also uses a paging and offset system, displaying only what can be
contained in your terminal (determined by the `page_size` and `bytes_per_line`
parameters passed to the `hexedit` function).
3. ASCII representations are displayed on the right (or dots if not renderable).
4. There is an edit history buffer with up to 100 applied and/or undone edits.
5. It keeps a checksum of the `applied_edits` buffer on file read and write to
detect unsaved edits when the "quit" command is run, which then requires
confirmation to abandon those edits. This also detects when edits have been
undone after the last file write.

This may be more useful outside of micropython, though other tools exist.

## Installation

There are two ways to install the desired editor on a micropython-enabled
microcontroller:

1. Including in a custom firmware, in which case you need to copy the `editor.py`
or `hexeditor.py` file into the proper directory for your build process.
2. Copying and pasting via the REPL. This requires the following steps:
    1. Run `python make_pastable.py [editor|hexeditor] > pastable_editor.txt` to
    generate a file with doubled backslashes
    2. Open the file and copy its contents
    3. Type `data = '''` into the REPL
    4. Paste the file contents
    5. Type `'''` and enter
    6. Type `with open('/path/to/libs/editor.py', 'w') as f:` and enter
    7. Type `    f.write(data)` and enter, deindent if necessary, and enter again

Additionally, `copy_pastable_editor.py` and `copy_pastable_hexeditor.py` are
also available, and they were generated in this way. I will try to remember to
update them whenever I update the main editor/hexeditor code; running the step
2.1 will guarantee it is up-to-date.

## Usage

### Micropython REPL

#### editor.py

To use, first `import edit from editor`, then `edit('/path/to/file', page_size)`
to begin the interactive editor. The `page_size` parameter has a default of 42
because that is the Ultimate Answer to Life, The Universe, and Everything --
actually, it just works well in my terminal when I use screen, but you will want
to tune this to fit your setup. You can change it while editing with the 'c {x}'
('change {pagesize}') command.

The interface is simple. The first line printed says the range of lines that are
printed, e.g. 'Displaying lines 0-41' or 'Displaying lines 42-83'. Then a page of
lines are listed, each preceded with padded line numbers in brackets, e.g.
'[04]:'. Line numbers are padded only when the range includes line numbers that
have different lengths when converted to strs. At the bottom, the commands are
displayed across three lines:

```
Commands: [r]e[place] {lineno} {count=1}|d[elete] {lineno} {count=1}|i[nsert] {lineno} {count=1}|a[ppend] {count=1}
          c[hange] {pagesize=42}|o[ffset] {lines}|n[ext]|p[revious]|s[elect] {pageno}
          u[ndo] {count=1}|r[edo] {count=1}|w[rite]|q[uit]
```

Then there is a simple prompt with a question mark. Type the command you want
to run and hit enter. If you do not specify a required argument for a command,
the screen will redraw, and an error message will be printed; this may cause the
top line showing which lines are displayed to scroll out of focus.

You can type either the full command or the short command, which is the single
character not enclosed in square brackets. For replace, insert, and append,
there will be an empty prompt for each line required to complete the command. An
empty line will be accepted as an empty line. Commands are case insensitive.

#### hexeditor.py

Use is nearly identical to `editor.py`, with the difference being that all
replaced/inserted/appended data must be inputted in valid hexadecimal form
(without any preceeding "0x"). The first line printed says "Displaying bytes
xxx-yyy". The next line is a header showing relative offsets of the hexadecimal
bytes printed below. Then each line of hexadecimal printed will start with the
starting offset, then each byte will be separated with a space for legibility,
then an ASCII representation (or periods/dots if not ASCII renderable) on the
right. At the bottom, the commands are displayed across three lines:

```
Commands: [r]e[place] {offset} {count}|d[elete] {offset} {count=1}|i[nsert] {offset} {count}|a[ppend] {count}
          c[hange] {bytes_per_line=40} {page_size=35}|o[ffset] {bytes}|n[ext]|p[revious]|s[elect] {pageno}
          u[ndo] {count=1}|r[edo] {count=1}|w[rite]|q[uit]
```

Note that for the `replace` command, the number of bytes that will be replaced
will be equal to the number of bytes input. E.g. if you type in "0a 0b 0c",
three bytes will be replaced starting at the offset supplied to the `replace`
command; if the count argument is supplied, the input bytes will be counted and
compared, and an error message will appear instead of replacing the bytes if
there is a discrepancy (essentially an optional safety feature). Same caveat
regarding the optional count argument applies to `insert` and `append` commands.

Also note that if the offset is manually set with the `offset` command, the
paging system will not be able to scroll back to bytes before that offset.
However, paging will work for the remainder of the file.

### CLI

#### editor.py

If you want to use this with the CLI from a non-REPL terminal, you can execute
it with the path of the file you want to edit and optionally the page size as
parameters:

```bash
python editor.py /path/to/file.txt 42
```

For a Posix system, you can make it executable and move it somewhere it is
accessible from your environment's path if you want to. The interactive
interface is the same as above.

#### hexeditor.py

Similarly, you can use this with the CLI from a non-REPL terminal with optional
`page_size` and `bytes_per_line` parameters:

```bash
python hexeditor.py /path/to/file.bin 35 40
```

## Miscellaneous notes

The original `editor.py` file was written entirely with vim -- no AI assistance.
I have tested it extensively on ESP32 microcontrollers and often use it instead
of thonny or other file editors when experimenting.

The `hexeditor.py` file was generated by Cursor as an adaptation of the original
editor with the desired changes for handling binary data. It has undergone much
less testing and use, but it appears to function as intended after a few small
patches.

## License

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

