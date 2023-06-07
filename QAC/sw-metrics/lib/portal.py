""" Portal is a library for helping you jump around in directories. """
import os


class In(object):
    """ Class for changing the current working directory """
    def __init__(self, new_path):
        self.saved_path = None
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def do_for_subfolders(func, exclude=None):
    """ Function to execute a passed function in subfolders """
    folders = next(os.walk('.'))[1]
    for folder in folders:
        if exclude is not None and folder in exclude:
            continue
        func(folder)
