def make_pastable() -> str:
    """Reads the editor.py source file, replaces all backslash chars
        with double backslashes, then returns that str.
    """
    with open('editor.py', 'r') as f:
        data = f.read()
    return data.replace('\\', '\\\\')

if __name__ == '__main__':
    print(make_pastable())

