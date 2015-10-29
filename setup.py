#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup.py
# Copyright (C) 2013 LEAP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Setup file for bitmask.
"""
from __future__ import print_function

import hashlib
import sys
import os
import re
import sys

if not sys.version_info[0] == 2:
    print("[ERROR] Sorry, Python 3 is not supported (yet). "
          "Try running with python2: python2 setup.py ...")
    exit()

try:
    from setuptools import setup, find_packages
except ImportError:
    from pkg import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup, find_packages

from pkg import utils

import versioneer
versioneer.versionfile_source = 'src/leap/bitmask/_version.py'
versioneer.versionfile_build = 'leap/bitmask/_version.py'
versioneer.tag_prefix = ''  # tags are like 1.2.0
versioneer.parentdir_prefix = 'leap.bitmask-'


# The following import avoids the premature unloading of the `util` submodule
# when running tests, which would cause an error when nose finishes tests and
# calls the exit function of the multiprocessing module.
from multiprocessing import util
assert(util)

setup_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(setup_root, "src"))

trove_classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: X11 Applications :: Qt",
    "Intended Audience :: End Users/Desktop",
    ("License :: OSI Approved :: GNU General "
     "Public License v3 or later (GPLv3+)"),
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Topic :: Security",
    'Topic :: Security :: Cryptography',
    "Topic :: Communications",
    'Topic :: Communications :: Email',
    'Topic :: Communications :: Email :: Post-Office :: IMAP',
    'Topic :: Internet',
    "Topic :: Utilities",
]

DOWNLOAD_BASE = ('https://github.com/leapcode/bitmask_client/'
                 'archive/%s.tar.gz')
_versions = versioneer.get_versions()
VERSION = _versions['version']
VERSION_FULL = _versions['full']
DOWNLOAD_URL = ""

# get the short version for the download url
_version_short = re.findall('\d+\.\d+\.\d+', VERSION)
if len(_version_short) > 0:
    VERSION_SHORT = _version_short[0]
    DOWNLOAD_URL = DOWNLOAD_BASE % VERSION_SHORT

cmdclass = versioneer.get_cmdclass()


from setuptools import Command


class freeze_debianver(Command):

    """
    Freezes the version in a debian branch.
    To be used after merging the development branch onto the debian one.
    """
    user_options = []
    template = r"""
# This file was generated by the `freeze_debianver` command in setup.py
# Using 'versioneer.py' (0.7+) from
# revision-control system data, or from the parent directory name of an
# unpacked source archive. Distribution tarballs contain a pre-generated copy
# of this file.

version_version = '{version}'
version_full = '{version_full}'
"""
    templatefun = r"""

def get_versions(default={}, verbose=False):
        return {'version': version_version, 'full': version_full}
"""

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        proceed = str(raw_input(
            "This will overwrite the file _version.py. Continue? [y/N] "))
        if proceed != "y":
            print("He. You scared. Aborting.")
            return
        subst_template = self.template.format(
            version=VERSION_SHORT,
            version_full=VERSION_FULL) + self.templatefun
        with open(versioneer.versionfile_source, 'w') as f:
            f.write(subst_template)


def freeze_pkg_ver(path, version_short, version_full):
    """
    Freeze the _version in other modules, used during the gathering of
    all the leap modules in the sumo tarball.
    """
    subst_template = freeze_debianver.template.format(
        version=version_short,
        version_full=version_full) + freeze_debianver.templatefun
    with open(path, 'w') as f:
        f.write(subst_template)


if sys.argv[:1] == '--sumo':
    IS_SUMO = True
else:
    IS_SUMO = False

cmdclass["freeze_debianver"] = freeze_debianver
parsed_reqs = utils.parse_requirements()

if utils.is_develop_mode() or IS_SUMO:
    print("")
    print ("[WARNING] Skipping leap-specific dependencies "
           "because development mode is detected.")
    print ("[WARNING] You can install "
           "the latest published versions with "
           "'pip install -r pkg/requirements-leap.pip'")
    print ("[WARNING] Or you can instead do 'python setup.py develop' "
           "from the parent folder of each one of them.")
    print("")
else:
    parsed_reqs += utils.parse_requirements(
        reqfiles=["pkg/requirements-leap.pip"])


leap_launcher = 'bitmask=leap.bitmask.app:start_app'

from setuptools.command.develop import develop as _develop


def copy_reqs(path, withsrc=False):
    # add a copy of the processed requirements to the package
    _reqpath = ('leap', 'bitmask', 'util', 'reqs.txt')
    if withsrc:
        reqsfile = os.path.join(path, 'src', *_reqpath)
    else:
        reqsfile = os.path.join(path, *_reqpath)
    print("UPDATING %s" % reqsfile)
    if os.path.isfile(reqsfile):
        os.unlink(reqsfile)
    with open(reqsfile, "w") as f:
        f.write('\n'.join(parsed_reqs))


class cmd_develop(_develop):

    def run(self):
        # versioneer:
        versions = versioneer.get_versions(verbose=True)
        self._versioneer_generated_versions = versions
        # unless we update this, the command will keep using the old version
        self.distribution.metadata.version = versions["version"]

        _develop.run(self)
        copy_reqs(self.egg_path)

cmdclass["develop"] = cmd_develop


class cmd_binary_hash(Command):

    """
    Update the _binaries.py file with hashes for the different helpers.
    This is used from within the bundle.
    """

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self, *args):

        OPENVPN_BIN = os.environ.get('OPENVPN_BIN', None)
        BITMASK_ROOT = os.environ.get('BITMASK_ROOT', None)

        def exit():
            print("Please set environment variables "
                  "OPENVPN_BIN and BITMASK_ROOT pointing to the right path "
                  "to use this command")
            sys.exit(1)

        bin_paths = OPENVPN_BIN, BITMASK_ROOT
        if not all(bin_paths):
            exit()

        if not all(map(os.path.isfile, bin_paths)):
            exit()

        openvpn_bin_hash, bitmask_root_hash = map(
            lambda path: hashlib.sha256(open(path).read()).hexdigest(),
            bin_paths)

        template = r"""
# Hashes for binaries used in Bitmask Bundle.
# This file has been automatically generated by `setup.py hash_binaries`
# DO NOT modify it manually.

OPENVPN_BIN = "{openvpn}"
BITMASK_ROOT = "{bitmask}"
"""
        subst_template = template.format(
            openvpn=openvpn_bin_hash,
            bitmask=bitmask_root_hash)

        bin_hash_path = os.path.join('src', 'leap', 'bitmask', '_binaries.py')
        with open(bin_hash_path, 'w') as f:
            f.write(subst_template)
        print("Binaries hash file %s has been updated!" % (bin_hash_path,))


cmdclass["hash_binaries"] = cmd_binary_hash


# next two classes need to augment the versioneer modified ones

versioneer_build = cmdclass['build']
versioneer_sdist = cmdclass['sdist']


class cmd_build(versioneer_build):

    def run(self):
        versioneer_build.run(self)
        copy_reqs(self.build_lib)



class cmd_sdist(versioneer_sdist):

    user_options = versioneer_sdist.user_options + \
        [('sumo', 's',
          "create a 'sumo' sdist which includes the contents of all "
          "the leap.* packages")
         ]
    boolean_options = ['sumo']
    leap_sumo_packages = ['soledad.common', 'soledad.client',
                          'keymanager', 'mail', 'common']

    def initialize_options(self):
        versioneer_sdist.initialize_options(self)
        self.sumo = False

    def run(self):
        return versioneer_sdist.run(self)

    def make_release_tree(self, base_dir, files):
        versioneer_sdist.make_release_tree(self, base_dir, files)
        # We need to copy the requirements to the specified path
        # so that the client has a copy to do the startup checks.
        copy_reqs(base_dir, withsrc=True)
        with open(os.path.join(base_dir,
                               'src', 'leap', '__init__.py'),
                  'w') as nuke_top_init:
            nuke_top_init.write('')
        with open(os.path.join(base_dir,
                               'src', 'leap', 'soledad', '__init__.py'),
                  'w') as nuke_soledad_ns:
            nuke_soledad_ns.write('')

    def make_distribution(self):
        # add our extra files to the list just before building the
        # tarball/zipfile. We override make_distribution() instead of run()
        # because setuptools.command.sdist.run() does not lend itself to
        # easy/robust subclassing (the code we need to add goes right smack
        # in the middle of a 12-line method). If this were the distutils
        # version, we'd override get_file_list().

        if self.sumo:
            # If '--sumo' was specified, include all the leap.* in the sdist.
            vdict = _get_leap_versions()
            vdict['soledad.common'] = vdict['soledad']
            vdict['soledad.client'] = vdict['soledad']
            import importlib
            for module in self.leap_sumo_packages:
                full_module = "leap." + module
                importlib.import_module(full_module)
                src_path = "src/leap/" + _fix_namespace(module)
                imported_module = importlib.sys.modules[full_module]
                copy_recursively(
                    imported_module.__path__[0] + "/",
                    src_path)
                all_module_files = list_recursively(src_path)
                self.filelist.extend(all_module_files)
                module_ver = vdict[module]
                freeze_pkg_ver(
                    src_path + "/_version.py",
                    module_ver, "%s-sumo" % module_ver)
            freeze_pkg_ver(
                "src/leap/bitmask/_version.py",
                VERSION, "%s-sumo" % VERSION)

            # In addition, we want the tarball/zipfile to have -SUMO in the
            # name, and the unpacked directory to have -SUMO too. The easiest
            # way to do this is to patch self.distribution and override the
            # get_fullname() method. (an alternative is to modify
            # self.distribution.metadata.version, but that also affects the
            # contents of PKG-INFO).
            fullname = self.distribution.get_fullname()

            def get_fullname():
                return fullname + "-SUMO"
            self.distribution.get_fullname = get_fullname

        try:
            old_mask = os.umask(int("022", 8))
            return versioneer_sdist.make_distribution(self)
        finally:
            os.umask(old_mask)
            for module in self.leap_sumo_packages:
                # check, just in case...
                if module and module != "bitmask":
                    shutil.rmtree("src/leap/" + _fix_namespace(module))


import shutil
import glob


def _get_leap_versions():
    versions = {}
    with open("pkg/leap_versions.txt") as vf:
        lines = vf.readlines()
    for line in lines:
        pkg, ver = line.split('\t')
        versions[pkg.strip().replace('leap_', '')] = ver.strip()
    return versions


def _fix_namespace(path):
    if path in ('soledad.common', 'soledad.client'):
        return path.replace('.', '/')
    return path


_ignore_files = ('*.pyc', '_trial*', '*.swp', '.*', 'cert', 'test*')
_ignore_dirs = ('tests', '_trial*', 'test*')
_ignore_paths = _ignore_files + _ignore_dirs

is_excluded_path = lambda path: any(
    map(lambda pattern: glob.fnmatch.fnmatch(path, pattern),
        _ignore_paths))


def _should_exclude(path):
    folder, f = os.path.split(path)
    if is_excluded_path(f):
        return True
    upper, leaf = os.path.split(folder)
    if is_excluded_path(leaf):
        return True
    return False


def list_recursively(root_dir):
    file_list = []
    for root, sub_dirs, files in os.walk(root_dir):
        for f in files:
            is_excluded = _should_exclude(f)
            if not is_excluded:
                file_list.append(os.path.join(root, f))
    return file_list


def _mkdir_recursively(path):
    sub_path = os.path.dirname(path)
    if not os.path.exists(sub_path):
        _mkdir_recursively(sub_path)
    if not os.path.exists(path):
        os.mkdir(path)


def copy_recursively(source_folder, destination_folder):

    if not os.path.exists(destination_folder):
        _mkdir_recursively(destination_folder)

    for root, dirs, files in os.walk(source_folder):
        if _should_exclude(root):
            continue
        for item in files:
            if _should_exclude(item):
                continue
            src_path = os.path.join(root, item)
            dst_path = os.path.join(
                destination_folder, src_path.replace(source_folder, ""))
            if _should_exclude(dst_path):
                continue
            if os.path.exists(dst_path):
                if os.stat(src_path).st_mtime > os.stat(dst_path).st_mtime:
                    shutil.copy2(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        for item in dirs:
            if _should_exclude(item):
                continue
            src_path = os.path.join(root, item)
            dst_path = os.path.join(
                destination_folder, src_path.replace(source_folder, ""))
            if _should_exclude(dst_path):
                continue
            if not os.path.exists(dst_path):
                os.mkdir(dst_path)

cmdclass["build"] = cmd_build
cmdclass["sdist"] = cmd_sdist

import platform
_system = platform.system()
IS_LINUX = _system == "Linux"
IS_MAC = _system == "Darwin"

data_files = []


if IS_LINUX:
    # XXX use check_for_permissions to install data
    # globally. Or make specific install command. See #3805
    isset = lambda var: os.environ.get(var, None)
    if isset('VIRTUAL_ENV') or isset('LEAP_SKIP_INIT'):
        data_files = None
    else:
        data_files = [
            ("share/polkit-1/actions",
                ["pkg/linux/polkit/se.leap.bitmask.policy"]),
            ("/usr/sbin",
                ["pkg/linux/bitmask-root"]),
        ]

extra_options = {}

setup(
    name="leap.bitmask",
    package_dir={"": "src"},
    version=VERSION,
    cmdclass=cmdclass,
    description=("The Internet Encryption Toolkit: "
                 "Encrypted Internet Proxy and Encrypted Mail."),
    long_description=open('README.rst').read() + '\n\n\n' +
    open('CHANGELOG.rst').read(),
    classifiers=trove_classifiers,
    install_requires=parsed_reqs,
    test_suite='nose.collector',
    tests_require=utils.parse_requirements(
        reqfiles=['pkg/requirements-testing.pip']),
    keywords=('Bitmask, LEAP, client, qt, encryption, '
              'proxy, openvpn, imap, smtp, gnupg'),
    author='The LEAP Encryption Access Project',
    author_email='info@leap.se',
    maintainer='Kali Kaneko',
    maintainer_email='kali@leap.se',
    url='https://bitmask.net',
    download_url=DOWNLOAD_URL,
    license='GPL-3+',
    packages=find_packages(
        'src',
        exclude=['ez_setup', 'setup', 'examples', 'tests']),
    namespace_packages=["leap"],
    package_data={'': ['util/*.txt', '*.pem']},
    include_package_data=True,
    # not being used? -- setuptools does not like it.
    # looks like debhelper is honoring it...
    data_files=data_files,
    zip_safe=False,
    platforms="all",
    entry_points={
        'console_scripts': [leap_launcher]
    },
    **extra_options
)
