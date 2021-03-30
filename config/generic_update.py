import jsonpatch
import sonic_yang
import os
load_source('sonic_cfggen', '/usr/local/bin/sonic-cfggen')
from sonic_cfggen import deep_update, FormatConverter

class JsonChange:
    def __init__(self, patch):
        self.patch = patch

    def apply(self, current_json):
        return self.patch.apply(current_json)

    def __str__(self):
        return f"{self.patch}"

class ConfigLocker():
    def acquire_lock(self):
        # TODO: Implement ConfigLocker
        pass

    def release_lock(self):
        # TODO: Implement ConfigLocker
        pass

class NoOpConfigLocker(ConfigLocker):
    def acquire_lock(self):
        pass
    def release_lock(self):
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
    def get_current_config(self):
        config_db_json = __get_config_db_as_json()
        return __convert_config_db_to_yang(config_db_json)

    def validate_config(self, yang_as_json):
        config_db_as_json = __convert_yang_to_config_db(yang_as_json)
        config_as_yang

        sy = sonic_yang.SonicYang(YANG_DIR, debug=debug)
        sy.loadYangModel()
        sy.loadData(config_db_as_json)

        try:
            sy.validate_data_tree()
            return True
        except Exception as ex:
            return False

    def get_config_db_as_json(self):
        db_kwargs = dict(); data = dict()
        configdb = ConfigDBConnector(**db_kwargs)
        configdb.connect()
        deep_update(data, FormatConverter.db_to_output(configdb.get_config()))
        return FormatConverter.to_serialized(data)

    def convert_config_db_to_yang(self, config_db_as_json):
        sy = sonic_yang.SonicYang(YANG_DIR, debug=debug)
        sy.loadYangModel()

        yang_as_json = dict()
        sy._xlateConfigDBtoYang(config_db_as_json, yang_as_json)

        return yang_as_json

    def convert_yang_to_config_db(self, yang_as_json):
        sy = sonic_yang.SonicYang(YANG_DIR, debug=debug)
        sy.loadYangModel()

        config_db_as_json = dict()
        sy.xlateJson = yang_as_json
        sy.revXlateJson = config_db_as_json
        sy._revXlateYangtoConfigDB(config_db_as_json, yang_as_json)

        return yang_as_json

class PatchApplier:
    def __init__(self, patchorderer = PatchOrderer(), changeapplier = ChangeApplier(), configlocker = ConfigLocker(), configwrapper = ConfigWrapper()):
        self.patchorderer = patchorderer
        self.changeapplier = changeapplier
        self.configlocker = configlocker

    def apply(self, patch, format, verbose, dry_run):
        if format == "ConfigDB":
            yang_patch = __convert_config_db_patch_to_yang_patch(patch)
        elif format == "YANG":
            yang_patch = patch
        else:
            raise AttributeError(f"format argument value '{format}', the supported values are 'ConfigDB' or 'YANG'")

        if verbose:
            # TODO: Implement verbose logging
            raise NotImplementedError

        if dry_run:
            # TODO: Implement dry-run
            raise NotImplementedError

        __acquire_config_lock()
        old_config = __get_current_config()
        target_config = __simulate_patch(patch, old_config)

        if not(__validate(target_config)):
            raise Exception(f"The given patch is not valid")

        changes = __order_patch(patch)
        for change in changes:
            __apply_change(change)

        new_config = __get_current_config()
        if not(__verify_same_json(target_config, new_config)):
            raise Exception(f"After applying patch to config, there is still some parts not updated")
        __release_config_lock()

    def __convert_config_db_patch_to_yang_patch(patch):
        current_config_db = self.configwrapper.get_config_db_as_json()
        target_config_db = self.__simulate_patch(patch, current_config_db)

        current_yang = self.configwrapper.convert_config_db_to_yang(current_config_db)
        target_yang = self.configwrapper.convert_config_db_to_yang(target_config_db)

        return __generate_patch(current_yang, target_yang)

    def __acquire_config_lock():
        self.configlocker.acquire_lock()

    def __release_config_lock():
        self.configlocker.release_lock()

    def __get_current_config():
        self.configwrapper.get_current_config()

    def __simulate_patch(patch, jsonconfig):
        return patch.apply(jsonconfig)

    def __validate(target_config):
        return self.configwrapper.validate_config(target_config)

    def __order_patch(patch):
        return self.patchorderer.order(patch)

    def __apply_change(change):
        return self.changeapplier.apply(change)

    def __generate_patch(current, target):
        return jsonpatch.make_patch(current, target)

    def __verify_same_json(expected_json, actual_json):
        return jsonpatch.make_patch(expected_json, actual_json) == []

class ConfigReplacer:
    def __init__(self, patchorderer = PatchOrderer(), changeapplier = ChangeApplier(), configlocker = ConfigLocker(), configwrapper = ConfigWrapper()):
        # NOTE: patch-applier receives a NoOpConfigLocker
        self.patchapplier = PatchApplier(patchorder, changeapplier, NoOpConfigLocker(), configwrapper)
        self.configwrapper = configwrapper
        self.configlocker = configlocker

    def replace(self, full_json, format, verbose, dry_run):
        if format == "ConfigDB":
            yang_as_json = convert_config_db_to_yang(full_json)
        elif format == "YANG":
            yang_as_json = full_json
        else:
            raise AttributeError(f"format argument value '{format}', the supported values are 'ConfigDB' or 'YANG'")

        if verbose:
            # TODO: Implement verbose logging
            raise NotImplementedError

        if dry_run:
            # TODO: Implement dry-run
            raise NotImplementedError

        __acquire_config_lock()
        if not(__validate(target_config)):
            raise Exception(f"The given target config is not valid")

        old_config = __get_current_config()
        patch = __generate_patch(old_config, target_config)

        __apply_patch(patch, verbose, dry_run)

        new_config = __get_current_config()
        if not(__verify_same_json(target_config, new_config)):
            raise Exception(f"After applying patch to config, there is still some parts not updated")

        __release_config_lock()

    def __acquire_config_lock():
        self.configlocker.acquire_lock()

    def __release_config_lock():
        self.configlocker.release_lock()

    def __validate(target_config):
        return self.configwrapper.validate_config(target_config)

    def __get_current_config():
        self.configwrapper.get_current_config()

    def __generate_patch(current, target):
        return jsonpatch.make_patch(current, target)

    def __apply_patch(patch, verbose, dry_run):
        self.patchapplier.apply(patch, verbose, dry_run)

    def __verify_same_json(expected_json, actual_json):
        return jsonpatch.make_patch(expected_json, actual_json) == []

CHECKPOINTS_DIR = "/etc/sonic/checkpoints"
CHECKPOINT_EXT = ".cp.json"
class FileSystemRollbacker:
    def __init__(self, patchorderer = PatchOrderer(), changeapplier = ChangeApplier(), configlocker = ConfigLocker(), configwrapper = ConfigWrapper()):
        # NOTE: config-replacer receives a NoOpConfigLocker
        self.configreplacer = PatchApplier(patchorder, changeapplier, NoOpConfigLocker(), configwrapper)
        self.configlocker = configlocker

    def rollback(self, checkpoint_name, verbose, dry_run):
        if verbose:
            # TODO: Implement verbose logging
            raise NotImplementedError

        if dry_run:
            # TODO: Implement dry-run
            raise NotImplementedError

        __acquire_config_lock()
        target_config = __get_checkpoint_content(checkpoint_name)

        __config_replace(target_config)

        __release_lock()

    def checkpoint(self, checkpoint_name, verbose, dry_run):
        if verbose:
            # TODO: Implement verbose logging
            raise NotImplementedError

        if dry_run:
            # TODO: Implement dry-run
            raise NotImplementedError

        __acquire_config_lock()
        current_config = _get_current_config()

        __save_checkpoint_content(current_config)

        __release_lock()

    def list_checkpoints(self, verbose, dry_run):
        if verbose:
            # TODO: Implement verbose logging
            raise NotImplementedError

        if dry_run:
            # TODO: Implement dry-run
            raise NotImplementedError

        if not(__checkpoints_dir_exist()):
            return []

        return __get_checkpoint_names()

    def delete_checkpoint(self, checkpoint_name, verbose, dry_run):
        if verbose:
            # TODO: Implement verbose logging
            raise NotImplementedError

        if dry_run:
            # TODO: Implement dry-run
            raise NotImplementedError

        if not(__check_checkpoint_exists()):
            raise Exception("Checkpoint does not exist")

        __delete_checkpoint(checkpoint_name)

    def __acquire_config_lock():
        self.configlocker.acquire_lock()

    def __release_config_lock():
        self.configlocker.release_lock()

    def __get_current_config():
        self.configwrapper.get_current_config()

    def __ensure_checkpoints_dir_exists(self):
        os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

    def __save_checkpoint_content(name, content):
        __ensure_checkpoints_dir_exists()
        path = __get_checkpoint_full_path(name)
        with open(path, "w") as fh:
            fh.write(text)

    def __get_checkpoint_content(name):
        path = __get_checkpoint_full_path(name)
        with open(path) as fh:
            text = fh.read()
            return json.loads(text)

    def __get_checkpoint_full_path(name)
        return os.path.join(CHECKPOINTS_DIR, name, CHECKPOINT_EXT)

    def __config_replace(target_config):
        self.configreplacer.replace(target_config)

    def __get_checkpoint_names():
        return [f for f in listdir(CHECKPOINTS_DIR) if f.endswith(CHECKPOINT_EXT)]

    def __checkpoints_dir_exist():
        os.path.isdir(CHECKPOINTS_DIR)

    def __check_checkpoint_exists(name):
        path = __get_checkpoint_full_path(name)
        return os.path.isfile(path)

    def __delete_checkpoint(name):
        path = __get_checkpoint_full_path(name)
        return os.remove(path)
