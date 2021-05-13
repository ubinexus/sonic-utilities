#!/usr/bin/env python

import jinja2

from sonic_cli_gen.yang_parser import YangParser

class CliGenerator:
    """ SONiC CLI generator. This class provides public API
    for sonic-cli-gen python library. It can generate config,
    show, sonic-clear CLI plugins
    """

    def __init__(self,
                 yang_model):
        """ Initialize PackageManager. """

        self.yang_model_name = yang_model
        self.loader = jinja2.FileSystemLoader(['/usr/share/sonic/templates/sonic-cli-gen/'])
        self.env = jinja2.Environment(loader=self.loader)

    def generate_config_plugin(self):
        """ Generate CLI plugin for 'config' CLI group. """
        parser = YangParser(self.yang_model_name)
        yang_dict = parser.parse_yang_model()
        template = self.env.get_template('config.py.j2')
        with open('config.py', 'w') as config_py:
            config_py.write(template.render(yang_dict))
        

    def generate_show_plugin(self):
        """ Generate CLI plugin for 'show' CLI group. """
        parser = YangParser(self.yang_model_name)
        yang_dict = parser.parse_yang_model()
        template = self.env.get_template('show.py.j2')
        with open('show.py', 'w') as show_py:
            show_py.write(template.render(yang_dict))

    # to be implemented in the next Phases
    def generate_sonic_clear_plugin(self):
        """ Generate CLI plugin for 'sonic-clear' CLI group. """
        parser = YangParser(self.yang_model_name)
        yang_dict = parser.parse_yang_model()
        raise NotImplementedError
        
