'''
This is a template python script that has basic option parsing
and logging framework set up already.

maintained by REndicott
'''

import logging
import sys
import os
import datetime
from collections import namedtuple

from pyOcto_functions import get_mach_id
from pyOcto_functions import get_env_id
from pyOcto_functions import get_proj_id
from pyOcto_functions import search_vars
from pyOcto_functions import delete_mach_var_from_proj
from pyOcto_functions import get_variableset
from pyOcto_functions import post_varset
from pyOcto_functions import add_variable

sversion = 'v0.1'
scriptfilename = os.path.basename(sys.argv[0])
defaultlogfilename = scriptfilename + '.log'


def setuplogging(loglevel, printtostdout, logfile):
    # pretty self explanatory. Takes options and sets up logging.
    print("starting up with loglevel", loglevel, logging.getLevelName(loglevel))
    logging.basicConfig(filename=logfile,
                        filemode='w', level=loglevel,
                        format='%(asctime)s:%(levelname)s:%(message)s')
    if printtostdout:
        soh = logging.StreamHandler(sys.stdout)
        soh.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(soh)

def process_opts(opts):
    attrs = []
    for attr in dir(opts):
        if ('__' not in attr and
            'instancemethod' not in str(type(getattr(opts, attr))) and
            'dict' not in str(type(getattr(opts, attr)))
             ):
            attrs.append(attr)
    for a in attrs:
        logging.debug("OPTION: '%s' = '%s' " % (a, getattr(opts, a)))
    return(opts)


def main(opts):
    """ The main() method. Program starts here.
    """
    success = False
    t1_totalruntime = datetime.datetime.now()
    opts = process_opts(opts)
    if opts.baseurl is None:
        print("BASEURL IS REQUIRED. Exiting...")
        sys.exit(1)
    if opts.apikey is None:
        print("APIKEY IS REQUIRED. Exiting...")
        sys.exit(1)
    baseurl = opts.baseurl

    field_names = ['machine_name',
                   'environment_string',
                   'project_name',
                   'role',
                   'api_key',
                   'base_url',
                   'url_machines',
                   'url_projects',
                   'url_environments']
    field_values = [opts.machinename,
                    opts.environmentname,
                    opts.projectname,
                    opts.rolename,
                    opts.apikey,
                    baseurl,
                    baseurl + '/api/machines/all',
                    baseurl + '/api/projects/all',
                    baseurl + '/api/environments/all']
    Settings = namedtuple('settings', field_names)
    s = Settings(*field_values)

    if opts.machinename:
        mach_id = get_mach_id(s)
        logging.debug("MACHINE ID: " + mach_id)
    else:
        print("MACHINE NAME REQUIRED. EXITING")
        sys.exit(1)
    if opts.projectname is None:
        print("PROJECT NAME IS REQUIRED. EXITING")
        sys.exit(1)
    if opts.environmentname:
        env_id = get_env_id(s)
        logging.debug("ENVIRONMENT ID: " + env_id)
    proj_id = None
    if opts.projectname:
        proj_id = get_proj_id(s)
        logging.debug("PROJECT ID: " + proj_id)

    if opts.deletemachinevars:
        if proj_id is not None:
            print(proj_id)
            url = '/api/variables/variableset-' + proj_id
            list_of_proj_where_mach_found = [url]
        else:  # if not specified we need to search and purge from all projects
            list_of_proj_where_mach_found = search_vars(s, mach_id)
        success = delete_mach_var_from_proj(s, list_of_proj_where_mach_found, mach_id)
    else:
        if opts.variablename and opts.variablevalue and not opts.deletemachinevars:
            fulljson, varset = get_variableset(s, proj_id)
            newvarset_json = add_variable(s, varset, opts, mach_id)
            fulljson['Variables'] = newvarset_json
            success = post_varset(s, fulljson, proj_id)
        else:
            print("VARIABLE NAME AND VALUE ARE REQUIRED. EXITING.")
            success = False

    t2_totalruntime = datetime.datetime.now()
    totalruntime = t2_totalruntime - t1_totalruntime
    logging.debug("TOTAL PROGRAM RUNTIME: " + str(totalruntime))
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    '''This main section is mostly for parsing arguments to the
    script and setting up debugging'''
    from optparse import OptionParser
    '''set up an additional option group just for debugging parameters'''
    from optparse import OptionGroup
    usage = "%prog [--debug] [--printtostdout] [--logfile] [--version] [--help] [--samplefileoption]"
    # set up the parser object
    parser = OptionParser(usage, version='%prog ' + sversion)
    parser.add_option('--machinename',
                      type='string',
                      help='This is the machine name to find in Octopus. Default=None', default=None)
    parser.add_option('--baseurl',
                      type='string',
                      help='This is the base url for the Octopus REST API. Default=None', default=None)
    parser.add_option('--projectname',
                      type='string',
                      help='This is the name of the project in which to add machine variables. Default=None',
                      default=None)
    parser.add_option('--environmentname',
                      type='string',
                      help="NOT USED: When adding a variable this environment will be added in scope. Default=None",
                      default=None)
    parser.add_option('--apikey',
                      type='string',
                      help="This is the API key with which to authenticate against the Octopus REST API. Default=None",
                      default=None)
    parser.add_option('--rolename',
                      type='string',
                      help="NOT USED: When adding a variable this role will be added in scope. Default=None",
                      default=None)
    parser.add_option('--variablename',
                      type='string',
                      help='Name of the variable to add. Default=None',
                      default=None)
    parser.add_option('--variablevalue',
                      type='string',
                      help="Value of the variable to add. Default=None",
                      default=None)
    parser.add_option('--scope',
                      type='string',
                      help="This is the scope of the variable. Defaults to None", default=None)
    parser.add_option('--deletemachinevars',
                      action='store_true',
                      help=("Boolean Flag. Overrides all other parameters for variable addition. " +
                            "Deletes all variables in Octopus assigned to 'machinename'. " +
                            "When combined with the 'projectname' parameter the machine vars will only be " +
                            "deleted from the specified project--otherwise all projects will be searched. All " +
                            "variables that contain the machine name in the given project or projects will be " +
                            "modified to remove that reference. If the machine name was the only object referenced " +
                            "in that variable's scope then the entire variable will be deleted. Otherwise, only the " +
                            "scope of the variable will be modified to remove reference to 'machinename' Default=None"),
                      default=None)
    parser_debug = OptionGroup(parser, 'Debug Options')
    parser_debug.add_option('-d', '--debug', type='string',
                            help=('Available levels are CRITICAL (3), ERROR (2), '
                                  'WARNING (1), INFO (0), DEBUG (-1)'),
                            default='CRITICAL')
    parser_debug.add_option('-p', '--printtostdout', action='store_true',
                            default=False, help='Print all log messages to stdout')
    parser_debug.add_option('-l', '--logfile', type='string', metavar='FILE',
                            help=('Desired filename of log file output. Default '
                                  'is "' + defaultlogfilename + '"'),
                            default=defaultlogfilename)
    # officially adds the debugging option group
    parser.add_option_group(parser_debug)
    options, args = parser.parse_args()  # here's where the options get parsed

    try: # now try and get the debugging options
        loglevel = getattr(logging, options.debug)
    except AttributeError:  # set the log level
        loglevel = {3: logging.CRITICAL,
                    2: logging.ERROR,
                    1: logging.WARNING,
                    0: logging.INFO,
                    -1: logging.DEBUG,
                    }[int(options.debug)]

    try:
        open(options.logfile, 'w')  # try and open the default log file
    except:
        print("Unable to open log file '%s' for writing." % options.logfile)
        logging.debug(
            "Unable to open log file '%s' for writing." % options.logfile)

    setuplogging(loglevel, options.printtostdout, options.logfile)

    main(options)
