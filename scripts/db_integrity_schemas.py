CONFIG_DB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-06/schema",
    "type": "object",
    "title": "Schema for config_db.json critical structure needed before reboot",
    "required": [
        "ACL_TABLE",
        "BGP_NEIGHBOR",
        "BGP_PEER_RANGE",
        "CRM",
        "DEVICE_METADATA",
        "DEVICE_NEIGHBOR",
        "DEVICE_NEIGHBOR_METADATA",
        "FEATURE",
        "LOOPBACK_INTERFACE",
        "PORT",
        "VERSIONS"
    ],
    "properties": {
        "ACL_TABLE": {"$id": "#/properties/ACL_TABLE", "type": "object"},
        "BGP_NEIGHBOR": {"$id": "#/properties/BGP_NEIGHBOR", "type": "object"},
        "BGP_PEER_RANGE": {"$id": "#/properties/BGP_PEER_RANGE", "type": "object"},
        "CRM": {"$id": "#/properties/CRM", "type": "object"},
        "DEVICE_METADATA": {"$id": "#/properties/DEVICE_METADATA", "type": "object"},
        "DEVICE_NEIGHBOR": {"$id": "#/properties/DEVICE_NEIGHBOR", "type": "object"},
        "DEVICE_NEIGHBOR_METADATA": {"$id": "#/properties/DEVICE_NEIGHBOR_METADATA", "type": "object"},
        "FEATURE": {
            "$id": "#/properties/FEATURE", "type": "object",
            "required": ["bgp","database","lldp","radv","swss","syncd","teamd"],
            "properties": {
                "bgp": {"$id": "#/properties/FEATURE/properties/bgp", "type": "object"},
                "database": {"$id": "#/properties/FEATURE/properties/database", "type": "object"},
                "lldp": {"$id": "#/properties/FEATURE/properties/lldp", "type": "object"},
                "radv": {"$id": "#/properties/FEATURE/properties/radv", "type": "object"},
                "swss": {"$id": "#/properties/FEATURE/properties/swss", "type": "object"},
                "syncd": {"$id": "#/properties/FEATURE/properties/syncd", "type": "object"},
                "teamd": {"$id": "#/properties/FEATURE/properties/teamd", "type": "object"}
            }
        },
        "LOOPBACK_INTERFACE": {"$id": "#/properties/LOOPBACK_INTERFACE", "type": "object"},
        "PORT": {"$id": "#/properties/PORT", "type": "object"},
        "VERSIONS": {
            "$id": "#/properties/VERSIONS",
            "type": "object",
            "required": ["DATABASE"],
            "properties": {
                "DATABASE": {
                    "$id": "#/properties/VERSIONS/properties/DATABASE",
                    "type": "object",
                    "required": ["VERSION"],
                    "properties": {
                        "VERSION": {"$id": "#/properties/VERSIONS/properties/DATABASE/properties/VERSION", "type": "string"}
                    }
                }
            }
        }
    }
}

COUNTERS_DB_SCHEMA = {
    "$schema": "http://json-schema.org/draft-06/schema",
    "type": "object",
    "title": "Schema for COUNTERS DB's entities",
    "required": [
        "COUNTERS_PORT_NAME_MAP"
    ],
    "properties": {
        "COUNTERS_PORT_NAME_MAP": {"$id": "#/properties/COUNTERS_PORT_NAME_MAP", "type": "object"}
    }
}
