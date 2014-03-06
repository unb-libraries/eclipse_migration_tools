#!/usr/bin/env python
# eclipse_remove_squelched_includes.py
#
# Easily un-squelch includes.
#
import os
import re


tree_to_walk = '/home/jsanford/gitDev/lib.unb.ca-webtree/core'

for parse_root, dirs, tree_files in os.walk(tree_to_walk):
    for cur_tree_file in tree_files: