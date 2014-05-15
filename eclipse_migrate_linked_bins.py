#!/usr/bin/env python
# eclipse_migrate_linked_bins.py
#
# Migrate linked binaries in webserver project directories.
#
# This script performs 2 tasks:
# 1) Migrates linked binaries from their current position mixed in with
#    code to a new location, sanitizing names of offending files in the
#    process.
# 2) Updates the references to that file within the HTML/PHP to reflect
#    the new location and filenames.
#
from bs4 import BeautifulSoup
import os
import re
import readline
import unicodedata
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
    if image_path.startswith('/'):
        slugged_path = slugify_path(unicode(image_path))
        return slugged_path
    if image_path.startswith('./') :
        image_path = re.sub('./', '', image_path)
    if subdir_slug in image_path:
        image_path = re.sub(subdir_slug, '', image_path)
    slugged_path = slugify_path(unicode(image_path))
    new_imagepath_guess = subdir_slug + '/' + slugged_path
    new_imagepath_guess = re.sub('(?<!http:)/{2,}', '/', new_imagepath_guess)
    return new_imagepath_guess


tree_to_walk = '/home/jsanford/gitDev/lib.unb.ca-webtree/commons'
subdir_string = '/commons'
media_server_url = '//media.lib.unb.ca'

media_bins_suffixes = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".tif",
    ".tiff",
    ".psd",
    ".bmp",
    ".mp3",
    ".mp4",
    ".wav",
    ".mov",
    ".avi",
    ".wmv",
    ".swf",
    ".fla",
    ".ra",
    ".ram",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
)

on_eclipse_uri_prefixes = (
    'http://lib.unb.ca/',
    'https://lib.unb.ca/',
    'http://www.lib.unb.ca/',
    'https://www.lib.unb.ca/',
    'http://dev.hil.unb.ca/',
    'https://dev.hil.unb.ca/',
    'http://eclipse.hil.unb.ca/',
    'https://eclipse.hil.unb.ca/',
    'http://www.dev.hil.unb.ca/',
    'https://www.dev.hil.unb.ca/',
    'http://www.eclipse.hil.unb.ca/',
    'https://www.eclipse.hil.unb.ca/',
)


replace_queue = {}

script_file = open("copyset-migrate" + subdir_string.replace('/', '') + "-bins-to-media.sh", "wb")
temp_filepath_on_eclipse = '/tmp'
temp_dir_string = 'migrate' + subdir_string.replace('/', '') + '-bins-to-media'
script_file.write("rm -rf {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))
script_file.write("rm -rf {0}/htdocs\n".format(temp_filepath_on_eclipse))
script_file.write("mkdir {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))

for parse_root, dirs, tree_files in os.walk(tree_to_walk):
    for cur_tree_file in tree_files:
        copy_queue = {}
        cur_tree_location = parse_root.replace(tree_to_walk, '')

        full_treeitem_filepath = os.path.join(parse_root, cur_tree_file)
        html_file = open(full_treeitem_filepath, 'r')
        file_as_string = unicode(html_file.read(), errors='ignore')
        html_file.close()

        raw_a_tag_values = []
        raw_a_tag_values.extend(re.findall(r"(\<a .*?\>)", file_as_string))

        if len(raw_a_tag_values) > 0 :
            print "Operating on " + subdir_string + '/' + cur_tree_location + '/' + cur_tree_file + ":\n"
            for cur_raw_a_tag_value in raw_a_tag_values :
                print "Testing " + cur_raw_a_tag_value
                cur_a_href_value = BeautifulSoup(cur_raw_a_tag_value).a['href']
                print "Link " + cur_a_href_value
                if cur_a_href_value.lower().endswith(media_bins_suffixes):
                    if not cur_a_href_value.startswith('http') or cur_a_href_value.startswith(on_eclipse_uri_prefixes):
                        print "Replacing " + cur_raw_a_tag_value
                        new_filestring = read_input_prefill(
                            'New img src : ',
                            media_server_url + guess_new_imagepath(
                                cur_a_href_value,
                                media_server_url,
                                subdir_string + cur_tree_location
                            )
                        )
                        replace_queue[cur_raw_a_tag_value] = str(
                            cur_raw_a_tag_value.replace(
                                cur_a_href_value,
                                new_filestring
                            )
                        )

                        if not cur_a_href_value.startswith('http://'):
                            if cur_a_href_value.startswith('/'):
                                copy_source = read_input_prefill(
                                    'Original Source : ',
                                    cur_a_href_value
                                )
                                copy_target = read_input_prefill(
                                    'New Dest : ',
                                    new_filestring.replace(media_server_url, '')
                                )
                            else:
                                original_source = subdir_string + cur_tree_location + '/' + cur_a_href_value
                                copy_source = read_input_prefill(
                                    'Original Source : ',
                                    re.sub('/{2,}','',original_source.replace('/./','/'))
                                )
                                copy_target = read_input_prefill(
                                    'New Dest : ',
                                    re.sub(
                                        '/{2,}',
                                        '/',
                                        subdir_string + '/' + guess_new_imagepath(
                                            cur_a_href_value,
                                            media_server_url,
                                            cur_tree_location
                                        )
                                    )
                                )
                        else:
                            copy_source = read_input_prefill(
                                'Original Source : ',
                                urlparse(cur_a_href_value).path
                            )
                            copy_target = read_input_prefill(
                                'New Dest : ',
                                guess_new_imagepath(urlparse(cur_a_href_value).path,  media_server_url, '')
                            )
                        copy_queue[copy_source] = copy_target

        # Replace old paths with new in HTML/PHP file.
        file_as_string = file_as_string.decode('utf-8')
        print "Replacing all In : " + full_treeitem_filepath
        with open(full_treeitem_filepath, 'w') as html_file:
            for old_string, new_string in replace_queue.iteritems():
                if not new_string is '' or not old_string is '':
                    file_as_string = file_as_string.replace(old_string, new_string)
            html_file.write(file_as_string.encode('utf-8'))
            html_file.close()

        for copy_source, copy_target in copy_queue.items():
            if not copy_source is '' or not copy_target is '':
                script_file.write("cd /www\n")
                script_file.write("cp --parents .{0} {1}/{2}\n".format(copy_source, temp_filepath_on_eclipse,temp_dir_string))
                script_file.write("cd {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))
                script_file.write("mkdir -p .{0}\n".format(os.path.dirname(copy_target)))
                script_file.write("mv .{0} .{1}\n".format(copy_source, copy_target))

script_file.write("find {0}/{1} -type d -depth -empty -exec rmdir \"{{}}\" \;\n".format(temp_filepath_on_eclipse,temp_dir_string))
script_file.write("cd {0}\n".format(temp_filepath_on_eclipse))
script_file.write("mv " + temp_dir_string + " htdocs\n")
script_file.write("tar cvzpf /tmp/" + subdir_string.replace('/', '') + "-bins-transfer.tar.gz htdocs\n")
script_file.write("scp /tmp/" + subdir_string.replace('/', '') + "-bins-transfer.tar.gz gorgon:/var/www/media.lib.unb.ca/\n")
script_file.close()