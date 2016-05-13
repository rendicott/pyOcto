'''
This is a template python script that has basic option parsing
and logging framework set up already.

maintained by REndicott
'''

import logging
import sys
import requests
import os
import json
from collections import namedtuple

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


def process_variables(settings, varset, opts, mach_id):

    newVar = {u'Prompt': None,
              u'Name': opts.variablename.decode("utf-8"),
              u'IsEditable': True,
              u'IsSensitive': False,
              u'Value': opts.variablevalue.decode("utf-8"),
              u'Scope': {
                  u'Machine': [mach_id.decode("utf-8")]},
              }
    logging.debug("Created new var: " + str(newVar))
    varset.append(newVar)
    return(varset)


def post_varset(settings, fulljson, proj_id):
    headers = {'x-Octopus-ApiKey': settings.api_key}
    url_variables = settings.base_url + '/api/variables/variableset-' + proj_id
    try:
        jsons = json.dumps(fulljson)
        print(jsons)
    except Exception as o:
        logging.debug("Exception encoding json: " + str(o))
    try:
        r = requests.put(url_variables, headers=headers, data=jsons)
        logging.debug(r.content)
    except Exception as e:
        logging.debug("Exception putting full json: " + str(e))
        sys.exit(1)


def get_variableset(settings, proj_id):
    headers = {'x-Octopus-ApiKey': settings.api_key}
    url_variables = settings.base_url  + '/api/variables/variableset-' + proj_id
    try:
        r = requests.get(url_variables, headers=headers)
        varset = r.json().get('Variables')
        fulljson = r.json()
        return fulljson, varset
    except Exception as e:
        logging.debug("Exception getting variableset: " + str(e))
        sys.exit(1)


def get_proj_id(settings):
    headers = {'x-Octopus-ApiKey': settings.api_key}

    r = requests.get(settings.url_projects, headers=headers)
    proj_id = [x.get('Id') for x in r.json() if x.get('Name') == settings.project_name]
    if len(proj_id) > 1:
        logging.error("Error: More than one machine matches name '%s'" % settings.project_name)
        sys.exit(1)
    else:
        try:
            proj_id = proj_id[0]
        except Exception as e:
            logging.critical("Exception getting project Id: " + str(e))

    logging.debug("Project ID = " + str(proj_id))
    return proj_id


def get_mach_id(settings):
    headers = {'x-Octopus-ApiKey': settings.api_key}

    r = requests.get(settings.url_machines, headers=headers)
    mach_id = [x.get('Id') for x in r.json() if x.get('Name') == settings.machine_name]
    if len(mach_id) > 1:
        logging.error("Error: More than one machine matches name '%s'" % settings.environment_string)
        sys.exit(1)
    else:
        try:
            mach_id = mach_id[0]
        except Exception as e:
            logging.critical("Exception getting machine Id: " + str(e))

    logging.debug("Machine ID = " + str(mach_id))
    return mach_id


def get_env_id(settings):
    headers = {'x-Octopus-ApiKey': settings.api_key}

    r = requests.get(settings.url_environments, headers=headers)
    env_id = [x.get('Id') for x in r.json() if x.get('Name') == settings.environment_string]
    if len(env_id) > 1:
        logging.error("Error: More than one environment matches name '%s'" % settings.environment_string)
        sys.exit(1)
    else:
        try:
            env_id = env_id[0]
        except Exception as e:
            logging.critical("Exception getting environment Id: " + str(e))

    logging.debug("Environment ID = " + str(env_id))
    return env_id


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
    opts = process_opts(opts)
    baseUrl = opts.baseurl
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
                    baseUrl,
                    baseUrl + '/api/machines/all',
                    baseUrl + '/api/projects/all',
                    baseUrl + '/api/environments/all']
    Settings = namedtuple('settings', field_names)
    s = Settings(*field_values)
    env_id = get_env_id(s)
    mach_id = get_mach_id(s)
    proj_id = get_proj_id(s)
    logging.debug(env_id)
    logging.debug(mach_id)
    logging.debug(proj_id)
    fulljson, varset = get_variableset(s, proj_id)
    newvarset = process_variables(s, varset, opts, mach_id)
    fulljson['Variables'] = newvarset
    post_varset(s, fulljson, proj_id)

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
                      help="This is the environment in which to look for the machine. Default=None",
                      default=None)
    parser.add_option('--apikey',
                      type='string',
                      help="This is the API key with which to authenticate against the Octopus REST API. Default=None",
                      default=None)
    parser.add_option('--rolename',
                      type='string',
                      help="This is the role with which to search for the machine. Default=None",
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
    '''
    parser.add_option('--sampleflag',
                      action='store_true',
                      help="Boolean flag. If this option is present then options.sampleflag will be True",
                      default=False)
    '''
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
