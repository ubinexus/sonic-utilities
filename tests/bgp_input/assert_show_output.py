"""
Module holding the correct values for show CLI command outputs for the bgp_test.py
"""

show_device_global_empty = """\
No configuration is present in CONFIG DB
"""

show_device_global_all_disabled = """\
TSA       ORIGINATE-BANDWIDTH
--------  ---------------------
disabled  disabled
"""
show_device_global_all_disabled_json = """\
{
    "tsa": "disabled",
    "originate-bandwidth": "disabled"
}
"""

show_device_global_all_enabled = """\
TSA        ORIGINATE-BANDWIDTH
-------  ---------------------
enabled                      5
"""
show_device_global_all_enabled_json = """\
{
    "tsa": "enabled",
    "originate-bandwidth": "5"
}
"""

show_device_global_tsa_enabled = """\
TSA      ORIGINATE-BANDWIDTH
-------  ---------------------
enabled  cumulative
"""
show_device_global_tsa_enabled_json = """\
{
    "tsa": "enabled",
    "originate-bandwidth": "cumulative"
}
"""

show_device_global_wcmp_enabled = """\
TSA       ORIGINATE-BANDWIDTH
--------  ---------------------
disabled  num_multipaths
"""
show_device_global_wcmp_enabled_json = """\
{
    "tsa": "disabled",
    "originate-bandwidth": "num_multipaths"
}
"""

show_device_global_all_disabled_multi_asic = """\
ASIC ID    TSA       ORIGINATE-BANDWIDTH
---------  --------  ---------------------
asic0      disabled  disabled
asic1      disabled  disabled
"""
show_device_global_all_disabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "disabled",
        "originate-bandwidth": "disabled"
    },
    "asic1": {
        "tsa": "disabled",
        "originate-bandwidth": "disabled"
    }
}
"""

show_device_global_all_enabled_multi_asic = """\
ASIC ID    TSA        ORIGINATE-BANDWIDTH
---------  -------  ---------------------
asic0      enabled                      5
asic1      enabled                      5
"""
show_device_global_all_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "originate-bandwidth": "5"
    },
    "asic1": {
        "tsa": "enabled",
        "originate-bandwidth": "5"
    }
}
"""

show_device_global_tsa_enabled_multi_asic = """\
ASIC ID    TSA      ORIGINATE-BANDWIDTH
---------  -------  ---------------------
asic0      enabled  cumulative
asic1      enabled  cumulative
"""
show_device_global_tsa_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "originate-bandwidth": "cumulative"
    },
    "asic1": {
        "tsa": "enabled",
        "originate-bandwidth": "cumulative"
    }
}
"""

show_device_global_wcmp_enabled_multi_asic = """\
ASIC ID    TSA       ORIGINATE-BANDWIDTH
---------  --------  ---------------------
asic0      disabled  num_multipaths
asic1      disabled  num_multipaths
"""
show_device_global_wcmp_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "disabled",
        "originate-bandwidth": "num_multipaths"
    },
    "asic1": {
        "tsa": "disabled",
        "originate-bandwidth": "num_multipaths"
    }
}
"""

show_device_global_opposite_multi_asic = """\
ASIC ID    TSA       ORIGINATE-BANDWIDTH
---------  --------  ---------------------
asic0      enabled   cumulative
asic1      disabled  num_multipaths
"""
show_device_global_opposie_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "originate-bandwidth": "cumulative"
    },
    "asic1": {
        "tsa": "disabled",
        "originate-bandwidth": "num_multipaths"
    }
}
"""
