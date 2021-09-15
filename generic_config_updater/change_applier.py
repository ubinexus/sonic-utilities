import json
from jsonpatch import PatchOperation, AddOperation, RemoveOperation, ReplaceOperation
from swsscommon.swsscommon import ConfigDBConnector
from .gu_common import GenericConfigUpdaterError, JsonChange

class ChangeApplier:
    def __init__(self, service_metadata_file: str=None):
        self.config_db = ConfigDBConnector()
        self.config_db.connect()
        service_metadata = {}
        if service_metadata_file:
            with open(service_metadata_file, 'r') as f:
                service_metadata = json.load(f)
        self.table_service = service_metadata.get('tables', {})
        self.service_commands = service_metadata.get('services', {})
        self.valiate_metadata()
        self.previous_table_name = None

    def valiate_metadata(self):
        # TODO: check metadata file syntax
        pass

    def exec_command(self, cmd) -> int:
        p = subprocess.Popen(cmd)
        p.communicate()
        return p.returncode

    def on_table_operation(self, table_name):
        services = self.table_service.get(table_name, {})
        for service in services:
            commands = self.service_commands.get(service, {})
            restart_comand = commands.get('restart-command')
            if restart_comand:
                rc = self.exec_command(restart_comand)
                if rc != 0:
                    raise GenericConfigUpdaterError(f"Restart command failed: {restart_comand}, rc={rc}")
            validate_command = commands.get('validate-commands')
            if validate_command:
                rc = self.exec_command(validate_command)
                if rc != 0:
                    raise GenericConfigUpdaterError(f"Validate command failed: {validate_command}, rc={rc}")

    def on_table_operation_lazy(self, table_name):
        # Optimze: reduce the duplicated restarting in a batch
        if table_name != self.previous_table_name:
            self.on_table_operation(self.previous_table_name)
            self.previous_table_name = table_name

    def _apply_entry(self, op: PatchOperation):
        parts = op.pointer.parts
        entry = self.config_db.get_entry(parts[0], parts[1])
        oldtree = entry
        for part in parts[1::-1]:
            oldtree = { part: oldtree }
        op.apply(oldtree)
        self.config_db.set_entry(parts[0], parts[1], entry)

    def apply(self, change: JsonChange):
        ## Note: ordering of applying the modifications in a JsonChange is arbitrary

        ## TODO: The implementation is not optimized.
        ## Please folllow the stages in design doc https://github.com/Azure/SONiC/blob/master/doc/config-generic-update-rollback/Json_Change_Application_Design.md#22-functional-description
        patch = change.patch

        self.previous_table_name = None
        # JsonChange is a list of PatchOperation
        for op in patch._ops:
            parts = op.pointer.parts
            nparts = len(parts)
            value = op.operation.get('value', None)


            tree = value
            for part in parts[::-1]:
                tree = { part: tree }
            if isinstance(op, AddOperation):
                self.config_db.mod_config(tree)
                if nparts == 2:
                    # Added a key in a table
                    self.on_table_operation_lazy(parts[0])
            elif isinstance(op, RemoveOperation):
                if nparts == 1:
                    # Delete a table
                    self.config_db.delete_table(parts[0])
                    self.on_table_operation_lazy(parts[0])
                elif nparts == 2:
                    # Delete a key in a table
                    self.config_db.set_entry(parts[0], parts[1], None)
                    self.on_table_operation_lazy(parts[0])
                else:
                    self._apply_entry(op)
            elif isinstance(op, ReplaceOperation):
                if nparts <= 2:
                    raise NotImplementedError("ConfigDb does not support replace a table name or key name")
                else:
                    self._apply_entry(op)
            else:
                raise NotImplementedError("Not supported PatchOperation type")
