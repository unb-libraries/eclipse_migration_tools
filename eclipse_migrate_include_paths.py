#!/usr/bin/env python
# eclipse_migrate_include_paths.py
#
# Easily migrate include paths from ECLIPSE to PULSAR.
#
import os
import re
import readline
import shutil

def read_input_prefill(prompt, prefill = ''):
    """
    Provides user input through readline with 'prefill' default values.
    """
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return raw_input(prompt)
    finally:
        readline.set_startup_hook()

def guess_new_includepath(include_path):
    """
    Guess at the desired 'new' path for includes.
    """
    old_path_start = '/www/'
    new_path_start = '/srv/www/lib.unb.ca/htdocs/'
    if include_path.startswith(old_path_start):
        return include_path.replace(old_path_start, new_path_start) 
    return include_path


tree_to_walk = '/home/jsanford/gitDev/lib.unb.ca-webtree/admintools'

regex_to_find_paths = re.compile(r'include.*[\'\"](.*)[\'\"].*;')
replace_queue = {}

for parse_root, dirs, tree_files in os.walk(tree_to_walk):
    for cur_tree_file in tree_files:
        # Read in tree file as string
        full_treeitem_filepath = os.path.join(parse_root, cur_tree_file)
        html_file = open(full_treeitem_filepath, 'r')
        file_as_string = html_file.read()
        html_file.close()
        # Extract path values from file
        for (pathval) in re.findall(regex_to_find_paths, file_as_string):
            if not pathval.startswith('/srv/www/lib.unb.ca/htdocs/'):
                if not pathval in replace_queue :
                    print "Replacing " + pathval
                    new_filepath = read_input_prefill(
                                                      'New path : ',
                                                      guess_new_includepath(pathval)
                                                      )
                    replace_queue[pathval] = new_filepath

        # Replace old paths with new in HTML/PHP file.
        print "Replacing all In : " + full_treeitem_filepath
        with open(full_treeitem_filepath, 'w') as html_file:
            for old_string, new_string in replace_queue.iteritems():
                if not new_string is '':
                    file_as_string = file_as_string.replace(old_string, new_string)
            html_file.write(file_as_string)
            html_file.close()
