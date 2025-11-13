from sys import argv


def make_editor_pastable() -> str:
    """Reads the editor.py source file, replaces all backslash chars
        with double backslashes, then returns that str.
    """
    with open('editor.py', 'r') as f:
        data = f.read()
    return data.replace('\\', '\\\\')

def make_hexeditor_pastable() -> str:
    """Reads the hexeditor.py source file, replaces all backslash chars
        with double backslashes, then returns that str.
    """
    with open('hexeditor.py', 'r') as f:
        data = f.read()
    return data.replace('\\', '\\\\')

def usage():
    """Tool usage help text."""
    print('Usage: python make_pastable.py [editor|hexeditor]')


if __name__ == '__main__':
    if len(argv) < 2:
        usage()
        exit()
    if argv[1] == 'editor':
        print(make_editor_pastable())
    elif argv[1] == 'hexeditor':
        print(make_hexeditor_pastable())
    else:
        usage()
