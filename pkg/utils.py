"""
Utils to help in the setup process
"""
import os
import re
import sys


def get_reqs_from_files(reqfiles):
    """
    Returns the contents of the top requirement file listed as a
    string list with the lines

    @param reqfiles: requirement files to parse
    @type reqfiles: list of str
    """
    for reqfile in reqfiles:
        if os.path.isfile(reqfile):
            return open(reqfile, 'r').read().split('\n')


def parse_requirements(reqfiles=['requirements.txt',
                                 'requirements.pip',
                                 'pkg/requirements.pip']):
    """
    Parses the requirement files provided.

    Checks the value of LEAP_VENV_SKIP_PYSIDE to see if it should
    return PySide as a dep or not. Don't set, or set to 0 if you want
    to install it through pip.

    @param reqfiles: requirement files to parse
    @type reqfiles: list of str
    """

    requirements = []
    skip_pyside = os.getenv("LEAP_VENV_SKIP_PYSIDE", "0") != "0"
    for line in get_reqs_from_files(reqfiles):
        # -e git://foo.bar/baz/master#egg=foobar
        if re.match(r'\s*-e\s+', line):
            pass
            # do not try to do anything with externals on vcs
            #requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1',
                                #line))
        # http://foo.bar/baz/foobar/zipball/master#egg=foobar
        elif re.match(r'\s*https?:', line):
            requirements.append(re.sub(r'\s*https?:.*#egg=(.*)$', r'\1',
                                line))
        # -f lines are for index locations, and don't get used here
        elif re.match(r'\s*-f\s+', line):
            pass

        # argparse is part of the standard library starting with 2.7
        # adding it to the requirements list screws distro installs
        elif line == 'argparse' and sys.version_info >= (2, 7):
            pass
        elif line == 'PySide' and skip_pyside:
            pass
        else:
            if line != '':
                requirements.append(line)

    #print 'REQUIREMENTS', requirements
    return requirements