import ast

QSFP_DATA_MAP = {
    'model': 'Vendor PN',
    'vendor_oui': 'Vendor OUI',
    'vendor_date': 'Vendor Date Code(YYYY-MM-DD Lot)',
    'manufacturer': 'Vendor Name',
    'vendor_rev': 'Vendor Rev',
    'serial': 'Vendor SN',
    'type': 'Identifier',
    'ext_identifier': 'Extended Identifier',
    'ext_rateselect_compliance': 'Extended RateSelect Compliance',
    'cable_length': 'cable_length',
    'cable_type': 'Length',
    'nominal_bit_rate': 'Nominal Bit Rate(100Mbs)',
    'specification_compliance': 'Specification compliance',
    'encoding': 'Encoding',
    'connector': 'Connector',
    'application_advertisement': 'Application Advertisement'
}


def covert_application_advertisement_to_output_string(indent, sfp_info_dict):
    key = 'application_advertisement'
    field_name = '{}{}: '.format(indent, QSFP_DATA_MAP[key])
    output = field_name
    try:
        app_adv_str = sfp_info_dict[key]
        app_adv_dict = ast.literal_eval(app_adv_str)
        if not app_adv_dict:
            output += 'N/A\n'
        else:
            lines = []
            for item in app_adv_dict.values():
                host_interface_id = item.get('host_electrical_interface_id')
                if not host_interface_id:
                    continue
                elements = []
                elements.append(host_interface_id)
                elements.append(item.get('module_media_interface_id', 'Unknown'))
                elements.append(str(item.get('host_lane_assignment_options', 'Unknown')))
                lines.append(' - '.join(elements))
            sep = '\n' + ' ' * len(field_name)
            output += sep.join(lines)
            output += '\n'
    except Exception:
        output += '{}\n'.format(app_adv_str)
    return output
