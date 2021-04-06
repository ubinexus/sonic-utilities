import json
import jsonpatch
import sonic_yang
import os
import copy
from enum import Enum
from swsssdk import ConfigDBConnector
from imp import load_source
load_source('sonic_cfggen', '/usr/local/bin/sonic-cfggen')
from sonic_cfggen import deep_update, FormatConverter

class JsonChange:
    # TODO: Implement JsonChange
    pass

class ConfigLock:
    def acquire_lock(self):
        # TODO: Implement ConfigLock
        pass

    def release_lock(self):
        # TODO: Implement ConfigLock
        pass

class PatchOrderer:
    def order(patch):
        # TODO: Implement patch orderer
        pass

class ChangeApplier:
    def apply(change):
        # TODO: Implement change applier
        pass

YANG_DIR = "/usr/local/yang-models"
class ConfigWrapper:
    def __init__(self, default_config_db_connector = None, yang_dir = YANG_DIR):
        self.default_config_db_connector = default_config_db_connector
        self.yang_dir = YANG_DIR

    def get_config_db_as_json(self):
        config_db = self.__create_and_connect_config_db()
        data = dict()
        deep_update(data, FormatConverter.db_to_output(config_db.get_config()))
        return FormatConverter.to_serialized(data)

    def get_sonic_yang_as_json(self):
        config_db_json = self.get_config_db_as_json()
        return self.convert_config_db_to_sonic_yang(config_db_json)

    def convert_config_db_to_sonic_yang(self, config_db_as_json):
        sy = sonic_yang.SonicYang(self.yang_dir)
        sy.loadYangModel()

        # Crop config_db tables that do not have sonic yang models
        cropped_config_db_as_json = self.crop_tables_without_yang(config_db_as_json)

        sonic_yang_as_json = dict()

        sy._xlateConfigDBtoYang(cropped_config_db_as_json, sonic_yang_as_json)

        return sonic_yang_as_json

    def convert_sonic_yang_to_config_db(self, sonic_yang_as_json):
        sy = sonic_yang.SonicYang(self.yang_dir)
        sy.loadYangModel()

        # replace container of the format 'module:table' with just 'table'
        new_sonic_yang_json = {}
        for module_top in sonic_yang_as_json.keys():
            new_sonic_yang_json[module_top] = {}
            for container in sonic_yang_as_json[module_top].keys():
                table = container.split(':')[1]
                new_sonic_yang_json[module_top][table] = sonic_yang_as_json[module_top][container]

        config_db_as_json = dict()
        sy.xlateJson = new_sonic_yang_json
        sy.revXlateJson = config_db_as_json
        sy._revXlateYangtoConfigDB(new_sonic_yang_json, config_db_as_json)

        return config_db_as_json

    def validate_sonic_yang_config(self, sonic_yang_as_json):
        config_db_as_json = self.convert_sonic_yang_to_config_db(sonic_yang_as_json)

        sy = sonic_yang.SonicYang(self.yang_dir)
        sy.loadYangModel()

        try:
            sy.loadData(config_db_as_json)

            sy.validate_data_tree()
            return True
        except Exception as ex:
            return False

    def crop_tables_without_yang(self, config_db_as_json):
        sy = sonic_yang.SonicYang(self.yang_dir)
        sy.loadYangModel()

        sy.jIn = copy.deepcopy(config_db_as_json)

        sy.tablesWithOutYang = dict()

        sy._cropConfigDB()

        return sy.jIn

    def __create_and_connect_config_db(self):
        if self.default_config_db_connector != None:
            return self.default_config_db_connector

        db_kwargs = dict()
        data = dict()
        config_db = ConfigDBConnector(**db_kwargs)
        config_db.connect()
        return config_db

class DryRunConfigWrapper(ConfigWrapper):
    # TODO: implement DryRunConfigWrapper
    # This class will simulate all read/write operations to ConfigDB on a virtual storage unit.
    pass

class PatchWrapper:
    def __init__(self, config_wrapper = ConfigWrapper()):
        self.config_wrapper = config_wrapper

    def validate_config_db_patch(self, patch):
        config_db = {}
        for operation in patch:
            tokens = operation['path'].split('/')[1:]
            if len(tokens) == 0: # Modifying whole config_db
                tables_dict = {table_name: {} for table_name in operation['value']}
                config_db.update(tables_dict)
            elif not tokens[0]: # Not empty
                raise Exception("Table name in patch cannot be empty")
            else:
                config_db[tokens[0]] = {}

        cropped_config_db = self.config_wrapper.crop_tables_without_yang(config_db)

        # valid if no tables dropped during cropping
        return len(cropped_config_db.keys()) == len(config_db.keys())

    def verify_same_json(self, expected, actual):
        # patch will be [] if no diff, [] evaluates to False
        return not jsonpatch.make_patch(expected, actual)

    def generate_patch(self, current, target):
        return jsonpatch.make_patch(current, target)

    def simulate_patch(self, patch, jsonconfig):
        return patch.apply(jsonconfig)

    def convert_config_db_patch_to_sonic_yang_patch(self, patch):
        if not(self.validate_config_db_patch(patch)):
            raise Exception(f"Given patch is not valid")

        current_config_db = self.config_wrapper.get_config_db_as_json()
        target_config_db = self.simulate_patch(patch, current_config_db)

        current_yang = self.config_wrapper.convert_config_db_to_sonic_yang(current_config_db)
        target_yang = self.config_wrapper.convert_config_db_to_sonic_yang(target_config_db)

        return self.generate_patch(current_yang, target_yang)

class ConfigFormat(Enum):
    SONICYANG = 1
    CONFIGDB = 2

class PatchApplier:
    def __init__( \
        self, \
            patchorderer = PatchOrderer(), \
                changeapplier = ChangeApplier(), \
                    config_wrapper = ConfigWrapper(), \
                        patch_wrapper = PatchWrapper()):
        self.patchorderer = patchorderer
        self.changeapplier = changeapplier
        self.config_wrapper = config_wrapper
        self.patch_wrapper = patch_wrapper

    def apply(self, patch):
        # 1. Get old config as SONiC Yang
        old_config = self.config_wrapper.get_sonic_yang_as_json()

        # 2. Generate target config
        target_config = self.patch_wrapper.simulate_patch(patch, old_config)

        # 3. Validate target config
        if not(self.config_wrapper.validate_sonic_yang_config(target_config)):
            raise Exception(f"The given patch is not valid")

        # 4. Generate list of changes to apply
        changes = self.patchorderer.order(patch)

        # 5. Apply changes in order
        for change in changes:
            self.changeapplier.apply(change)

        # 6. Validate config updated successfully
        new_config = self.config_wrapper.get_sonic_yang_as_json()
        if not(self.patch_wrapper.verify_same_json(target_config, new_config)):
            raise Exception(f"After applying patch to config, there are still some parts not updated")

class ConfigReplacer:
    def __init__(self, patch_applier = PatchApplier(), config_wrapper = ConfigWrapper(), patch_wrapper = PatchWrapper()):
        self.patch_applier = patch_applier
        self.config_wrapper = config_wrapper
        self.patch_wrapper = patch_wrapper

    def replace(self, target_config):
        if not(self.config_wrapper.validate_sonic_yang_config(target_config)):
            raise Exception(f"The given target config is not valid")

        old_config = self.config_wrapper.get_sonic_yang_as_json()
        patch = self.patch_wrapper.generate_patch(old_config, target_config)

        self.patch_applier.apply(patch)

        new_config = self.config_wrapper.get_sonic_yang_as_json()
        if not(self.patch_wrapper.verify_same_json(target_config, new_config)):
            raise Exception(f"After applying patch to config, there is still some parts not updated")

CHECKPOINTS_DIR = "/etc/sonic/checkpoints"
CHECKPOINT_EXT = ".cp.json"
class FileSystemConfigRollbacker:
    def __init__( \
            self, \
                checkpoints_dir = CHECKPOINTS_DIR, \
                    config_replacer = ConfigReplacer(), \
                        config_wrapper = ConfigWrapper()):
        self.checkpoints_dir = checkpoints_dir
        self.config_replacer = config_replacer
        self.config_wrapper = config_wrapper

    def rollback(self, checkpoint_name):
        if not self.__check_checkpoint_exists(checkpoint_name):
            raise Exception(f"Checkpoint '{checkpoint_name}' does not exist")

        target_config = self.__get_checkpoint_content(checkpoint_name)

        self.config_replacer.replace(target_config)

    def checkpoint(self, checkpoint_name):
        json_content = self.config_wrapper.get_sonic_yang_as_json()

        path = self.__get_checkpoint_full_path(checkpoint_name)

        self.__ensure_checkpoints_dir_exists()

        self.__save_json_file(path, json_content)

    def list_checkpoints(self):
        if not self.__checkpoints_dir_exist():
            return []

        return self.__get_checkpoint_names()

    def delete_checkpoint(self, checkpoint_name):
        if not self.__check_checkpoint_exists(checkpoint_name):
            raise Exception("Checkpoint does not exist")

        self.__delete_checkpoint(checkpoint_name)

    def __ensure_checkpoints_dir_exists(self):
        os.makedirs(self.checkpoints_dir, exist_ok=True)

    def __save_json_file(self, path, json_content):
        with open(path, "w") as fh:
            fh.write(json.dumps(json_content))

    def __get_checkpoint_content(self, checkpoint_name):
        path = self.__get_checkpoint_full_path(checkpoint_name)
        with open(path) as fh:
            text = fh.read()
            return json.loads(text)

    def __get_checkpoint_full_path(self, name):
        return os.path.join(self.checkpoints_dir, f"{name}{CHECKPOINT_EXT}")

    def __get_checkpoint_names(self):
        return [f[:-len(CHECKPOINT_EXT)] for f in os.listdir(self.checkpoints_dir) if f.endswith(CHECKPOINT_EXT)]

    def __checkpoints_dir_exist(self):
        return os.path.isdir(self.checkpoints_dir)

    def __check_checkpoint_exists(self, name):
        path = self.__get_checkpoint_full_path(name)
        return os.path.isfile(path)

    def __delete_checkpoint(self, name):
        path = self.__get_checkpoint_full_path(name)
        return os.remove(path)

class Decorator(PatchApplier, ConfigReplacer, FileSystemConfigRollbacker):
    def __init__(self, decorated_patch_applier=None, decorated_config_replacer=None, decorated_config_rollbacker=None):
        # initing base classes to make LGTM happy
        PatchApplier.__init__(self)
        ConfigReplacer.__init__(self)
        FileSystemConfigRollbacker.__init__(self)

        self.decorated_patch_applier = decorated_patch_applier
        self.decorated_config_replacer = decorated_config_replacer
        self.decorated_config_rollbacker = decorated_config_rollbacker

    def apply(self, patch):
        self.decorated_patch_applier.apply(patch)

    def replace(self, target_config):
        self.decorated_config_replacer.replace(target_config)

    def rollback(self, checkpoint_name):
        self.decorated_config_rollbacker.rollback(checkpoint_name)

    def checkpoint(self, checkpoint_name):
        self.decorated_config_rollbacker.checkpoint(checkpoint_name)

    def list_checkpoints(self):
        return self.decorated_config_rollbacker.list_checkpoints()

    def delete_checkpoint(self, checkpoint_name):
        self.decorated_config_rollbacker.delete_checkpoint(checkpoint_name)

class ConfigDbDecorator(Decorator):
    def __init__(self, patch_wrapper, config_wrapper, decorated_patch_applier=None, decorated_config_replacer=None):
        Decorator.__init__(self, decorated_patch_applier, decorated_config_replacer)

        self.patch_wrapper = patch_wrapper
        self.config_wrapper = config_wrapper

    def apply(self, patch):
        yang_patch = self.patch_wrapper.convert_config_db_patch_to_sonic_yang_patch(patch)
        Decorator.apply(self, yang_patch)

    def replace(self, target_config):
        yang_target_config = self.config_wrapper.convert_config_db_to_sonic_yang(target_config)
        Decorator.replace(self, yang_target_config)

class ConfigLockDecorator(Decorator):
    def __init__( \
        self, \
            decorated_patch_applier=None, \
                decorated_config_replacer=None, \
                    decorated_config_rollbacker=None, \
                        config_lock = ConfigLock()):
        Decorator.__init__(self, decorated_patch_applier, decorated_config_replacer, decorated_config_rollbacker)

        self.config_lock = config_lock

    def apply(self, patch):
        self.execute_write_action(Decorator.apply, self, patch)
        
    def replace(self, target_config):
        self.execute_write_action(Decorator.replace, self, target_config)

    def rollback(self, checkpoint_name):
        self.execute_write_action(Decorator.rollback, self, checkpoint_name)

    def checkpoint(self, checkpoint_name):
        self.execute_write_action(Decorator.checkpoint, self, checkpoint_name)

    def execute_write_action(self, action, *args):
        self.config_lock.acquire_lock()
        action(*args)
        self.config_lock.release_lock()

class GenericUpdateFactory:
    def create_patch_applier(self, config_format, verbose, dry_run):
        self.init_verbose_logging(verbose)

        config_wrapper = self.get_config_wrapper(dry_run)

        patch_applier = PatchApplier(config_wrapper=config_wrapper)

        patch_wrapper = PatchWrapper(config_wrapper)

        if config_format == ConfigFormat.CONFIGDB:
            patch_applier = \
                ConfigDbDecorator( \
                    decorated_patch_applier = patch_applier, patch_wrapper=patch_wrapper, config_wrapper=config_wrapper)
        elif config_format == ConfigFormat.SONICYANG:
            pass
        else:
            raise ValueError(f"config-format '{config_format}' is not supported")

        if not dry_run:
            patch_applier = ConfigLockDecorator(decorated_patch_applier = patch_applier)

        return patch_applier

    def create_config_replacer(self, config_format, verbose, dry_run):
        self.init_verbose_logging(verbose)

        config_wrapper = self.get_config_wrapper(dry_run)

        patch_applier = PatchApplier(config_wrapper=config_wrapper)

        patch_wrapper = PatchWrapper(config_wrapper)

        config_replacer = ConfigReplacer(patch_applier=patch_applier, config_wrapper=config_wrapper)
        if config_format == ConfigFormat.CONFIGDB:
            config_replacer = \
                ConfigDbDecorator( \
                    decorated_config_replacer = config_replacer, patch_wrapper=patch_wrapper, config_wrapper=config_wrapper)
        elif config_format == ConfigFormat.SONICYANG:
            pass
        else:
            raise ValueError(f"config-format '{config_format}' is not supported")

        if not dry_run:
            config_replacer = ConfigLockDecorator(decorated_config_replacer = config_replacer)

        return config_replacer

    def create_config_rollbacker(self, verbose, dry_run):
        self.init_verbose_logging(verbose)

        config_wrapper = self.get_config_wrapper(dry_run)

        patch_applier = PatchApplier(config_wrapper=config_wrapper)
        config_replacer = ConfigReplacer(config_wrapper=config_wrapper, patch_applier=patch_applier)
        config_rollbacker = FileSystemConfigRollbacker(config_wrapper = config_wrapper, config_replacer = config_replacer)

        if not dry_run:
            config_rollbacker = ConfigLockDecorator(decorated_config_rollbacker = config_rollbacker)

        return config_rollbacker

    def init_verbose_logging(self, verbose):
        # TODO: implement verbose logging
        # Usually logs have levels such as: error, warning, info, debug.
        # By default all log levels should show up to the user, except debug.
        # By allowing verbose logging, debug msgs will also be shown to the user.
        pass

    def get_config_wrapper(self, dry_run):
        if dry_run:
            return DryRunConfigWrapper()
        else:
            return ConfigWrapper()

class GenericUpdater:
    def __init__(self, generic_update_factory = GenericUpdateFactory()):
        self.generic_update_factory = generic_update_factory

    def apply_patch(self, patch, config_format, verbose, dry_run):
        patch_applier = self.generic_update_factory.create_patch_applier(config_format, verbose, dry_run)
        patch_applier.apply(patch)

    def replace(self, target_config, config_format, verbose, dry_run):
        config_replacer = self.generic_update_factory.create_config_replacer(config_format, verbose, dry_run)
        config_replacer.replace(target_config)

    def rollback(self, checkpoint_name, verbose, dry_run):
        config_rollbacker = self.generic_update_factory.create_config_rollbacker(verbose, dry_run)
        config_rollbacker.rollback(checkpoint_name)

    def checkpoint(self, checkpoint_name, verbose, dry_run):
        config_rollbacker = self.generic_update_factory.create_config_rollbacker(verbose, dry_run)
        config_rollbacker.checkpoint(checkpoint_name)

    def delete_checkpoint(self, checkpoint_name, verbose, dry_run):
        config_rollbacker = self.generic_update_factory.create_config_rollbacker(verbose, dry_run)
        config_rollbacker.delete_checkpoint(checkpoint_name)

    def list_checkpoints(self, verbose, dry_run):
        config_rollbacker = self.generic_update_factory.create_config_rollbacker(verbose, dry_run)
        return config_rollbacker.list_checkpoints()