import jsonpatch

from swsscommon.swsscommon import SonicV2Connector, ConfigDBConnector
from generic_config_updater.generic_updater import GenericUpdater, ConfigFormat

class ValidatedConfigDBConnector(ConfigDBConnector):

    def set_entry(self, op, path, value):
        gcu_json_input = []
        gcu_json = {"op": "{}".format(op),
                    "path": "{}".format(path)}
        if value:
            gcu_json["value"] = value
        gcu_json_input.append(gcu_json)
        gcu_patch = jsonpatch.JsonPatch(gcu_json_input)
        format = ConfigFormat.CONFIGDB.name
        config_format = ConfigFormat[format.upper()]
        GenericUpdater().apply_patch(patch=gcu_patch, config_format=config_format, verbose=False, dry_run=False, ignore_non_yang_tables=False, ignore_paths=None)
