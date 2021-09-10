"""
List all the schemas to be verified here.
Every database (counters_db, app_db, etc) should have a separate schema.
Every schema is defined in dictionary format, and details can be found at:
http://json-schema.org/draft-06/schema
"""

DB_ID_MAP = {
    "APPL_DB":	0,
    "ASIC_DB":	1,
    "COUNTERS_DB":	2,
    "LOGLEVEL_DB":	3,
    "CONFIG_DB":	4,
    "FLEX_COUNTER_DB":	5,
    "STATE_DB":	6
}

DB_SCHEMA = {
    "COUNTERS_DB":
    {
        "$schema": "http://json-schema.org/draft-06/schema",
        "type": "object",
        "title": "Schema for COUNTERS DB's entities",
        "required": ["COUNTERS_PORT_NAME_MAP"],
        "properties": {
            "COUNTERS_PORT_NAME_MAP": {"$id": "#/properties/COUNTERS_PORT_NAME_MAP", "type": "object"}
        }
    }
}
