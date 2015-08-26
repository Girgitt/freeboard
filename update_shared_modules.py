#!/usr/bin/python
import platform
import subprocess
import os
import sys

arg_loaded = False
opt_loaded = False

try:
    import argparse
    arg_loaded = True
except:
    from optparse import OptionParser
    opt_loaded = True

__author__ = 'z.zasieczny@gmail.com'

is_windows = False
is_posix = False
SKIP_UPDATES = True
INCLUDE_UPDATES = False
SRC_REPO_PATH_FILE = "src_repo_path"
LOCAL_MODULES_UPDATE_SCRIPT_FILE = "update_shared_modules.py"

BRANCH = 'default'
BASE_DIR = os.getcwd()

checkout_dirs = [
    {'from': '../freeboard_plugins_girgitt', 'to': './freeboard_plugins', 'branch': 'master'}
]

print "checkout_dirs: %s" % str(checkout_dirs)


def get_array_from_cmd_str(cmd_str):
    cmd_str_parts = cmd_str.split(" ")
    return [str(cmd_part) for cmd_part in cmd_str_parts]


def run_command_str(command):
    #p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = subprocess.Popen(get_array_from_cmd_str(command),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    resp = {'out': p[0],
            'err': p[1]}
    return resp


def validate_file_exists_bool(file_path):
    try:
        with open(file_path):
            return True
    except IOError:
        pass
        #raise IOError("file: %s not found" % file_path)
    return False


def get_repo_type_from_url(url):
    if url[-4:] == '.git':
        return 'git'
    return 'hg'

print "preparing shared modules"
if platform.system().upper() == "LINUX":
    is_posix = True
    print "for POSIX"
elif platform.system().upper() == "WINDOWS":
    is_windows = True
    print "for WIN"


def update_modules_on_posix(skip_repo_pull_update=False, ssh_key_path=None):
    for chk_dir in checkout_dirs:
        os.chdir(BASE_DIR)
        dst_dir = chk_dir['to']
        src_dir = chk_dir['from']
        print "  > updating module %s" % src_dir
        os.chdir(src_dir)

        if not skip_repo_pull_update:
            fh_in = "./"+SRC_REPO_PATH_FILE

            with open(fh_in, 'r') as src_repo_path_file:
                src_repo_path = src_repo_path_file.readline()

            #cmd = "hg pull %s" % src_repo_path
            if get_repo_type_from_url(src_repo_path) == 'hg':
                cmd = "hg pull %s" % src_repo_path
            elif get_repo_type_from_url(src_repo_path) == 'git':
                cmd = "ssh-agent bash -c 'ssh-add %s; git pull'" % ssh_key_path

            print " >> pulling repo from: %s; cmd: '%s'" % (src_repo_path, cmd)
            cmd_result = run_command_str(cmd)
            err = cmd_result['err']
            out = cmd_result['out']
            if err != '':
                if 'Identity added' in err:
                     print "  > err: '%s'" % err
                else:
                    sys.exit("err: '%s'" % err)
            print "  > out: '%s'" % out

            if get_repo_type_from_url(src_repo_path) == 'hg':
                cmd = "hg update -C %s" % chk_dir['branch']
            elif get_repo_type_from_url(src_repo_path) == 'git':
                cmd = "ssh-agent bash -c 'ssh-add %s; git checkout %s'" % (ssh_key_path, chk_dir['branch'])

            print " >> updating repo to branch: %s; cmd: '%s'" % (chk_dir['branch'], cmd)
            cmd_result = run_command_str(cmd)
            err = cmd_result['err']
            out = cmd_result['out']
            if err != '':
                if 'Identity added' in err:
                     print "  > err: '%s'" % err
                else:
                    sys.exit("err: '%s'" % err)
            print "  > out: '%s'" % out
            print " << updating repo to branch: %s; cmd: '%s'" % (chk_dir['branch'], cmd)

            print " >> calling local shared modules update script if script exists"
            update_script_path = os.getcwd()+"/"+LOCAL_MODULES_UPDATE_SCRIPT_FILE
            if validate_file_exists_bool(update_script_path):
                err = run_command_str("python %s" % update_script_path)['err']
                if len(err) > 0:
                    sys.exit("local shared module update script failed with error: %s" % err)

            print " << calling local shared modules update script if script exists"

        print ">>> cd %s" % BASE_DIR
        os.chdir(BASE_DIR)
        if os.path.exists(chk_dir['to']):
            print " >> deleting module from %s" % (chk_dir['to'])
            cmd = "rm -rf %s" % (chk_dir['to'])
            print ">>> %s " % cmd
            cmd_result = run_command_str(cmd)
            err = cmd_result['err']
            out = cmd_result['out']
            if err != '':
                sys.exit("err: %s" % err)
            else:
                print "  > out: %s" % out
            print " << deleting module from %s to %s" % (chk_dir['from'], chk_dir['to'])

        print " >> copying module from %s to %s" % (chk_dir['from'], chk_dir['to'])
        print ">>> cd %s" % BASE_DIR
        os.chdir(BASE_DIR)
        if not os.path.exists(chk_dir['to']):
            cmd = "cp -r %s %s" % (chk_dir['from'], chk_dir['to'])
        else:
            cmd = "cp -r %s %s" % (chk_dir['from'], "/".join(chk_dir['to'].split("/")[:-1]))
        print ">>> %s " % cmd
        cmd_result = run_command_str(cmd)
        err = cmd_result['err']
        out = cmd_result['out']
        if err != '':
            sys.exit("err: %s" % err)
        else:
            print "  > out: %s" % out
        print " << copying module from %s to %s" % (chk_dir['from'], chk_dir['to'])

        print " >> removing vcs files form dir %s" % chk_dir['to']

        paths_to_remove = []
        if os.path.exists("%s/.hg" % chk_dir['to']):
            paths_to_remove.append("%s/.hg" % chk_dir['to'])
        if os.path.exists("%s/.git" % chk_dir['to']):
            paths_to_remove.append("%s/.git" % chk_dir['to'])

        for path in paths_to_remove:
            cmd = "rm -rf %s" % path

            print ">>> %s " % cmd
            cmd_result = run_command_str(cmd)
            err = cmd_result['err']
            out = cmd_result['out']
            if err != '':
                sys.exit("err: %s" % err)
            else:
                print "  > out: %s" % out

        print " << removing vcs files form dir %s" % chk_dir['to']

        print " >> removing unit test files from module %s" % chk_dir['to']
        cmd = "rm -rf %s/test_*" % chk_dir['to']
        print ">>> %s " % cmd
        cmd_result = run_command_str(cmd)
        err = cmd_result['err']
        out = cmd_result['out']
        if err != '':
            sys.exit("err: %s" % err)
        else:
            print "  > out: %s" % out
        print " << removing removing unit test files from module %s" % chk_dir['to']

        print "  < updating module %s" % dst_dir


def main(skip_repo_update=False, ssh_key_path=None):

    if is_posix or is_windows:
        update_modules_on_posix(skip_repo_pull_update=skip_repo_update, ssh_key_path=ssh_key_path)


if __name__ == "__main__":
    parser = None
    if arg_loaded:
        parser = argparse.ArgumentParser()

        parser.add_argument("-k", "--ssh-key", dest="ssh_key_path",
                          help="public ssh key used to authenticate over ssh when git is used", metavar="SSH_KEY_FILE")
        parser.add_argument("-s", "--skip-repo-updates",
                          action="store_true", dest="skip_repo_update", default=False,
                          help="skip updating repositories; use on CI when repos are updated anyway")
        options = parser.parse_args()

    elif opt_loaded:
        parser = OptionParser()
        parser.add_option("-k", "--ssh-key", dest="ssh_key_path",
                          help="public ssh key used to authenticate over ssh when git is used", metavar="SSH_KEY_FILE")
        parser.add_option("-s", "--skip-repo-updates",
                          action="store_true", dest="skip_repo_update", default=False,
                          help="skip updating repositories; use on CI when repos are updated anyway")

        (options, args) = parser.parse_args()


    main( **vars( options ) )