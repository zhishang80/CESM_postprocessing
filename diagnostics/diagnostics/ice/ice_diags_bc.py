#!/usr/bin/env python2
"""Base class for ice diagnostics
"""
from __future__ import print_function

import sys
import glob

if sys.hexversion < 0x02070000:
    print(70 * "*")
    print("ERROR: {0} requires python >= 2.7.x. ".format(sys.argv[0]))
    print("It appears that you are running python {0}".format(
        ".".join(str(x) for x in sys.version_info[0:3])))
    print(70 * "*")
    sys.exit(1)

import errno
import os
import traceback

# import the MPI related modules
from asaptools import partition, simplecomm, vprinter, timekeeper

# import the helper utility modules
from cesm_utils import cesmEnvLib
from diag_utils import diagUtilsLib

class IceDiagnostic(object):
    """This is the base class defining the common interface for all
    ice diagnostics
    """
    def __init__(self):
        self._name = 'Base'
        self._title = 'Base'
        self.scomm = ''

    def name(self):
        return self._name

    def title(self):
        return self._title

    def setup_workdir(self, env, t, scomm):
        """This method sets up the unique working directory for a given diagnostic type
        """
        # create the working directory first before calling the base class prerequisites
        avg_BEGYR = (int(env['ENDYR_'+t]) - int(env['YRS_TO_AVG'])) + 1
        subdir = '{0}.{1}-{2}/{3}.{4}_{5}'.format(env['CASE_TO_'+t], avg_BEGYR, env['ENDYR_'+t],self._name.lower(), str(avg_BEGYR), env['ENDYR_'+t])
        workdir = '{0}/{1}'.format(env['PATH_CLIMO_'+t], subdir)
        env['CLIMO_'+t] = workdir

        if (scomm.is_manager()):
            try:
                os.makedirs(workdir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    err_msg = 'ERROR: {0} problem accessing the working directory {1}'.format(self.__class__.__name__, workdir)
                    raise OSError(err_msg)

        # create symbolic links between the old and new workdir and get the real names of the files
        old_workdir = env['PATH_CLIMO_'+t]+env['CASE_TO_'+t]+'.'+str(avg_BEGYR)+'-'+env['ENDYR_'+t]
        env['PATH_CLIMO_'+t] = workdir
        # Add links to the new wkrdir that use the expected file names (existing climos have dates, the NCL do not like dates)
        if (scomm.is_manager()):
            climo_files = glob.glob(old_workdir+'/*.nc') 
            for climo_file in climo_files:
                name_split = climo_file.split('.') # Split on '.'
                if ('-' in name_split[-3]):
                    fn = str.join('.',name_split[:len(name_split)-3] + name_split[-2:]) #Piece together w/o the date, but still has old path 
                    path_split = fn.split('/') # Remove the path
                    if ('jfm' in path_split[-1]):
                        s = 'jfm'
                    elif ('amj' in path_split[-1]):
                        s = 'amj'
                    elif ('jas' in path_split[-1]):
                        s = 'jas'
                    elif ('ond' in path_split[-1]):
                        s = 'ond'
                    elif ('fm' in path_split[-1]):
                        s = 'fm'
                    elif ('on' in path_split[-1]):
                        s = 'on'
                    elif ('ANN' in path_split[-1]):
                        s = 'ann'
                    else:
                        s = None
                    if s is not None:
                        new_fn = workdir + '/' + s + '_avg_' + str(avg_BEGYR).zfill(4) + '-' + env['ENDYR_'+t].zfill(4) + '.nc' 
                    else:
                        new_fn = workdir + '/' +path_split[-1] # Take file name and add it to new path
                else:
                    new_fn = workdir + '/' + os.path.basename(climo_file)
                rc1, err_msg1 = cesmEnvLib.checkFile(new_fn, 'read')
                if not rc1:
                    os.symlink(climo_file,new_fn)

        return env

    def check_prerequisites(self, env, scomm):
        """This method does some generic checks for the prerequisites
        that are common to all diagnostics
        """
        print('  Checking generic prerequisites for ice diagnostics.')
        # setup the working directory for each diagnostics class
        env = self.setup_workdir(env, 'CONT', scomm)
        if (env['MODEL_VS_MODEL'] == 'True'):
            env = self.setup_workdir(env, 'DIFF', scomm)

    def run_diagnostics(self, env, scomm):
        """ base method for calling diagnostics
        """
        return

# todo move these classes to another file
class RecoverableError(RuntimeError):
    pass

class UnknownDiagType(RecoverableError):
    pass
