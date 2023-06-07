""" Finder is a library for helping you get files and folders you need. """
import os


def get_files_with_ending(ending, exclude=None):
    """ Recursive get all files with ending. """
    matches = []
    if os.name == "nt" and exclude:
        exclude = exclude.replace("/", "\\")
    for root, _, files in os.walk("."):
        for file_name in files:
            if file_name.endswith(ending):
                if exclude and exclude in os.path.join(root, file_name):
                    continue
                matches.append(os.path.join(root, file_name))
    return matches
