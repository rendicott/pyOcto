

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