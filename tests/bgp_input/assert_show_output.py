"""
Module holding the correct values for show CLI command outputs for the bgp_test.py
"""

show_device_global_empty = """\
No configuration is present in CONFIG DB
"""

show_device_global_all_disabled = """\
TSA       W-ECMP    BANDWIDTH
--------  --------  -----------
disabled  disabled  ignore
"""
show_device_global_all_disabled_json = """\
{
    "tsa": "disabled",
    "w-ecmp": "disabled",
    "bandwidth": "ignore"
}
"""

show_device_global_all_enabled = """\
TSA        W-ECMP  BANDWIDTH
-------  --------  -----------
enabled         5  active
"""
show_device_global_all_enabled_json = """\
{
    "tsa": "enabled",
    "w-ecmp": "5",
    "bandwidth": "active"
}
"""

show_device_global_tsa_enabled = """\
TSA      W-ECMP      BANDWIDTH
-------  ----------  ------------
enabled  cumulative  skip_missing
"""
show_device_global_tsa_enabled_json = """\
{
    "tsa": "enabled",
    "w-ecmp": "cumulative",
    "bandwidth": "skip_missing"
}
"""

show_device_global_wcmp_enabled = """\
TSA       W-ECMP          BANDWIDTH
--------  --------------  --------------------------
disabled  num_multipaths  default_weight_for_missing
"""
show_device_global_wcmp_enabled_json = """\
{
    "tsa": "disabled",
    "w-ecmp": "num_multipaths",
    "bandwidth": "default_weight_for_missing"
}
"""

show_device_global_all_disabled_multi_asic = """\
ASIC ID    TSA       W-ECMP    BANDWIDTH
---------  --------  --------  -----------
asic0      disabled  disabled  ignore
asic1      disabled  disabled  ignore
"""
show_device_global_all_disabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "disabled",
        "w-ecmp": "disabled",
        "bandwidth": "ignore"
    },
    "asic1": {
        "tsa": "disabled",
        "w-ecmp": "disabled",
        "bandwidth": "ignore"
    }
}
"""

show_device_global_all_enabled_multi_asic = """\
ASIC ID    TSA        W-ECMP  BANDWIDTH
---------  -------  --------  -----------
asic0      enabled         5  active
asic1      enabled         5  active
"""
show_device_global_all_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "w-ecmp": "5",
        "bandwidth": "active"
    },
    "asic1": {
        "tsa": "enabled",
        "w-ecmp": "5",
        "bandwidth": "active"
    }
}
"""

show_device_global_tsa_enabled_multi_asic = """\
ASIC ID    TSA      W-ECMP      BANDWIDTH
---------  -------  ----------  ------------
asic0      enabled  cumulative  skip_missing
asic1      enabled  cumulative  skip_missing
"""
show_device_global_tsa_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "w-ecmp": "cumulative",
        "bandwidth": "skip_missing"
    },
    "asic1": {
        "tsa": "enabled",
        "w-ecmp": "cumulative",
        "bandwidth": "skip_missing"
    }
}
"""

show_device_global_wcmp_enabled_multi_asic = """\
ASIC ID    TSA       W-ECMP          BANDWIDTH
---------  --------  --------------  --------------------------
asic0      disabled  num_multipaths  default_weight_for_missing
asic1      disabled  num_multipaths  default_weight_for_missing
"""
show_device_global_wcmp_enabled_multi_asic_json = """\
{
    "asic0": {
        "tsa": "disabled",
        "w-ecmp": "num_multipaths",
        "bandwidth": "default_weight_for_missing"
    },
    "asic1": {
        "tsa": "disabled",
        "w-ecmp": "num_multipaths",
        "bandwidth": "default_weight_for_missing"
    }
}
"""

show_device_global_opposite_multi_asic = """\
ASIC ID    TSA       W-ECMP          BANDWIDTH
---------  --------  --------------  --------------------------
asic0      enabled   cumulative      skip_missing
asic1      disabled  num_multipaths  default_weight_for_missing
"""
show_device_global_opposie_multi_asic_json = """\
{
    "asic0": {
        "tsa": "enabled",
        "w-ecmp": "cumulative",
        "bandwidth": "skip_missing"
    },
    "asic1": {
        "tsa": "disabled",
        "w-ecmp": "num_multipaths",
        "bandwidth": "default_weight_for_missing"
    }
}
"""
