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
from bs4 import BeautifulSoup
from migration_tools_paths import *
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
        image_path = image_path.replace('http://lib.unb.ca', '')
        slugged_path = slugify_path(unicode(image_path))
        return slugged_path
    if image_path.startswith('http://www.lib.unb.ca/'):
        image_path = image_path.replace('http://www.lib.unb.ca', '')
        slugged_path = slugify_path(unicode(image_path))
        return slugged_path
    if image_path.startswith('http://dev.hil.unb.ca/'):
        image_path = image_path.replace('http://dev.hil.unb.ca', '')
        slugged_path = slugify_path(unicode(image_path))
        return slugged_path
    if image_path.startswith('/'):
        slugged_path = slugify_path(unicode(image_path))
        return slugged_path
    if image_path.startswith('./') :
        image_path = image_path.replace('./', '')
    if subdir_slug in image_path:
        image_path = image_path.replace(subdir_slug, '')
    slugged_path = slugify_path(unicode(image_path))
    new_imagepath_guess = subdir_slug + '/' + slugged_path
    new_imagepath_guess = re.sub('(?<!http:)/{2,}', '/', new_imagepath_guess)
    return new_imagepath_guess


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

script_file = open("copyset-migrate-" + subdir_string.replace('/', '') + "-css-files-to-media.sh", "wb")
temp_filepath_on_eclipse = '/tmp'
temp_dir_string = 'migrate' + subdir_string.replace('/', '') + '-css-to-media'
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
                                if not cur_css_url_value.startswith('http://'):
                                    if cur_css_url_value.startswith('/'):
                                        copy_source = read_input_prefill(
                                            'Original Source : ',
                                            cur_css_url_value
                                        )
                                        copy_target = read_input_prefill(
                                            'New Dest : ',
                                            new_filestring.replace(media_server_url, '')
                                        )
                                    else:
                                        original_source = subdir_string + cur_tree_location + '/' + cur_css_url_value
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
                                                    cur_css_url_value,
                                                    media_server_url,
                                                    cur_tree_location
                                                )
                                            )
                                        )
                                else:
                                    copy_source = read_input_prefill(
                                        'Original Source : ',
                                        urlparse(cur_css_url_value).path
                                    )
                                    copy_target = read_input_prefill(
                                        'New Dest : ',
                                        guess_new_imagepath(urlparse(cur_css_url_value).path,  media_server_url, '')
                                    )
                                copy_queue[copy_source] = copy_target

        # If there are changes needed, open and write the file.
        #
        file_as_string = file_as_string.decode('utf-8')
        file_needs_write = False
        for old_string, new_string in replace_queue.iteritems():
            if not new_string is '':
                if old_string in file_as_string:
                    print "Replacing contents in : " + full_treeitem_filepath
                    file_as_string = file_as_string.replace(old_string, new_string)
                    file_needs_write = True
        if file_needs_write:
            with open(full_treeitem_filepath, 'w') as html_file:
                html_file.write(file_as_string.encode('utf-8'))
                html_file.close()

        # Write out steps to copy binaries referenced in this file to a location for archiving.
        #
        for copy_source, copy_target in copy_queue.items():
            if not copy_source is '' or not copy_target is '':
                script_file.write("cd /www\n")
                script_file.write("if [ -f \".{0}\" ]\n".format(copy_source))
                script_file.write("then\n")
                script_file.write("    cp --parents .{0} {1}/{2}\n".format(copy_source, temp_filepath_on_eclipse,temp_dir_string))
                script_file.write("    cd {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))
                script_file.write("    mkdir -p .{0}\n".format(os.path.dirname(copy_target)))
                script_file.write("    mv .{0} .{1}\n".format(copy_source, copy_target))
                script_file.write("else\n")
                script_file.write("	echo \".{0}\" >> missing_files_from_move.txt\n".format(copy_source))
                script_file.write("fi\n")

# Write out steps to clean up temporary location, tar up contents, and copy the tarball to gorgon.
#
script_file.write("find {0}/{1} -type d -depth -empty -exec rmdir \"{{}}\" \;\n".format(temp_filepath_on_eclipse,temp_dir_string))
script_file.write("cd {0}\n".format(temp_filepath_on_eclipse))
script_file.write("mv " + temp_dir_string + " htdocs\n")
script_file.write("tar cvzpf /tmp/" + subdir_string.replace('/', '') + "-css-transfer.tar.gz htdocs\n")
script_file.write("scp /tmp/" + subdir_string.replace('/', '') + "-css-transfer.tar.gz gorgon:/var/www/media.lib.unb.ca/\n")
script_file.close()
