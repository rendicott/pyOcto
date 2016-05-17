import json
import requests
import logging
import datetime
import sys
from OctoVar import OctoVar


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
    proj_id = [x.get('Id') for x in r.json() if x.get('Name').lower() == settings.project_name.lower()]
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
    mach_id = [x.get('Id') for x in r.json() if x.get('Name').lower() == settings.machine_name.lower()]
    if len(mach_id) > 1:
        logging.error("Error: More than one machine matches name '%s'" % settings.environment_string)
        sys.exit(1)
    else:
        try:
            if len(mach_id) == 0:
                print("Machine ID for machine name '%s' not found. Exiting" % settings.machine_name)
                sys.exit(0)
            mach_id = mach_id[0]
        except Exception as e:
            logging.critical("Exception getting machine Id: " + str(e))

    logging.debug("Machine ID = " + str(mach_id))
    return mach_id


def get_env_id(settings):
    headers = {'x-Octopus-ApiKey': settings.api_key}

    r = requests.get(settings.url_environments, headers=headers)
    env_id = [x.get('Id') for x in r.json() if x.get('Name').lower() == settings.environment_string.lower()]
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
