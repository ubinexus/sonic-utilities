#!/usr/bin/env python

from collections import OrderedDict
from config.config_mgmt import ConfigMgmt

class YangParser:
    """ YANG model parser

        Attributes:
        yang_model_name: Name of the YANG model file
        conf_mgmt: Instance of Config Mgmt class to help parse YANG models
        idx_yJson: Index of yang_model_file (1 attr) inside conf_mgmt.sy.yJson object
        y_module: Reference to 'module' entity from YANG model file
        y_top_level_container: Reference to top level 'container' entity from YANG model file
        y_table_containers: Reference to 'container' entities from YANG model file
                            that represent Config DB tables
        yang_2_dict: dictionary created from YANG model file that represent Config DB schema.
                     In case if YANG model has a 'list' entity:
        {
            'tables': [{
                'name': 'value',
                'description': 'value',
                'dynamic-objects': [
                    'name': 'value',
                    'description': 'value,
                    'attrs': [
                        {
                            'name': 'value',
                            'descruption': 'value',
                            'is-leaf-list': False,
                            'is-mandatory': False
                        }
                        ...
                    ],
                    'keys': [
                        {
                            'name': 'ACL_TABLE_NAME',
                            'description': 'value'
                        }
                        ...
                    ]
                ],
            }]
        }
        In case if YANG model does NOT have a 'list' entity, it has the same structure as above, but 'dynamic-objects' changed to 'static-objects' and have no 'keys'
    """
    def __init__(self,
                 yang_model_name):
        self.yang_model_name = yang_model_name
        self.conf_mgmt = None
        self.idx_yJson = None
        self.y_module = None
        self.y_top_level_container = None
        self.y_table_containers = None
        self.yang_2_dict = dict()

        try:
            self.conf_mgmt = ConfigMgmt()
        except Exception as e:
            raise Exception("Failed to load the {} class".format(str(e)))
    
    def _init_yang_module_and_containers(self):
        """ Initialize inner class variables:
            self.y_module
            self.y_top_level_container
            self.y_table_containers

            Raises:
                KeyError: if invalid YANG model provided
                KeyError: if YANG models is NOT exist
        """

        self._find_index_of_yang_model()

        if self.idx_yJson is not None:
            self.y_module = self.conf_mgmt.sy.yJson[self.idx_yJson]['module']
            if self.y_module.get('container') is not None:
                self.y_top_level_container = self.y_module['container']
                self.y_table_containers = self.y_top_level_container['container']
            else:
                raise KeyError('YANG model {} does NOT have "container" element'.format(self.yang_model_name))
        else:
            raise KeyError('YANG model {} is NOT exist'.format(self.yang_model_name))

    def _find_index_of_yang_model(self):
        """ Find index of provided YANG model inside yJson object
            and save it to self.idx_yJson variable
        """

        for i in range(len(self.conf_mgmt.sy.yJson)):
            if (self.conf_mgmt.sy.yJson[i]['module']['@name'] == self.yang_model_name):
                self.idx_yJson = i

    def parse_yang_model(self) -> dict:
        """ Parse proviced YANG model
            and save output to self.yang_2_dict obj 

            Returns:
                dictionary - parsed YANG model in dictionary format
        """

        self._init_yang_module_and_containers()
        self.yang_2_dict['tables'] = list()

        # determine how many (1 or couple) containers YANG model have after 'top level' container
        # 'table' container it is a container that goes after 'top level' container
        if isinstance(self.y_table_containers, list):
            for tbl_cont in self.y_table_containers:
                y2d_elem = on_table_container(self.y_module, tbl_cont)
                self.yang_2_dict['tables'].append(y2d_elem)
        else:
            y2d_elem = on_table_container(self.y_module, self.y_table_containers)
            self.yang_2_dict['tables'].append(y2d_elem)

        return self.yang_2_dict

#------------------------------HANDLERS--------------------------------#

def on_table_container(y_module: OrderedDict, tbl_cont: OrderedDict) -> dict:
    """ Parse 'table' container,
        'table' container goes after 'top level' container

        Args:
            y_module: reference to 'module'
            tbl_cont: reference to 'table' container
        Returns:
            dictionary - element for self.yang_2_dict['tables'] 
    """

    y2d_elem = {
        'name': tbl_cont.get('@name'),
        'description': get_description(tbl_cont)
    }

    # determine if 'table container' have a 'list' entity
    if tbl_cont.get('list') is None:
        y2d_elem['static-objects'] = list()

        # 'object' container goes after 'table' container
        # 'object' container have 2 types - list (like sonic-flex_counter.yang) and NOT list (like sonic-device_metadata.yang)
        obj_cont = tbl_cont.get('container')
        if isinstance(obj_cont, list):
            for cont in obj_cont:
                static_obj_elem = on_object_container(y_module, cont, is_list=False)
                y2d_elem['static-objects'].append(static_obj_elem)
        else:
            static_obj_elem = on_object_container(y_module, obj_cont, is_list=False)
            y2d_elem['static-objects'].append(static_obj_elem)
    else:
        y2d_elem['dynamic-objects'] = list()
        tbl_cont_lists = tbl_cont.get('list')
        # 'container' can have more than 1 'list' entity
        if isinstance(tbl_cont_lists, list):
            for _list in tbl_cont_lists:
                dynamic_obj_elem = on_object_container(y_module, _list, is_list=True)
                y2d_elem['dynamic-objects'].append(dynamic_obj_elem)
        else:
            dynamic_obj_elem = on_object_container(y_module, tbl_cont_lists, is_list=True)
            y2d_elem['dynamic-objects'].append(dynamic_obj_elem)

        # move 'keys' elements from 'attrs' to 'keys'
        change_dyn_obj_struct(y2d_elem['dynamic-objects'])

    return y2d_elem

def on_object_container(y_module: OrderedDict, cont: OrderedDict, is_list: bool) -> dict:
    """ Parse a 'object container'.
        'Object container' represent OBJECT inside Config DB schema:
        {
            "TABLE": {
                "OBJECT": {
                    "attr": "value"
                }
            }
        }

        Args:
            y_module: reference to 'module'
            cont: reference to 'object container'
        Returns:
            dictionary - element for y2d_elem['static-objects'] OR y2d_elem['dynamic-objects']
    """

    obj_elem = {
        'name': cont.get('@name'),
        'description': get_description(cont),
        'attrs': list()
    }

    if is_list:
        obj_elem['keys'] = get_list_keys(cont)

    attrs_list = list()
    attrs_list.extend(get_leafs(cont))
    attrs_list.extend(get_leaf_lists(cont))
    attrs_list.extend(get_choices(y_module, cont))
    # TODO: need to test 'grouping'
    #attrs_list.extend(get_uses_grouping(y_module, cont))

    obj_elem['attrs'] = attrs_list

    return obj_elem

def on_grouping(y_module: OrderedDict, y_grouping, y_uses) -> list:
    """ Parse a YANG 'grouping' and 'uses' entities
        'grouping' element can have - 'leaf', 'leaf-list', 'choice'

        Args:
            y_module: reference to 'module'
            y_grouping: reference to 'grouping'
            y_uses: reference to 'uses'
        Returns:
            dictionary - element for obj_elem['attrs'], 'attrs' contain a parsed 'leafs'
    """

    ret_attrs = list()

    if isinstance(y_uses, list):
        if isinstance(y_grouping, list):
            for use in y_uses:
                for group in y_grouping:
                    if use.get('@name') == group.get('@name'):
                        ret_attrs.extend(get_leafs(group))
                        ret_attrs.extend(get_leaf_lists(group))
                        ret_attrs.extend(get_choices(y_module, group))
        else:
            for use in y_uses:
                if use.get('@name') == y_grouping.get('@name'):
                    ret_attrs.extend(get_leafs(y_grouping))
                    ret_attrs.extend(get_leaf_lists(y_grouping))
                    ret_attrs.extend(get_choices(y_module, y_grouping))
    else:
        if isinstance(y_grouping, list):
            for group in y_grouping:
                if y_uses.get('@name') == group.get('@name'):
                    ret_attrs.extend(get_leafs(group))
                    ret_attrs.extend(get_leaf_lists(group))
                    ret_attrs.extend(get_choices(y_module, group))
        else:
            if y_uses.get('@name') == y_grouping.get('@name'):
                ret_attrs.extend(get_leafs(y_grouping))
                ret_attrs.extend(get_leaf_lists(y_grouping))
                ret_attrs.extend(get_choices(y_module, y_grouping))

    return ret_attrs

def on_choices(y_module: OrderedDict, y_choices) -> list:
    """ Parse a YANG 'choice' entities

        Args:
            cont: reference to 'choice'
        Returns:
            dictionary - element for obj_elem['attrs'], 'attrs' contain a parsed 'leafs'
    """

    ret_attrs = list()

    # the YANG model can have multiple 'choice' entities inside 'container' or 'list'
    if isinstance(y_choices, list):
        for choice in y_choices:
            attrs = on_choice_cases(y_module, choice.get('case'))
            ret_attrs.extend(attrs)
    else:
        ret_attrs = on_choice_cases(y_module, y_choices.get('case'))

    return ret_attrs

def on_choice_cases(y_module: OrderedDict, y_cases: list) -> list:
    """ Parse a single YANG 'case' entity from 'choice' entity
        'case' element can have inside - 'leaf', 'leaf-list', 'uses'

        Args:
            y_module: reference to 'module'
            y_cases: reference to 'case'
        Returns:
            dictionary - element for obj_elem['attrs'], 'attrs' contain a parsed 'leafs'
    """

    ret_attrs = list()

    if isinstance(y_cases, list):
        for case in y_cases:
            ret_attrs.extend(get_leafs(case))
            ret_attrs.extend(get_leaf_lists(case))
            # TODO: need to deeply test it
            #ret_attrs.extend(get_uses_grouping(y_module, case))
    else:
        raise Exception('It has no sense to using a single "case" element inside "choice" element')
    
    return ret_attrs

def on_leafs(y_leafs, is_leaf_list: bool) -> list:
    """ Parse all the 'leaf' or 'leaf-list' elements

        Args:
            y_leafs: reference to all 'leaf' elements
        Returns:
            list - list of parsed 'leaf' elements 
    """

    ret_attrs = list()
    # The YANG 'container' entity may have only 1 'leaf' element OR a list of 'leaf' elements
    if isinstance(y_leafs, list): 
        for leaf in y_leafs:
            attr = on_leaf(leaf, is_leaf_list)
            ret_attrs.append(attr)
    else:
        attr = on_leaf(y_leafs, is_leaf_list)
        ret_attrs.append(attr)

    return ret_attrs

def on_leaf(leaf: OrderedDict, is_leaf_list: bool) -> dict:
    """ Parse a single 'leaf' element

        Args:
            leaf: reference to a 'leaf' entity
        Returns:
            dictionary - parsed 'leaf' element
    """

    attr = { 'name': leaf.get('@name'),
             'description': get_description(leaf),
             'is-leaf-list': is_leaf_list,
             'is-mandatory': get_mandatory(leaf) }

    return attr

#----------------------GETERS-------------------------#

def get_mandatory(y_leaf: OrderedDict) -> bool:
    if y_leaf.get('mandatory') is not None:
        return True

    return False

def get_description(y_entity: OrderedDict) -> str:
    """ Parse 'description' entity from any YANG element

        Args:
            y_entity: reference to YANG 'container' OR 'list' OR 'leaf' ...
        Returns:
            str - text of the 'description'
    """

    if y_entity.get('description') is not None:
        return y_entity.get('description').get('text')
    else:
        return ''

def get_leafs(y_entity: OrderedDict) -> list:
    if y_entity.get('leaf') is not None:
        return on_leafs(y_entity.get('leaf'), is_leaf_list=False)

    return []

def get_leaf_lists(y_entity: OrderedDict) -> list:
    if y_entity.get('leaf-list') is not None:
        return on_leafs(y_entity.get('leaf-list'), is_leaf_list=True)

    return []

def get_choices(y_module: OrderedDict, y_entity: OrderedDict) -> list:
    if y_entity.get('choice') is not None:
        return on_choices(y_module, y_entity.get('choice'))

    return []

def get_uses_grouping(y_module: OrderedDict, y_entity: OrderedDict) -> list:
    if y_entity.get('uses') is not None and y_module.get('grouping') is not None:
        return on_grouping(y_module, y_module.get('grouping'), y_entity.get('uses'))

    return []

def get_list_keys(y_list: OrderedDict) -> list:
    ret_list = list()
    keys = y_list.get('key').get('@value').split()
    for k in keys:
        key = { 'name': k }
        ret_list.append(key)

    return ret_list

def change_dyn_obj_struct(dynamic_objects: OrderedDict):
    """ Rearrange self.yang_2_dict['dynamic_objects'] structure.
        If YANG model have a 'list' entity - inside the 'list' it has 'key' entity.
        'key' entity it is whitespace-separeted list of 'leafs', those 'leafs' was
        parsed by 'on_leaf()' function and placed under 'attrs' in self.yang_2_dict['dynamic_objects']
        need to move 'leafs' from 'attrs' and put them to 'keys' section of elf.yang_2_dict['dynamic_objects']

        Args:
            dynamic_objects: reference to self.yang_2_dict['dynamic_objects']
    """
    for obj in dynamic_objects:
        for key in obj.get('keys'):
            for attr in obj.get('attrs'):
                if key.get('name') == attr.get('name'):
                    key['description'] = attr.get('description')
                    obj['attrs'].remove(attr)
                    break