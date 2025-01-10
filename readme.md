# Micropython file editor

The purpose of this tool is to allow users of micropython devices to edit files
through a tty serial terminal connection. It is simple, but it has some nice
features:

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

## Installation

There are two ways to install this on a micropython-enabled microcontroller:

1. Including in a custom firmware, in which case you need to copy the `edit.py`
file into the proper directory for your build process.
2. Copying and pasting via the REPL. This requires the following steps:
    1. Run `python make_pastable.py > pastable_editor.txt` to generate a file
with doubled backslashes
    2. Open the file and copy its contents
    3. Type `data = '''` into the REPL
    4. Paste the file contents
    5. Type `'''` and enter
    6. Type `with open('/path/to/libs/editor.py', 'w') as f:` and enter
    7. Type `    f.write(data)` and enter, deindent if necessary, and enter again

Another file, `copy_pastable_editor.py`, is also available, and it was generated
in this way. I will try to remember to update it whenever I update the main
editor code; running the step 2.1 will guarantee it is up-to-date.

## Usage

### Micropython REPL

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
displayed across two lines:

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

### CLI

If you want to use this with the CLI from a non-REPL terminal, you can execute
it with the path of the file you want to edit and optionally the page size as
parameters:

```bash
python editor.py /path/to/file.txt 42
```

For a Posix system, you can add a shebang to the top, make it executable, and
move it somewhere it is accessible from your environment's path if you want to.
The interactive interface is the same as above.

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

