# pyOcto

Script for interfacing with the Octopus REST API. Designed as a replacement for some of the features in [Octopus-Cmdlets](https://github.com/Swoogan/Octopus-Cmdlets). The intention is to use the script in a VM automation workflow where you need to add variables to a given Octopus project in preparation for a release and then be able to delete references to the machine when you delete the VM. 

 * Add variables to Octopus Project with machine name as scope. 
 * Remove all references to variables with a given machine name in the scope. 
 
## Usage
A basic usage example for adding a variable looks like this:

```
c:\source\DevOps\pyOcto> python pyOcto.py -d -1 --machinename "DOWIN08" --apikey "API-DZ8ABRTSLKL855555MM4ITT8HCQ" --baseurl "http://octodeployserver:8090/" --projectname "Awesome Project - TEST" --variablename "TESTING1234_4" --variablevalue "1234TESTING"

('starting up with loglevel', 10, 'DEBUG')
SUCCESSFULLY POSTED VARSET!


```

And basic usage for deleting all variables for a given machine looks like this:

```
c:\source\DevOps\pyOcto>python pyOcto.py -d -1 --machinename "DOWIN08" --apikey "API-DZ8ABRTSLKL855555MM4ITT8HCQ" --baseurl "http://octodeployserver:8090/" --projectname "Awesome Project - TEST" --deletemachinevars

('starting up with loglevel', 10, 'DEBUG')
Projects-125
DELETING 4 VARIABLES...
SUCCESS! Created 1 new variable sets in 1 projects.

```


The in-program help goes as follows:
```
Usage: pyOcto.py [--debug] [--printtostdout] [--logfile] [--version] [--help] [--samplefileoption]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  --machinename=MACHINENAME
                        This is the machine name to find in Octopus.
                        Default=None
  --baseurl=BASEURL     This is the base url for the Octopus REST API.
                        Default=None
  --projectname=PROJECTNAME
                        This is the name of the project in which to add
                        machine variables. Default=None
  --environmentname=ENVIRONMENTNAME
                        NOT USED: When adding a variable this environment will
                        be added in scope. Default=None
  --apikey=APIKEY       This is the API key with which to authenticate against
                        the Octopus REST API. Default=None
  --rolename=ROLENAME   NOT USED: When adding a variable this role will be
                        added in scope. Default=None
  --variablename=VARIABLENAME
                        Name of the variable to add. Default=None
  --variablevalue=VARIABLEVALUE
                        Value of the variable to add. Default=None
  --scope=SCOPE         This is the scope of the variable. Defaults to None
  --deletemachinevars   Boolean Flag. Overrides all other parameters for
                        variable addition. Deletes all variables in Octopus
                        assigned to 'machinename'. When combined with the
                        'projectname' parameter the machine vars will only be
                        deleted from the specified project--otherwise all
                        projects will be searched. All variables that contain
                        the machine name in the given project or projects will
                        be modified to remove that reference. If the machine
                        name was the only object referenced in that variable's
                        scope then the entire variable will be deleted.
                        Otherwise, only the scope of the variable will be
                        modified to remove reference to 'machinename'
                        Default=None

  Debug Options:
    -d DEBUG, --debug=DEBUG
                        Available levels are CRITICAL (3), ERROR (2), WARNING
                        (1), INFO (0), DEBUG (-1)
    -p, --printtostdout
                        Print all log messages to stdout
    -l FILE, --logfile=FILE
                        Desired filename of log file output. Default is
                        "pyOcto.py.log"


```

## Future Enhancements
* Ability to create and deploy releases.
* Support for other scopes (e.g., Role, and Environment) besides just Machine.
* Ability to export and import project variables to/from flat file.
