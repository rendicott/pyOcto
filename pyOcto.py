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
import datetime
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


class OctoVar():
    def __init__(self, varset = None):
        self.name = None
        self.value = None
        self.is_editable = None
        self.is_sensitive = None
        self.scope = None
        self.prompt = None
        self.Id = None
        self.scope_machines = []
        self.scope_environments = []
        self.scope_roles = []
        self.ignore_attrs = ['scope_machines', 'scope_environments', 'scope_roles']
        self.scope_was_empty = False  # flag to indicate whether scope came in empty
        if varset is not None:
            self.process_varjson(varset)

    def process_varjson(self, vj):
        self.name = vj.get('Name')
        self.value = vj.get('Value')
        self.is_editable = vj.get('IsEditable')
        self.is_sensitive = vj.get('IsSensitive')
        self.scope = vj.get('Scope')
        if self.scope == {}:
            self.scope_was_empty = True
        self.Id = vj.get('Id')
        try:
            self.scope_machines = (vj.get('Scope').get('Machine'))
            if self.scope_machines is None:
                self.scope_machines = []
        except:
            self.scope_machines = []
        try:
            self.scope_environments = (vj.get('Scope').get('Environment'))
            if self.scope_environments is None:
                self.scope_environments = []
        except:
            self.scope_environments = []
        try:
            self.scope_roles = (vj.get('Scope').get('Role'))
            if self.scope_roles is None:
                self.scope_roles = []
        except:
            self.scope_roles = []
        self.prompt = vj.get('Prompt')

    def dumpself(self):
        message = '\n'
        for attr in dir(self):
            if (    '__' not in attr and
                    'instancemethod' not in str(type(getattr(self, attr)))
                    #attr not in self.ignore_attrs
                    ):
                message += "-- %s = %s %s" % (attr, getattr(self, attr), '\n')
        return message

    def build_json(self):
        message = {u'Prompt': self.prompt,
                   u'Name': self.name,
                   u'IsEditable': self.is_editable,
                   u'IsSensitive': self.is_sensitive,
                   u'Value': self.value,
                   u'Scope': {}
                   }
        if len(self.scope_environments) > 0:
            message[u'Scope'][u'Environment'] = self.scope_environments
        if len(self.scope_machines) > 0:
            message[u'Scope'][u'Machine'] = self.scope_machines
        if len(self.scope_roles) > 0:
            message[u'Scope'][u'Role'] = self.scope_roles
        # now rebuild the scope so we can compare objects
        self.scope = message[u'Scope']
        if self.Id is not None:
            message[u'Id'] = self.Id
        return message

    def __eq__(self, other):
        return (self.name == other.name and
                self.value == other.value and
                self.scope == other.scope and
                self.prompt == other.prompt and
                self.is_sensitive == other.is_sensitive
                )

    def __hash__(self):
        return hash(('name', self.name,
                     'value', self.value,
                     'scope', self.scope,
                     'is_sensitive', self.is_sensitive,
                     'prompt', self.prompt,
                     ))


def delete_mach_var_from_proj(settings, urls_proj, mach_id):
    headers = {'x-Octopus-ApiKey': settings.api_key}
    successes = 0
    success = False
    if len(urls_proj) == 0:
        logging.debug('NO URLS TO PROCESS, LEAVING FUNCTION')
        pass
    else:
        for ustub in urls_proj:
            varset = None
            url = settings.base_url + ustub
            r = requests.get(url, headers=headers)
            logging.debug("TYPE OF RESPONSE BODY: " + str(type(r.json())))
            logging.debug("TYPE OF RESPONSE BODY-VARIABLES: " + str(type(r.json().get('Variables'))))
            compare1 = r.json()
            varset = process_variables(r.json().get('Variables'))
            logging.debug("LENGTH BEFORE STRIP: " + str(len(varset)))
            # [logging.debug(x.dumpself()) for x in varset]
            for v in varset:
                try:
                    v.scope_machines.remove(mach_id)
                    v.build_json()  # to make sure scope is updated
                except:
                    pass

            # now build the varset back again and add vars from modified vars only if they have content in the scope
            purged_set_json = [x.build_json() for x in varset if x.scope != {} or x.scope_was_empty]
            # [logging.debug(x) for x in purged_set_json]
            logging.debug("LENGTH AFTER STRIP: " + str(len(purged_set_json)))
            message = "DELETING %s VARIABLES..." % str(len(varset)-len(purged_set_json))
            logging.debug(message)
            print(message)
            newbody = r.json()
            newbody['Variables'] = purged_set_json
            logging.debug("TYPE OF BUILT BODY: " + str(type(newbody)))
            logging.debug("TYPE OF BUILT BODY-VARIABLES: " + str(type(newbody.get('Variables'))))
            if compare1 != newbody:
                logging.debug("REST PUTTING NEW VARIABLE SET....")
                r = requests.put(url, data=json.dumps(newbody), headers=headers)
                # logging.info("RESPONSE FROM PUT: " + str(r.content))
                if r.status_code == 200:
                    successes += 1
            else:
                print("VARIABLE SET UNMODIFIED. NO VARIABLES MATCH MACHINENAME? DOING NOTHING..")
        if len(urls_proj) == successes:
            print("SUCCESS! Created %s new variable sets in %s projects." % (str(successes), str(len(urls_proj))))
            success = True
        else:
            print("SUCCESSES: '%s', LEN URLS: '%s'" % (str(successes), str(len(urls_proj))))
            success = False
    return success


def search_vars(settings, mach_id):
    headers = {'x-Octopus-ApiKey': settings.api_key}
    r = requests.get(settings.url_projects, headers=headers)
    proj_var_urls = [x['Links']['Variables'] for x in r.json()]
    proj_var_urls_mach_found = []
    for ustub in proj_var_urls:
        url = settings.base_url + ustub
        t1_rest = datetime.datetime.now()
        r_v = requests.get(url, headers=headers)
        t2_rest = datetime.datetime.now()
        t1_search = datetime.datetime.now()
        varset = r_v.json().get('Variables')
        varObjs = process_variables(varset)
        for obj in varObjs:
            try:
                if mach_id.decode('utf-8') in obj.scope_machines:
                    proj_var_urls_mach_found.append(ustub)
                    break
            except:
                pass
        t2_search = datetime.datetime.now()
        timediff_search = t2_search - t1_search
        timediff_rest = t2_rest - t1_rest
        logging.debug("SEARCHTIME: " + str(timediff_search))
        logging.debug("REST_TIME:" + str(timediff_rest))
    if len(proj_var_urls_mach_found) == 0:
        logging.debug("NO PROJECTS CONTAIN MACHINE: '%s' with ID '%s'" % (settings.machine_name, mach_id))
    return proj_var_urls_mach_found


def add_variable(settings, varset, opts, mach_id):
    newVar = OctoVar()
    newVar.is_editable = True
    newVar.is_sensitive = False
    newVar.name = opts.variablename.decode("utf-8")
    newVar.value = opts.variablevalue.decode("utf-8")
    newVar.scope_machines = [mach_id.decode("utf-8")]
    logging.debug('===============NEWVAR=====================')
    logging.debug(newVar.build_json())
    logging.debug(newVar.dumpself())
    logging.debug("Created new var: " + str(newVar))
    logging.debug('===============NEWVAR=====================')

    varset.append(newVar.build_json())
    return varset


def process_variables(varset):
    allvars = [OctoVar(x) for x in varset]
    return allvars


def post_varset(settings, fulljson, proj_id):
    headers = {'x-Octopus-ApiKey': settings.api_key}
    url_variables = settings.base_url + '/api/variables/variableset-' + proj_id
    try:
        jsons = json.dumps(fulljson)
        #print(jsons)
    except Exception as o:
        logging.debug("Exception encoding json: " + str(o))
    try:
        r = requests.put(url_variables, headers=headers, data=jsons)
        if r.status_code == 200:
            print("SUCCESSFULLY POSTED VARSET!")
            return(True)
        else:
            print("BAD STATUS CODE! %s %s" % (str(r.status_code), str(r.content)))
            sys.exit(1)
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
