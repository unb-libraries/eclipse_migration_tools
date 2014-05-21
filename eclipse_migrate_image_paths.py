#!/usr/bin/env python
# eclipse_migrate_image_paths.py
#
# migrate images in webserver project directories.
#
# this script performs 2 tasks:
# 1) migrates image binaries from their current position mixed in with
#    code to a new location, sanitizing names of offending files in the
#    process.
# 2) updates the references to that file within the html/php to reflect
#    the new location and filenames.
#
from bs4 import BeautifulSoup
from eclipse_migration_tools import *
from optparse import OptionParser
import os
import re
from urlparse import urlparse

media_server_url = '//media.lib.unb.ca'
tag_uri_tuples_to_ignore = (
    '//',
    'http://maps.google.com',
    "'http://blogs.unb.ca/iss",
    "http://www.unb.ca/"
)
replace_queue = {}

parser = OptionParser()
parser.add_option('-a', '--auto-process', dest='auto_process', default=False, help='Process without input.', action='store_true')
(options, args) = parser.parse_args()

# Open script used to copy migrated files out of the eclipse tree
#
script_file_handle = open("copyset-migrate-" + subdir_string.replace('/', '') + "-img-to-media.sh", "wb")
write_copy_script_intro(script_file_handle, subdir_string)

# Walk the Tree
#
for parse_root, dirs, tree_files in os.walk(tree_to_walk):
    for cur_tree_file in tree_files:
        copy_queue = {}
        cur_tree_location = parse_root.replace(tree_to_walk, '')

        full_treeitem_filepath = os.path.join(parse_root, cur_tree_file)
        html_file = open(full_treeitem_filepath, 'r')
        file_as_string = unicode(html_file.read(), errors='ignore')
        html_file.close()

        raw_img_src_values = []
        raw_img_src_values.extend(re.findall(r"\<img.*?\>", file_as_string, re.IGNORECASE | re.MULTILINE | re.DOTALL))

        if len(raw_img_src_values) > 0 :
            print "Operating on " + subdir_string + '/' + cur_tree_location + '/' + cur_tree_file + ":\n"
            for cur_raw_img_src_value in raw_img_src_values :
                cur_raw_img_src_value_orig = cur_raw_img_src_value
                cur_raw_img_src_value = cur_raw_img_src_value.replace("\r", " ").replace("\n", " ")

                if not '<?' in cur_raw_img_src_value and not '$' in cur_raw_img_src_value and not cur_raw_img_src_value.count('\\') > 3 and not 'file://' in cur_raw_img_src_value :
                    src_image_tag = BeautifulSoup(cur_raw_img_src_value).img
                    if not src_image_tag['src'].startswith(tag_uri_tuples_to_ignore):
                        if not cur_raw_img_src_value in replace_queue :
                            print "replacing " + cur_raw_img_src_value

                            if options.auto_process is True:
                                new_filestring = media_server_url + guess_new_imagepath(
                                    src_image_tag['src'],
                                    media_server_url,
                                    subdir_string + cur_tree_location
                                )
                            else:
                                new_filestring = read_input_prefill(
                                    'New img src (enter nothing to skip) : ',
                                    media_server_url + guess_new_imagepath(
                                        src_image_tag['src'],
                                        media_server_url,
                                        subdir_string + cur_tree_location
                                    )
                                )

                            if new_filestring is '':
                                replace_queue[cur_raw_img_src_value_orig] = ''
                            else :
                                replace_queue[cur_raw_img_src_value_orig] = str(
                                    cur_raw_img_src_value.replace(
                                        src_image_tag['src'],
                                        new_filestring
                                    )
                                )

                            # do not proceed any further if '' was received as new_filestring:
                            #
                            if not new_filestring is '':
                                src_image_path = src_image_tag['src']
                                if subdir_string in src_image_path :
                                    src_image_path = re.sub(subdir_string, '', src_image_path)
                                if subdir_string in new_filestring :
                                    new_filestring = re.sub(subdir_string, '', new_filestring)

                                if options.auto_process is True:
                                    if src_image_tag['src'].startswith('/'):
                                        copy_source = src_image_tag['src'].replace('./','').replace('%20', ' ')
                                        copy_target = guess_new_imagepath(
                                            src_image_tag['src'],
                                            media_server_url,
                                            subdir_string + cur_tree_location
                                        )
                                    elif not src_image_path.startswith('http://'):
                                        original_source = subdir_string + cur_tree_location + '/' + src_image_path
                                        copy_source = re.sub('/{2,}','',original_source.replace('/./','/')).replace('%20', ' ')
                                        copy_target = re.sub(
                                            '/{2,}',
                                            '/',
                                            subdir_string + '/' + guess_new_imagepath(
                                                src_image_path,
                                                media_server_url,
                                                cur_tree_location
                                            )
                                        )
                                    else:
                                        copy_source = urlparse(src_image_path).path.replace('%20', ' ')
                                        copy_target = urlparse(src_image_path).path
                                else:
                                    src_image_path = src_image_tag['src']
                                    if subdir_string in src_image_path :
                                        src_image_path = re.sub(subdir_string, '', src_image_path)
                                    if subdir_string in new_filestring :
                                        new_filestring = re.sub(subdir_string, '', new_filestring)

                                    if src_image_tag['src'].startswith('/'):
                                        copy_source = read_input_prefill(
                                            'Original source : ',
                                            src_image_tag['src'].replace('./','').replace('%20', ' ')
                                        )
                                        copy_target = read_input_prefill(
                                            'New dest : ',
                                            guess_new_imagepath(
                                                src_image_tag['src'],
                                                media_server_url,
                                                subdir_string + cur_tree_location
                                            )
                                        )
                                    elif not src_image_path.startswith('http://'):
                                        original_source = subdir_string + cur_tree_location + '/' + src_image_path
                                        copy_source = read_input_prefill(
                                            'Original source : ',
                                            re.sub('/{2,}','',original_source.replace('/./','/')).replace('%20', ' ')
                                        )
                                        copy_target = read_input_prefill(
                                            'New dest : ',
                                            re.sub(
                                                '/{2,}',
                                                '/',
                                                subdir_string + '/' + guess_new_imagepath(
                                                    src_image_path,
                                                    media_server_url,
                                                    cur_tree_location
                                                )
                                            )
                                        )
                                    else:
                                        copy_source = read_input_prefill(
                                            'Original source : ',
                                            urlparse(src_image_path).path.replace('%20', ' ')
                                        )
                                        copy_target = read_input_prefill(
                                            'New dest : ',
                                            guess_new_imagepath(urlparse(src_image_path).path,  media_server_url, '')
                                        )
                                copy_queue[copy_source] = copy_target

        write_tree_file_with_changes(file_as_string, replace_queue, full_treeitem_filepath)
        write_copy_queue_to_script(script_file_handle, copy_queue)

write_copy_script_outro(script_file_handle, subdir_string)