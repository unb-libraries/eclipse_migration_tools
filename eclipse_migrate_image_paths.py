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
import tempfile
from urlparse import urlparse

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
    Guess at the desired 'new' path for image binaries, based on convoluted mess.
    """
    if image_path.startswith('http://lib.unb.ca/'):
        image_path = re.sub('http://lib.unb.ca', '', image_path)
        slugged_path = slugify_path(unicode(image_path))
        return slugged_path
    if image_path.startswith('http://dev.hil.unb.ca/'):
        image_path = re.sub('http://dev.hil.unb.ca', '', image_path)
        slugged_path = slugify_path(unicode(image_path))
        return slugged_path
    if image_path.startswith('./') :
        image_path = re.sub('./', '', image_path)
    if subdir_slug in image_path :
        image_path = re.sub(subdir_slug, '', image_path)
    slugged_path = slugify_path(unicode(image_path))
    new_imagepath_guess = subdir_slug + '/' + slugged_path
    new_imagepath_guess = re.sub('(?<!http:)/{2,}', '/', new_imagepath_guess)
    return new_imagepath_guess


tree_to_walk = '/home/jsanford/gitDev/lib.unb.ca-webtree/asin'
subdir_string = '/asin'
media_server_url = '//media.lib.unb.ca'

replace_queue = {}

script_file = open("copyset-migrate-to-media.sh", "wb")
temp_filepath_on_eclipse = '/tmp'
temp_dir_string = 'migrate-to-media'
script_file.write("rm -rf {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))
script_file.write("rm -rf {0}/htdocs\n".format(temp_filepath_on_eclipse))
script_file.write("mkdir {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))
script_file.write("cd /www\n")

for parse_root, dirs, tree_files in os.walk(tree_to_walk):
    for cur_tree_file in tree_files:
        copy_queue = {}
        # Get current spot in tree
        cur_tree_location = parse_root.replace(tree_to_walk, '')

        full_treeitem_filepath = os.path.join(parse_root, cur_tree_file)
        html_file = open(full_treeitem_filepath, 'r')
        file_as_string = html_file.read()
        html_file.close()


	img_src_values = set()
	# CSS Matching
	img_src_values.update(re.findall('url\(([^)]+)\)',file_as_string))

        # Extract img src values from HTML
        tree_file_soup = BeautifulSoup(file_as_string)
        img_src_values.update([image["src"] for image in tree_file_soup.findAll("img")])
        print img_src_values
        if len(img_src_values) > 0 :
            print "Operating on " + cur_tree_file + ":\n"
            for src_image_path in img_src_values :
                if not src_image_path.startswith('//media.lib.unb.ca'):
                    if not src_image_path in replace_queue :
                        print "Replacing " + src_image_path
                        new_filestring = read_input_prefill('New img src : ',
                                                            media_server_url + guess_new_imagepath(src_image_path,
                                                                                media_server_url,
                                                                                subdir_string + cur_tree_location)
                                                            )
                        replace_queue[src_image_path] = new_filestring

                        if subdir_string in src_image_path :
                            src_image_path = re.sub(subdir_string, '', src_image_path)
                        if subdir_string in new_filestring :
                            new_filestring = re.sub(subdir_string, '', new_filestring)


                        if not src_image_path.startswith('http://'):
                            copy_source = read_input_prefill('Original Source : ',
                                                             re.sub('/{2,}',
                                                                    '/',
                                                                    subdir_string + cur_tree_location +
                                                                    '/' +
                                                                    src_image_path
                                                                    )
                                                             )
                            copy_target = read_input_prefill('New Dest : ',
                                                             re.sub('/{2,}',
                                                                    '/',
                                                                    subdir_string +
                                                                    '/' +
                                                                           str(new_filestring)
                                                                    )
                                                             )
                        else :
                            copy_source = read_input_prefill('Original Source : ',
                                                                    urlparse(src_image_path).path
                                                             )
                            copy_target = read_input_prefill('New Dest : ',
                                                                    guess_new_imagepath(urlparse(src_image_path).path,  media_server_url, '')
                                                             )
                        copy_queue[copy_source] = copy_target

        # Replace old paths with new in HTML/PHP file.
        print "Replacing all In : " + full_treeitem_filepath
        with open(full_treeitem_filepath, 'w') as html_file:
            for old_string, new_string in replace_queue.iteritems():
                file_as_string = file_as_string.replace(old_string, new_string)
            html_file.write(file_as_string)
            html_file.close()

        for copy_source, copy_target in copy_queue.items():
            print copy_source
            script_file.write("cp --parents .{0} {1}/{2}\n".format(copy_source, temp_filepath_on_eclipse,temp_dir_string))
            script_file.write("cd {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))
            script_file.write("mkdir -p .{0}\n".format(os.path.dirname(copy_target)))
            script_file.write("mv .{0} .{1}\n".format(copy_source, copy_target))


script_file.write("find {0}/{1} -type d -depth -empty -exec rmdir \"{{}}\" \;\n".format(temp_filepath_on_eclipse,temp_dir_string))
script_file.write("cd {0}\n".format(temp_filepath_on_eclipse))
script_file.write("mv migrate-to-media htdocs\n")
script_file.write("tar cvzpf /tmp/media-transfer.tar.gz htdocs")
script_file.close()
