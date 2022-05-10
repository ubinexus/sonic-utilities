import json
import sonic_yang
import subprocess
import copy

YANG_DIR = "/usr/local/yang-models"

class YangValidationService:
    def __init__(self, yang_dir = YANG_DIR):
        self.yang_dir = YANG_DIR
        self.sonic_yang_with_loaded_models = None

    def get_config_db_as_json(self):
        cmd = "show runningconfiguration all"
        result = subprocess.Popen(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        text, err = result.communicate()
        return_code = result.returncode
        if return_code:
            raise RuntimeError("Failed to get running config, Return Code: {}, Error: {}".format(return_code, err))
        return json.loads(text)

    def create_sonic_yang_with_loaded_models(self):
        if self.sonic_yang_with_loaded_models is None:
            loaded_models_sy = sonic_yang.SonicYang(self.yang_dir)
            loaded_models_sy.loadYangModel()
            self.sonic_yang_with_loaded_models = loaded_models_sy

        return copy.copy(self.sonic_yang_with_loaded_models)
    
    def validate_config_db_config(self, config_json):
        sy = self.create_sonic_yang_with_loaded_models()
        try:
            tmp_config_json = copy.deepcopy(config_json)
            sy.loadData(tmp_config_json)
            sy.validate_data_tree()
            return True
        except sonic_yang.SonicYangException as ex:
            return False
        return False

    def validate_set_entry(self, table, key, data):
        config_json = self.get_config_db_as_json()
        if not self.validate_config_db_config(config_json):
            return False
        if data is not None:
            config_json[table][key] = data
        if not self.validate_config_db_config(config_json):
            return False
        return True

  
