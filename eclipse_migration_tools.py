import os
import re
import readline
import unicodedata


subdir_string = '/archives'
tree_to_walk = '/home/jsanford/gitDev/lib.unb.ca-webtree' + subdir_string

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
    image_path = image_path.replace('%20', '_')
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
    if image_path.startswith('/') :
        return slugify_path(unicode(image_path))
    if image_path.startswith('./') :
        image_path = image_path.replace('./', '')
    if './' in image_path or '../' in image_path:
        image_path = os.path.normpath(image_path)
    if subdir_slug in image_path:
        image_path = image_path.replace(subdir_slug, '')
    slugged_path = slugify_path(unicode(image_path))
    new_imagepath_guess = subdir_slug + '/' + slugged_path
    new_imagepath_guess = re.sub('(?<!http:)/{2,}', '/', new_imagepath_guess)
    return new_imagepath_guess

def write_copy_script_intro(script_file_handle, subdir_string, temp_filepath_on_eclipse = '/home/jsanford/copy-temp'):
    temp_dir_string = 'migrate' + subdir_string.replace('/', '') + '-img-to-media'
    script_file_handle.write("rm -rf {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))
    script_file_handle.write("rm -rf {0}/htdocs\n".format(temp_filepath_on_eclipse))
    script_file_handle.write("mkdir {0}/{1}\n".format(temp_filepath_on_eclipse,temp_dir_string))

def write_copy_queue_to_script(script_file_handle, copy_queue, temp_filepath_on_eclipse = '/home/jsanford/copy-temp'):
    temp_dir_string = 'migrate' + subdir_string.replace('/', '') + '-img-to-media'
    for copy_source, copy_target in copy_queue.items():
        if not copy_source is '' or not copy_target is '':
            script_file_handle.write("cd /www\n")
            script_file_handle.write("if [ -f \".{0}\" ]\n".format(copy_source))
            script_file_handle.write("then\n")
            script_file_handle.write("    cp --parents \".{0}\" \"{1}/{2}\"\n".format(copy_source, temp_filepath_on_eclipse,temp_dir_string))
            script_file_handle.write("    cd \"{0}/{1}\"\n".format(temp_filepath_on_eclipse,temp_dir_string))
            script_file_handle.write("    mkdir -p \".{0}\"\n".format(os.path.dirname(copy_target)))
            script_file_handle.write("    mv \".{0}\" \".{1}\"\n".format(copy_source, copy_target))
            script_file_handle.write("else\n")
            script_file_handle.write("    echo \".{0}\" >> missing_files_from_move.txt\n".format(copy_source))
            script_file_handle.write("fi\n")

def write_copy_script_outro(script_file_handle, subdir_string, temp_filepath_on_eclipse = '/home/jsanford/copy-temp'):
    temp_dir_string = 'migrate' + subdir_string.replace('/', '') + '-img-to-media'
    script_file_handle.write("find {0}/{1} -type d -depth -empty -exec rmdir \"{{}}\" \;\n".format(temp_filepath_on_eclipse,temp_dir_string))
    script_file_handle.write("cd {0}\n".format(temp_filepath_on_eclipse))
    script_file_handle.write("mv " + temp_dir_string + " htdocs\n")
    script_file_handle.write("tar cvzpf " + temp_filepath_on_eclipse + "/" + subdir_string.replace('/', '') + "-img-transfer.tar.gz htdocs\n")
    script_file_handle.write("scp " + temp_filepath_on_eclipse + "/" + subdir_string.replace('/', '') + "-img-transfer.tar.gz gorgon:/var/www/media.lib.unb.ca/\n")
    script_file_handle.close()

def write_tree_file_with_changes(file_as_string, replace_queue, full_treeitem_filepath):
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
