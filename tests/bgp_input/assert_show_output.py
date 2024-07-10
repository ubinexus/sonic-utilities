"""
Module holding the correct values for show CLI command outputs for the bgp_test.py
"""

show_device_global_empty = """\
No configuration is present in CONFIG DB
"""

show_device_global_all_disabled = """\
TSA       W-ECMP
--------  --------
disabled  disabled
"""
show_device_global_all_disabled_json = """\
{
    "tsa": "disabled",
    "w-ecmp": "disabled"
}
"""

show_device_global_all_enabled = """\
TSA        W-ECMP
-------  --------
enabled         5
"""
show_device_global_all_enabled_json = """\
{
    "tsa": "enabled",
    "w-ecmp": "5"
}
"""

show_device_global_tsa_enabled = """\
TSA      W-ECMP
-------  ----------
enabled  cumulative
"""
show_device_global_tsa_enabled_json = """\
{
    "tsa": "enabled",
    "w-ecmp": "cumulative"
}
"""

show_device_global_wcmp_enabled = """\
TSA       W-ECMP
--------  --------------
disabled  num_multipaths
"""
show_device_global_wcmp_enabled_json = """\
{
    "tsa": "disabled",
    "w-ecmp": "num_multipaths"
}
"""

show_device_global_all_disabled_multi_asic = """\
ASIC ID    TSA       W-ECMP
---------  --------  --------
asic0      disabled  disabled
asic1      disabled  disabled
"""
show_device_global_all_disabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "disabled",
        "w-ecmp": "disabled"
    },
    "asic1": {
        "tsa": "disabled",
        "w-ecmp": "disabled"
    }
}
"""

show_device_global_all_enabled_multi_asic = """\
ASIC ID    TSA        W-ECMP
---------  -------  --------
asic0      enabled         5
asic1      enabled         5
"""
show_device_global_all_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "w-ecmp": "5"
    },
    "asic1": {
        "tsa": "enabled",
        "w-ecmp": "5"
    }
}
"""

show_device_global_tsa_enabled_multi_asic = """\
ASIC ID    TSA      W-ECMP
---------  -------  ----------
asic0      enabled  cumulative
asic1      enabled  cumulative
"""
show_device_global_tsa_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "w-ecmp": "cumulative"
    },
    "asic1": {
        "tsa": "enabled",
        "w-ecmp": "cumulative"
    }
}
"""

show_device_global_wcmp_enabled_multi_asic = """\
ASIC ID    TSA       W-ECMP
---------  --------  --------------
asic0      disabled  num_multipaths
asic1      disabled  num_multipaths
"""
show_device_global_wcmp_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "disabled",
        "w-ecmp": "num_multipaths"
    },
    "asic1": {
        "tsa": "disabled",
        "w-ecmp": "num_multipaths"
    }
}
"""

show_device_global_opposite_multi_asic = """\
ASIC ID    TSA       W-ECMP
---------  --------  --------------
asic0      enabled   cumulative
asic1      disabled  num_multipaths
"""
show_device_global_opposie_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "w-ecmp": "cumulative"
    },
    "asic1": {
        "tsa": "disabled",
        "w-ecmp": "num_multipaths"
    }
}
"""
