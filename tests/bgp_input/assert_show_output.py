"""
Module holding the correct values for show CLI command outputs for the bgp_test.py
"""

show_device_global_empty="""\
No configuration is present in CONFIG DB
"""

show_device_global_all_disabled="""\
TSA       WCMP
--------  --------
disabled  disabled
"""
show_device_global_all_disabled_json="""\
{
    "tsa": "disabled",
    "wcmp": "disabled"
}
"""

show_device_global_all_enabled="""\
TSA      WCMP
-------  -------
enabled  enabled
"""
show_device_global_all_enabled_json="""\
{
    "tsa": "enabled",
    "wcmp": "enabled"
}
"""

show_device_global_tsa_enabled="""\
TSA      WCMP
-------  --------
enabled  disabled
"""
show_device_global_tsa_enabled_json="""\
{
    "tsa": "enabled",
    "wcmp": "disabled"
}
"""

show_device_global_wcmp_enabled="""\
TSA       WCMP
--------  -------
disabled  enabled
"""
show_device_global_wcmp_enabled_json="""\
{
    "tsa": "disabled",
    "wcmp": "enabled"
}
"""
