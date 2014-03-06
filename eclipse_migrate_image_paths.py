#!/usr/bin/env python
# eclipse_migrate_image_paths.py
#
# Migrate images in webserver project directories.
#
# This script performs 2 tasks:
# 1) Migrates image binaries from their current position mixed in with
#    code to a new location, sanitizing names of offending files in the
#    process.
# 2) Updates the references to that file within the HTML/PHP to reflect
#    the new location and filenames.
#
from bs4 import BeautifulSoup
import os
import re
import readline
import shutil
import unicodedata


def slugify_path(value):
    """
    Ripped from django utils/text.py
    Converts to lowercase, removes non-word characters (alphanumerics and
    underscores) and converts spaces to hyphens. Also strips leading and
    trailing whitespace.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\/\.\w\s-]', '', value).strip()
    return re.sub('[-\s]+', '-', value)

def read_input_prefill(prompt, prefill = ''):
    """
    Provides user input through readline with 'prefill' default values.
    """
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return raw_input(prompt)
    finally:
        readline.set_startup_hook()

def guess_new_imagepath(image_path, server_url, subdir_slug):
    """
    Guess at the desired 'new' path for image binaries, based on .
    """
    if subdir_slug in image_path :
        image_path = re.sub(subdir_slug, '', image_path)
    slugged_path = slugify_path(unicode(image_path))
    new_imagepath_guess = server_url + '/'+ subdir_slug + '/' + slugged_path
    new_imagepath_guess = re.sub('(?<!http:)/{2,}', '/', new_imagepath_guess)
    return new_imagepath_guess


tree_to_walk = '/home/jsanford/gitDev/lib.unb.ca-webtree/admintools/eResources_admin'
subdir_string = '/admintools/eResources_admin'
media_server_url = 'http://media.lib.unb.ca'
source_image_root = '/home/jsanford/gitDev/media-sourcetree-root'
target_image_root = '/home/jsanford/gitDev/media-webtree-root'

replace_queue = {}

for parse_root, dirs, tree_files in os.walk(tree_to_walk):
    for cur_tree_file in tree_files:
        copy_queue = {}
        # Read in tree file as string
        full_treeitem_filepath = os.path.join(parse_root, cur_tree_file)
        html_file = open(full_treeitem_filepath, 'r')
        file_as_string = html_file.read()
        html_file.close()
        # Extract img src values from HTML
        tree_file_soup = BeautifulSoup(file_as_string)
        img_src_values = set([image["src"] for image in tree_file_soup.findAll("img")])
        if len(img_src_values) > 0 :
            print "Operating on " + cur_tree_file + ":\n"
            for src_image_path in img_src_values :
                if not src_image_path.startswith('http://') :
                    if not src_image_path in replace_queue :
                        print "Replacing " + src_image_path
                        new_filestring = read_input_prefill('New img src : ',
                                                            guess_new_imagepath(src_image_path,
                                                                                media_server_url,
                                                                                subdir_string)
                                                            )
                        replace_queue[src_image_path] = new_filestring

                        if subdir_string in src_image_path :
                            src_image_path = re.sub(subdir_string, '', src_image_path)
                        if subdir_string in new_filestring :
                            new_filestring = re.sub(subdir_string, '', new_filestring)

                        copy_source = read_input_prefill('Copy Source : ',
                                                         re.sub('/{2,}',
                                                                '/',
                                                                source_image_root +
                                                                '/' +
                                                                subdir_string +
                                                                '/' +
                                                                src_image_path
                                                                )
                                                         )
                        copy_target = read_input_prefill('Copy Dest : ',
                                                         re.sub('/{2,}',
                                                                '/',
                                                                target_image_root +
                                                                '/' +
                                                                subdir_string +
                                                                '/' +
                                                                re.sub(re.escape(media_server_url),
                                                                       '',
                                                                       str(new_filestring)
                                                                       )
                                                                )
                                                         )
                        copy_queue[copy_source] = copy_target
        # Replace old paths with new in HTML/PHP file.
        print "Replacing all In : " + full_treeitem_filepath
        with open(full_treeitem_filepath, 'w') as html_file:
            # 
            file_as_string = file_as_string.replace('@ include', 'include')
            for old_string, new_string in replace_queue.iteritems():
                file_as_string = file_as_string.replace(old_string, new_string)
            html_file.write(file_as_string)
            html_file.close()
#        # Copy image files with new names to new location.
#        for source_filepath, destination_filepath in copy_queue.iteritems():
#            dstdir =  os.path.dirname(destination_filepath)
#            if not os.path.isdir(dstdir):
#                os.makedirs(dstdir)
#            shutil.copy(source_filepath, dstdir)

