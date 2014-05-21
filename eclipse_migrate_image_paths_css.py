#!/usr/bin/env python
# eclipse_migrate_image_paths_css.py
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
from eclipse_migration_tools import *
from optparse import OptionParser
import os
import re
from urlparse import urlparse

media_server_url = '//media.lib.unb.ca'
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

parser = OptionParser()
parser.add_option('-a', '--auto-process', dest='auto_process', default=False, help='Process without input.', action='store_true')
(options, args) = parser.parse_args()

# Open script used to copy migrated files out of the eclipse tree
#
script_file_handle = open("copyset-migrate-" + subdir_string.replace('/', '') + "-css-to-media.sh", "wb")
write_copy_script_intro(script_file_handle, subdir_string)

for parse_root, dirs, tree_files in os.walk(tree_to_walk):
    for cur_tree_file in tree_files:
        copy_queue = {}
        cur_tree_location = parse_root.replace(tree_to_walk, '')

        full_treeitem_filepath = os.path.join(parse_root, cur_tree_file)
        html_file = open(full_treeitem_filepath, 'r')
        file_as_string = unicode(html_file.read(), errors='ignore')
        html_file.close()

        raw_css_url_values = []
        raw_css_url_values.extend(re.findall(r"(url\(.*?\))", file_as_string, re.IGNORECASE | re.MULTILINE | re.DOTALL))

        if len(raw_css_url_values) > 0 :
            print "Operating on " + subdir_string + '/' + cur_tree_location + '/' + cur_tree_file + ":\n"
            for cur_raw_css_url_value in raw_css_url_values :
                cur_raw_css_url_value_orig = cur_raw_css_url_value
                cur_raw_css_url_value = cur_raw_css_url_value.replace("\r", " ").replace("\n", " ")

                if not '<?' in cur_raw_css_url_value and not '$' in cur_raw_css_url_value and not cur_raw_css_url_value.count('\\') > 3 and not 'file://' in cur_raw_css_url_value :
                    cur_css_url_value = cur_raw_css_url_value.replace('url("', '').replace("url('", '').replace('")', '').replace("')", '').replace('url(', '').replace(')', '')
                    if not cur_css_url_value.startswith(('http', '//')) or cur_css_url_value.startswith(on_eclipse_uri_prefixes):
                        if not cur_raw_css_url_value in replace_queue:
                            print "Replacing " + cur_raw_css_url_value

                            if options.auto_process is True:
                                new_filestring = media_server_url + guess_new_imagepath(
                                    cur_css_url_value,
                                    media_server_url,
                                    subdir_string + cur_tree_location
                                )
                            else:
                                new_filestring = read_input_prefill(
                                    'New img src (Enter nothing to skip) : ',
                                    media_server_url + guess_new_imagepath(
                                        cur_css_url_value,
                                        media_server_url,
                                        subdir_string + cur_tree_location
                                    )
                                )

                            if new_filestring is '':
                                replace_queue[cur_raw_css_url_value_orig] = ''
                            else :
                                replace_queue[cur_raw_css_url_value_orig] = str(
                                    cur_raw_css_url_value.replace(
                                        cur_css_url_value,
                                        new_filestring
                                    )
                                )

                            # Do not proceed any further if '' was received as new_filestring:
                            #
                            if not new_filestring is '':
                                if options.auto_process is True:
                                    if not cur_css_url_value.startswith('http://'):
                                        if cur_css_url_value.startswith('/'):
                                            copy_source = cur_css_url_value.replace('%20', ' ')
                                            copy_target = new_filestring.replace(media_server_url, '')
                                        else:
                                            original_source = subdir_string + cur_tree_location + '/' + cur_css_url_value
                                            copy_source = re.sub('/{2,}','',original_source.replace('/./','/')).replace('%20', ' ')
                                            copy_target = re.sub(
                                                '/{2,}',
                                                '/',
                                                subdir_string + '/' + guess_new_imagepath(
                                                    cur_css_url_value,
                                                    media_server_url,
                                                    cur_tree_location
                                                )
                                            )
                                    else:
                                        copy_source = urlparse(cur_css_url_value).path.replace('%20', ' ')
                                        copy_target = guess_new_imagepath(urlparse(cur_css_url_value).path,  media_server_url, '')
                                else:
                                    if not cur_css_url_value.startswith('http://'):
                                        if cur_css_url_value.startswith('/'):
                                            copy_source = read_input_prefill(
                                                'Original Source : ',
                                                cur_css_url_value.replace('%20', ' ')
                                            )
                                            copy_target = read_input_prefill(
                                                'New Dest : ',
                                                new_filestring.replace(media_server_url, '')
                                            )
                                        else:
                                            original_source = subdir_string + cur_tree_location + '/' + cur_css_url_value
                                            copy_source = read_input_prefill(
                                                'Original Source : ',
                                                re.sub('/{2,}','',original_source.replace('/./','/')).replace('%20', ' ')
                                            )
                                            copy_target = read_input_prefill(
                                                'New Dest : ',
                                                re.sub(
                                                    '/{2,}',
                                                    '/',
                                                    subdir_string + '/' + guess_new_imagepath(
                                                        cur_css_url_value,
                                                        media_server_url,
                                                        cur_tree_location
                                                    )
                                                )
                                            )
                                    else:
                                        copy_source = read_input_prefill(
                                            'Original Source : ',
                                            urlparse(cur_css_url_value).path.replace('%20', ' ')
                                        )
                                        copy_target = read_input_prefill(
                                            'New Dest : ',
                                            guess_new_imagepath(urlparse(cur_css_url_value).path,  media_server_url, '')
                                        )
                                copy_queue[copy_source] = copy_target

        write_tree_file_with_changes(file_as_string, replace_queue, full_treeitem_filepath)
        write_copy_queue_to_script(script_file_handle, copy_queue)

write_copy_script_outro(script_file_handle, subdir_string)
