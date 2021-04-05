import json
import jsonpatch
import os
import shutil
import unittest
from imp import load_source
from unittest.mock import Mock, call
load_source('generic_update', \
    os.path.join(os.path.dirname(__file__), '..', 'config', 'generic_update.py'))
import generic_update

class MockSideEffectDict:
    def __init__(self, map):
        self.map = map

    def side_effect_func(self, *args):
        l = [str(arg) for arg in args]
        key = tuple(l)
        value = self.map.get(key)
        if value == None:
            raise ValueError(f"Given arguments were not found in arguments map.\n  Arguments: {key}\n  Map: {self.map}")

        return value

def create_side_effect_dict(map):
    return MockSideEffectDict(map).side_effect_func

class TestConfigWrapper(unittest.TestCase):
    def test_ctor__default_values_set(self):
        configwrapper = generic_update.ConfigWrapper()

        self.assertEqual(None, configwrapper.default_config_db_connector)
        self.assertEqual("/usr/local/yang-models", generic_update.YANG_DIR)

    def test_get_config_db_as_json__returns_config_db_as_json(self):
        # Arrange
        config_db_connector_mock = self.__get_config_db_connector_mock(CONFIG_DB_AS_DICT)
        configwrapper = generic_update.ConfigWrapper(default_config_db_connector = config_db_connector_mock)
        expected = CONFIG_DB_AS_JSON

        # Act
        actual = configwrapper.get_config_db_as_json()

        # Assert
        self.assertDictEqual(expected, actual)

    def test_get_sonic_yang_as_json__returns_sonic_yang_as_json(self):
        # Arrange
        config_db_connector_mock = self.__get_config_db_connector_mock(CONFIG_DB_AS_DICT)
        configwrapper = generic_update.ConfigWrapper(default_config_db_connector = config_db_connector_mock)
        expected = SONIC_YANG_AS_JSON

        # Act
        actual = configwrapper.get_sonic_yang_as_json()

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_config_db_to_sonic_yang__empty_config_db__returns_empty_sonic_yang(self):
        # Arrange
        configwrapper = generic_update.ConfigWrapper()
        expected = {}

        # Act
        actual = configwrapper.convert_config_db_to_sonic_yang({})

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_config_db_to_sonic_yang__non_empty_config_db__returns_sonic_yang_as_json(self):
        # Arrange
        configwrapper = generic_update.ConfigWrapper()
        expected = SONIC_YANG_AS_JSON

        # Act
        actual = configwrapper.convert_config_db_to_sonic_yang(CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_sonic_yang_to_config_db__empty_sonic_yang__returns_empty_config_db(self):
        # Arrange
        configwrapper = generic_update.ConfigWrapper()
        expected = {}

        # Act
        actual = configwrapper.convert_sonic_yang_to_config_db({})

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_sonic_yang_to_config_db__non_empty_sonic_yang__returns_config_db_as_json(self):
        # Arrange
        configwrapper = generic_update.ConfigWrapper()
        expected = CROPPED_CONFIG_DB_AS_JSON

        # Act
        actual = configwrapper.convert_sonic_yang_to_config_db(SONIC_YANG_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_validate_sonic_yang_config__valid_config__returns_true(self):
        # Arrange
        configwrapper = generic_update.ConfigWrapper()
        expected = True

        # Act
        actual = configwrapper.validate_sonic_yang_config(SONIC_YANG_AS_JSON)

        # Assert
        self.assertEqual(expected, actual)

    def test_validate_sonic_yang_config__invvalid_config__returns_false(self):
        # Arrange
        configwrapper = generic_update.ConfigWrapper()
        expected = False

        # Act
        actual = configwrapper.validate_sonic_yang_config(SONIC_YANG_AS_JSON_INVALID)

        # Assert
        self.assertEqual(expected, actual)

    def test_crop_tables_without_yang__returns_cropped_config_db_as_json(self):
        # Arrange
        configwrapper = generic_update.ConfigWrapper()
        expected = CROPPED_CONFIG_DB_AS_JSON

        # Act
        actual = configwrapper.crop_tables_without_yang(CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def __get_config_db_connector_mock(self, config_db_as_dict):
        mock_connector = Mock()
        mock_connector.get_config.return_value = config_db_as_dict
        return mock_connector

class TestPatchWrapper(unittest.TestCase):
    def test_validate_config_db_patch__table_without_yang_model__returns_false(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()
        patch = [ { 'op': 'remove', 'path': '/TABLE_WITHOUT_YANG' } ]
        expected = False

        # Act
        actual = patchwrapper.validate_config_db_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_validate_config_db_patch__table_with_yang_model__returns_true(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()
        patch = [ { 'op': 'remove', 'path': '/ACL_TABLE' } ]
        expected = True

        # Act
        actual = patchwrapper.validate_config_db_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__invalid_config_db_patch__failure(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()
        patch = [ { 'op': 'remove', 'path': '/TABLE_WITHOUT_YANG' } ]

        # Act and Assert
        self.assertRaises(Exception, patchwrapper.convert_config_db_patch_to_sonic_yang_patch, patch)

    def test_same_patch__no_diff__returns_true(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()

        # Act and Assert
        self.assertTrue(patchwrapper.verify_same_json(CONFIG_DB_AS_JSON, CONFIG_DB_AS_JSON))

    def test_same_patch__diff__returns_false(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()

        # Act and Assert
        self.assertFalse(patchwrapper.verify_same_json(CONFIG_DB_AS_JSON, CROPPED_CONFIG_DB_AS_JSON))

    def test_generate_patch__no_diff__empty_patch(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()

        # Act
        patch = patchwrapper.generate_patch(CONFIG_DB_AS_JSON, CONFIG_DB_AS_JSON)

        # Assert
        self.assertFalse(patch)

    def test_simulate_patch__empty_patch__no_changes(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()
        patch = jsonpatch.JsonPatch([])
        expected = CONFIG_DB_AS_JSON

        # Act
        actual = patchwrapper.simulate_patch(patch, CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_simulate_patch__non_empty_patch__changes_applied(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()
        patch = SINGLE_OPERATION_CONFIG_DB_PATCH
        expected = SINGLE_OPERATION_CONFIG_DB_PATCH.apply(CONFIG_DB_AS_JSON)

        # Act
        actual = patchwrapper.simulate_patch(patch, CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_generate_patch__diff__non_empty_patch(self):
        # Arrange
        patchwrapper = generic_update.PatchWrapper()
        after_update_json = SINGLE_OPERATION_CONFIG_DB_PATCH.apply(CONFIG_DB_AS_JSON)
        expected = SINGLE_OPERATION_CONFIG_DB_PATCH

        # Act
        actual = patchwrapper.generate_patch(CONFIG_DB_AS_JSON, after_update_json)

        # Assert
        self.assertTrue(actual)
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__empty_patch__returns_empty_patch(self):
        # Arrange
        configwrapper = self.__get_configwrapper_mock(CONFIG_DB_AS_DICT)
        patchwrapper = generic_update.PatchWrapper(configwrapper = configwrapper)
        patch = jsonpatch.JsonPatch([])
        expected = jsonpatch.JsonPatch([])

        # Act
        actual = patchwrapper.convert_config_db_patch_to_sonic_yang_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__single_operation_patch__returns_sonic_yang_patch(self):
        # Arrange
        configwrapper = self.__get_configwrapper_mock(CONFIG_DB_AS_DICT)
        patchwrapper = generic_update.PatchWrapper(configwrapper = configwrapper)
        patch = SINGLE_OPERATION_CONFIG_DB_PATCH
        expected = SINGLE_OPERATION_SONIC_YANG_PATCH

        # Act
        actual = patchwrapper.convert_config_db_patch_to_sonic_yang_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__multiple_operations_patch__returns_sonic_yang_patch(self):
        # Arrange
        configwrapper = self.__get_configwrapper_mock(CONFIG_DB_AS_DICT)
        patchwrapper = generic_update.PatchWrapper(configwrapper = configwrapper)
        config_db_patch = MULTI_OPERATION_CONFIG_DB_PATCH

        # Act
        sonic_yang_patch = patchwrapper.convert_config_db_patch_to_sonic_yang_patch(config_db_patch)

        # Assert
        self.__assert_same_patch(config_db_patch, sonic_yang_patch, configwrapper, patchwrapper)

    def __assert_same_patch(self, config_db_patch, sonic_yang_patch, configwrapper, patchwrapper):
        sonic_yang = configwrapper.get_sonic_yang_as_json()
        config_db = configwrapper.get_config_db_as_json()

        after_update_sonic_yang = patchwrapper.simulate_patch(sonic_yang_patch, sonic_yang)
        after_update_config_db = patchwrapper.simulate_patch(config_db_patch, config_db)

        after_update_config_db_as_sonic_yang = \
            configwrapper.convert_config_db_to_sonic_yang(after_update_config_db)

        self.assertTrue(patchwrapper.verify_same_json(after_update_sonic_yang, after_update_config_db_as_sonic_yang))

    def __get_configwrapper_mock(self, config_db_as_dict):
        config_db_connector_mock = self.__get_config_db_connector_mock(config_db_as_dict)
        configwrapper = generic_update.ConfigWrapper(default_config_db_connector = config_db_connector_mock)
        return configwrapper

    def __get_config_db_connector_mock(self, config_db_as_dict):
        mock_connector = Mock()
        mock_connector.get_config.return_value = config_db_as_dict
        return mock_connector

class TestPatchApplier(unittest.TestCase):
    def test_apply__invalid_sonic_yang__failure(self):
        # Arrange
        patchapplier = self.__create_patch_applier(valid_sonic_yang=False)

        # Act and assert
        self.assertRaises(Exception, patchapplier.apply, MULTI_OPERATION_SONIC_YANG_PATCH)

    def test_apply__json_not_fully_updated__failure(self):
        # Arrange
        patchapplier = self.__create_patch_applier(verified_same_config=False)

        # Act and assert
        self.assertRaises(Exception, patchapplier.apply, MULTI_OPERATION_SONIC_YANG_PATCH)

    def test_apply__no_errors__update_successful(self):
        # Arrange
        changes = [Mock(), Mock()]
        patchapplier = self.__create_patch_applier(changes)

        # Act
        patchapplier.apply(MULTI_OPERATION_SONIC_YANG_PATCH)

        # Assert
        patchapplier.configwrapper.get_sonic_yang_as_json.assert_has_calls([call(), call()])
        patchapplier.patchwrapper.simulate_patch.assert_has_calls( \
            [call(MULTI_OPERATION_SONIC_YANG_PATCH, SONIC_YANG_AS_JSON)])
        patchapplier.configwrapper.validate_sonic_yang_config.assert_has_calls([call(SONIC_YANG_AFTER_MULTI_PATCH)])
        patchapplier.patchorderer.order.assert_has_calls([call(MULTI_OPERATION_SONIC_YANG_PATCH)])
        patchapplier.changeapplier.apply.assert_has_calls([call(changes[0]), call(changes[1])])
        patchapplier.patchwrapper.verify_same_json.assert_has_calls( \
            [call(SONIC_YANG_AFTER_MULTI_PATCH, SONIC_YANG_AFTER_MULTI_PATCH)])

    def __create_patch_applier(self, changes=None, valid_sonic_yang=True, verified_same_config=True):
        configwrapper = Mock()
        configwrapper.get_sonic_yang_as_json.side_effect = [SONIC_YANG_AS_JSON, SONIC_YANG_AFTER_MULTI_PATCH]
        configwrapper.validate_sonic_yang_config.side_effect = \
            create_side_effect_dict({(str(SONIC_YANG_AFTER_MULTI_PATCH),): valid_sonic_yang})

        patchwrapper = Mock()
        patchwrapper.simulate_patch.side_effect = \
            create_side_effect_dict( \
                {(str(MULTI_OPERATION_SONIC_YANG_PATCH), str(SONIC_YANG_AS_JSON)): SONIC_YANG_AFTER_MULTI_PATCH})
        patchwrapper.verify_same_json.side_effect = \
            create_side_effect_dict( \
                {(str(SONIC_YANG_AFTER_MULTI_PATCH), str(SONIC_YANG_AFTER_MULTI_PATCH)): verified_same_config})

        changes = [Mock(), Mock()] if not changes else changes
        patchorderer = Mock()
        patchorderer.order.side_effect = create_side_effect_dict({(str(MULTI_OPERATION_SONIC_YANG_PATCH),): changes})

        changeapplier = Mock()
        changeapplier.apply.side_effect = create_side_effect_dict({(str(changes[0]),): 0, (str(changes[1]),): 0})

        return generic_update.PatchApplier(patchorderer, changeapplier, configwrapper, patchwrapper)

class TestConfigReplacer(unittest.TestCase):
    def test_replace__invalid_sonic_yang__failure(self):
        # Arrange
        configreplacer = self.__create_config_replacer(valid_sonic_yang=False)

        # Act and assert
        self.assertRaises(Exception, configreplacer.replace, SONIC_YANG_AFTER_MULTI_PATCH)

    def test_replace__json_not_fully_updated__failure(self):
        # Arrange
        configreplacer = self.__create_config_replacer(verified_same_config=False)

        # Act and assert
        self.assertRaises(Exception, configreplacer.replace, SONIC_YANG_AFTER_MULTI_PATCH)

    def test_replace__no_errors__update_successful(self):
        # Arrange
        configreplacer = self.__create_config_replacer()

        # Act
        configreplacer.replace(SONIC_YANG_AFTER_MULTI_PATCH)

        # Assert
        configreplacer.configwrapper.validate_sonic_yang_config.assert_has_calls([call(SONIC_YANG_AFTER_MULTI_PATCH)])
        configreplacer.configwrapper.get_sonic_yang_as_json.assert_has_calls([call(), call()])
        configreplacer.patchwrapper.generate_patch.assert_has_calls( \
            [call(SONIC_YANG_AS_JSON, SONIC_YANG_AFTER_MULTI_PATCH)])
        configreplacer.patchapplier.apply.assert_has_calls([call(MULTI_OPERATION_SONIC_YANG_PATCH)])
        configreplacer.patchwrapper.verify_same_json.assert_has_calls( \
            [call(SONIC_YANG_AFTER_MULTI_PATCH, SONIC_YANG_AFTER_MULTI_PATCH)])

    def __create_config_replacer(self, changes=None, valid_sonic_yang=True, verified_same_config=True):
        configwrapper = Mock()
        configwrapper.validate_sonic_yang_config.side_effect = \
            create_side_effect_dict({(str(SONIC_YANG_AFTER_MULTI_PATCH),): valid_sonic_yang})
        configwrapper.get_sonic_yang_as_json.side_effect = [SONIC_YANG_AS_JSON, SONIC_YANG_AFTER_MULTI_PATCH]

        patchwrapper = Mock()
        patchwrapper.generate_patch.side_effect = \
            create_side_effect_dict( \
                {(str(SONIC_YANG_AS_JSON), str(SONIC_YANG_AFTER_MULTI_PATCH)): MULTI_OPERATION_SONIC_YANG_PATCH})
        patchwrapper.verify_same_json.side_effect = \
            create_side_effect_dict( \
                {(str(SONIC_YANG_AFTER_MULTI_PATCH), str(SONIC_YANG_AFTER_MULTI_PATCH)): verified_same_config})

        changes = [Mock(), Mock()] if not changes else changes
        patchorderer = Mock()
        patchorderer.order.side_effect = create_side_effect_dict({(str(MULTI_OPERATION_SONIC_YANG_PATCH),): changes})

        patchapplier = Mock()
        patchapplier.apply.side_effect = create_side_effect_dict({(str(MULTI_OPERATION_SONIC_YANG_PATCH),): 0})

        return generic_update.ConfigReplacer(patchapplier, configwrapper, patchwrapper)

class TestFileSystemConfigRollbacker(unittest.TestCase):
    def setUp(self):
        self.checkpoints_dir = os.path.join(os.getcwd(),"checkpoints")
        self.checkpoint_ext = ".cp.json"
        self.any_checkpoint_name = "anycheckpoint"
        self.any_other_checkpoint_name = "anyothercheckpoint"
        self.any_config = {}
        self.clean_up()

    def tearDown(self):
        self.clean_up()

    def test_rollback__checkpoint_does_not_exist__failure(self):
        # Arrange
        rollbacker = self.create_rollbacker()

        # Act and assert
        self.assertRaises(Exception, rollbacker.rollback, "NonExistingCheckpoint")

    def test_rollback__no_errors__success(self):
        # Arrange
        self.create_checkpoints_dir()
        self.add_checkpoint(self.any_checkpoint_name, self.any_config)
        rollbacker = self.create_rollbacker()

        # Act
        rollbacker.rollback(self.any_checkpoint_name)

        # Assert
        rollbacker.config_replacer.replace.assert_has_calls([call(self.any_config)])

    def test_checkpoint__checkpoints_dir_does_not_exist__checkpoint_created(self):
        # Arrange
        rollbacker = self.create_rollbacker()
        self.assertFalse(os.path.isdir(self.checkpoints_dir))

        # Act
        rollbacker.checkpoint(self.any_checkpoint_name)

        # Assert
        self.assertTrue(os.path.isdir(self.checkpoints_dir))
        self.assertEqual(self.any_config, self.get_checkpoint(self.any_checkpoint_name))

    def test_checkpoint__checkpoints_dir_exists__checkpoint_created(self):
        # Arrange
        self.create_checkpoints_dir()
        rollbacker = self.create_rollbacker()

        # Act
        rollbacker.checkpoint(self.any_checkpoint_name)

        # Assert
        self.assertEqual(self.any_config, self.get_checkpoint(self.any_checkpoint_name))

    def test_list_checkpoints__checkpoints_dir_does_not_exist__empty_list(self):
        # Arrange
        rollbacker = self.create_rollbacker()
        self.assertFalse(os.path.isdir(self.checkpoints_dir))
        expected = []

        # Act
        actual = rollbacker.list_checkpoints()

        # Assert
        self.assertListEqual(expected, actual)


    def test_list_checkpoints__checkpoints_dir_exist_but_no_files__empty_list(self):
        # Arrange
        self.create_checkpoints_dir()
        rollbacker = self.create_rollbacker()
        expected = []

        # Act
        actual = rollbacker.list_checkpoints()

        # Assert
        self.assertListEqual(expected, actual)

    def test_list_checkpoints__checkpoints_dir_has_multiple_files__multiple_files(self):
        # Arrange
        self.create_checkpoints_dir()
        self.add_checkpoint(self.any_checkpoint_name, self.any_config)
        self.add_checkpoint(self.any_other_checkpoint_name, self.any_config)
        rollbacker = self.create_rollbacker()
        expected = [self.any_checkpoint_name, self.any_other_checkpoint_name]

        # Act
        actual = rollbacker.list_checkpoints()

        # Assert
        self.assertListEqual(expected, actual)

    def test_list_checkpoints__checkpoints_names_have_special_characters__multiple_files(self):
        # Arrange
        self.create_checkpoints_dir()
        self.add_checkpoint("check.point1", self.any_config)
        self.add_checkpoint(".checkpoint2", self.any_config)
        self.add_checkpoint("checkpoint3.", self.any_config)
        rollbacker = self.create_rollbacker()
        expected = ["check.point1", ".checkpoint2", "checkpoint3."]

        # Act
        actual = rollbacker.list_checkpoints()

        # Assert
        self.assertListEqual(expected, actual)

    def test_delete_checkpoint__checkpoint_does_not_exist__failure(self):
        # Arrange
        rollbacker = self.create_rollbacker()

        # Act and assert
        self.assertRaises(Exception, rollbacker.delete_checkpoint, self.any_checkpoint_name)

    def test_delete_checkpoint__checkpoint_exist__success(self):
        # Arrange
        self.create_checkpoints_dir()
        self.add_checkpoint(self.any_checkpoint_name, self.any_config)
        rollbacker = self.create_rollbacker()

        # Act
        rollbacker.delete_checkpoint(self.any_checkpoint_name)

        # Assert
        self.assertFalse(self.check_checkpoint_exists(self.any_checkpoint_name))

    def test_multiple_operations(self):
        rollbacker = self.create_rollbacker()

        self.assertListEqual([], rollbacker.list_checkpoints())

        rollbacker.checkpoint(self.any_checkpoint_name)
        self.assertListEqual([self.any_checkpoint_name], rollbacker.list_checkpoints())
        self.assertEqual(self.any_config, self.get_checkpoint(self.any_checkpoint_name))

        rollbacker.rollback(self.any_checkpoint_name)
        rollbacker.config_replacer.replace.assert_has_calls([call(self.any_config)])

        rollbacker.checkpoint(self.any_other_checkpoint_name)
        self.assertListEqual([self.any_checkpoint_name, self.any_other_checkpoint_name], rollbacker.list_checkpoints())
        self.assertEqual(self.any_config, self.get_checkpoint(self.any_other_checkpoint_name))

        rollbacker.delete_checkpoint(self.any_checkpoint_name)
        self.assertListEqual([self.any_other_checkpoint_name], rollbacker.list_checkpoints())

        rollbacker.delete_checkpoint(self.any_other_checkpoint_name)
        self.assertListEqual([], rollbacker.list_checkpoints())

    def clean_up(self):
        if os.path.isdir(self.checkpoints_dir):
            shutil.rmtree(self.checkpoints_dir)

    def create_checkpoints_dir(self):
        os.makedirs(self.checkpoints_dir)

    def add_checkpoint(self, name, json_content):
        path=os.path.join(self.checkpoints_dir, f"{name}{self.checkpoint_ext}")
        with open(path, "w") as fh:
            fh.write(json.dumps(json_content))

    def get_checkpoint(self, name):
        path=os.path.join(self.checkpoints_dir, f"{name}{self.checkpoint_ext}")
        with open(path) as fh:
            text = fh.read()
            return json.loads(text)

    def check_checkpoint_exists(self, name):
        path=os.path.join(self.checkpoints_dir, f"{name}{self.checkpoint_ext}")
        return os.path.isfile(path)

    def create_rollbacker(self):
        replacer = Mock()
        replacer.replace.side_effect = create_side_effect_dict({(str(self.any_config),): 0})

        configwrapper = Mock()
        configwrapper.get_sonic_yang_as_json.return_value = self.any_config

        return generic_update.FileSystemConfigRollbacker( \
            checkpoints_dir=self.checkpoints_dir, \
                config_replacer=replacer, \
                    configwrapper=configwrapper)

class TestGenericUpdateFactory(unittest.TestCase):
    def setUp(self):
        self.any_verbose=True
        self.any_dry_run=True

    def test_create_patch_applier__invalid_config_format__failure(self):
        # Arrange
        factory = generic_update.GenericUpdateFactory()

        # Act and assert
        self.assertRaises( \
            ValueError, factory.create_patch_applier, "INVALID_FORMAT", self.any_verbose, self.any_dry_run)

    def test_create_patch_applier__different_options(self):
        # Arrange
        options = [
            {"verbose": {True: None, False: None}},
            {"dry_run": {True: None, False: generic_update.ConfigLockDecorator}},
            {
                "config_format": {
                    generic_update.ConfigFormat.SONICYANG: None,
                    generic_update.ConfigFormat.CONFIGDB: generic_update.ConfigDbDecorator
                }
            },
        ]

        # Act and assert
        self.recursively_test_create_func(options, 0, {}, [], self.validate_create_patch_applier)

    def test_create_config_replacer__invalid_config_format__failure(self):
        # Arrange
        factory = generic_update.GenericUpdateFactory()

        # Act and assert
        self.assertRaises( \
            ValueError, factory.create_config_replacer, "INVALID_FORMAT", self.any_verbose, self.any_dry_run)

    def test_create_config_replacer__different_options(self):
        # Arrange
        options = [
            {"verbose": {True: None, False: None}},
            {"dry_run": {True: None, False: generic_update.ConfigLockDecorator}},
            {
                "config_format": {
                    generic_update.ConfigFormat.SONICYANG: None,
                    generic_update.ConfigFormat.CONFIGDB: generic_update.ConfigDbDecorator
                }
            },
        ]

        # Act and assert
        self.recursively_test_create_func(options, 0, {}, [], self.validate_create_config_replacer)

    def test_create_config_rollbacker__different_options(self):
        # Arrange
        options = [
            {"verbose": {True: None, False: None}},
            {"dry_run": {True: None, False: generic_update.ConfigLockDecorator}}
        ]

        # Act and assert
        self.recursively_test_create_func(options, 0, {}, [], self.validate_create_config_rollbacker)

    def recursively_test_create_func(self, options, cur_option, params, expected_decorators, create_func):
        if cur_option == len(options):
            create_func(params, expected_decorators)
            return

        param = list(options[cur_option].keys())[0]
        for key in options[cur_option][param]:
            params[param] = key
            decorator = options[cur_option][param][key]
            if decorator != None:
                expected_decorators.append(decorator)
            self.recursively_test_create_func(options, cur_option+1, params, expected_decorators, create_func)
            if decorator != None:
                expected_decorators.pop()

    def validate_create_patch_applier(self, params, expected_decorators):
        factory = generic_update.GenericUpdateFactory()
        patch_applier = factory.create_patch_applier(params["config_format"], params["verbose"], params["dry_run"])
        for decorator_type in expected_decorators:
            self.assertIsInstance(patch_applier, decorator_type)

            patch_applier = patch_applier.decorated_patch_applier

        self.assertIsInstance(patch_applier, generic_update.PatchApplier)
        if params["dry_run"]:
            self.assertIsInstance(patch_applier.configwrapper, generic_update.DryRunConfigWrapper)
        else:
            self.assertIsInstance(patch_applier.configwrapper, generic_update.ConfigWrapper)

    def validate_create_config_replacer(self, params, expected_decorators):
        factory = generic_update.GenericUpdateFactory()
        config_replacer = factory.create_config_replacer(params["config_format"], params["verbose"], params["dry_run"])
        for decorator_type in expected_decorators:
            self.assertIsInstance(config_replacer, decorator_type)

            config_replacer = config_replacer.decorated_config_replacer

        self.assertIsInstance(config_replacer, generic_update.ConfigReplacer)
        if params["dry_run"]:
            self.assertIsInstance(config_replacer.configwrapper, generic_update.DryRunConfigWrapper)
            self.assertIsInstance(config_replacer.patchapplier.configwrapper, generic_update.DryRunConfigWrapper)
        else:
            self.assertIsInstance(config_replacer.configwrapper, generic_update.ConfigWrapper)
            self.assertIsInstance(config_replacer.patchapplier.configwrapper, generic_update.ConfigWrapper)

    def validate_create_config_rollbacker(self, params, expected_decorators):
        factory = generic_update.GenericUpdateFactory()
        config_rollbacker = factory.create_config_rollbacker(params["verbose"], params["dry_run"])
        for decorator_type in expected_decorators:
            self.assertIsInstance(config_rollbacker, decorator_type)

            config_rollbacker = config_rollbacker.decorated_config_rollbacker

        self.assertIsInstance(config_rollbacker, generic_update.FileSystemConfigRollbacker)
        if params["dry_run"]:
            self.assertIsInstance(config_rollbacker.configwrapper, generic_update.DryRunConfigWrapper)
            self.assertIsInstance(config_rollbacker.config_replacer.configwrapper, generic_update.DryRunConfigWrapper)
            self.assertIsInstance( \
                config_rollbacker.config_replacer.patchapplier.configwrapper, generic_update.DryRunConfigWrapper)
        else:
            self.assertIsInstance(config_rollbacker.configwrapper, generic_update.ConfigWrapper)
            self.assertIsInstance(config_rollbacker.config_replacer.configwrapper, generic_update.ConfigWrapper)
            self.assertIsInstance( \
                config_rollbacker.config_replacer.patchapplier.configwrapper, generic_update.ConfigWrapper)

class TestGenericUpdater(unittest.TestCase):
    def setUp(self):
        self.any_checkpoint_name = "anycheckpoint"
        self.any_other_checkpoint_name = "anyothercheckpoint"
        self.any_checkpoints_list = [self.any_checkpoint_name, self.any_other_checkpoint_name]
        self.any_config_format = generic_update.ConfigFormat.SONICYANG
        self.any_verbose = True
        self.any_dry_run = True

    def test_apply_patch__creates_applier_and_apply(self):
        # Arrange
        patch_applier = Mock()
        patch_applier.apply.side_effect = create_side_effect_dict({(str(SINGLE_OPERATION_SONIC_YANG_PATCH),): 0})

        factory = Mock()
        factory.create_patch_applier.side_effect = \
            create_side_effect_dict( \
                {(str(self.any_config_format), str(self.any_verbose), str(self.any_dry_run),): patch_applier})

        generic_updater = generic_update.GenericUpdater(factory)

        # Act
        generic_updater.apply_patch( \
            SINGLE_OPERATION_SONIC_YANG_PATCH, self.any_config_format, self.any_verbose, self.any_dry_run)

        # Assert
        patch_applier.apply.assert_has_calls([call(SINGLE_OPERATION_SONIC_YANG_PATCH)])

    def test_replace__creates_replacer_and_replace(self):
        # Arrange
        config_replacer = Mock()
        config_replacer.replace.side_effect = create_side_effect_dict({(str(SONIC_YANG_AS_JSON),): 0})

        factory = Mock()
        factory.create_config_replacer.side_effect = \
            create_side_effect_dict( \
                {(str(self.any_config_format), str(self.any_verbose), str(self.any_dry_run),): config_replacer})

        generic_updater = generic_update.GenericUpdater(factory)

        # Act
        generic_updater.replace(SONIC_YANG_AS_JSON, self.any_config_format, self.any_verbose, self.any_dry_run)

        # Assert
        config_replacer.replace.assert_has_calls([call(SONIC_YANG_AS_JSON)])

    def test_rollback__creates_rollbacker_and_rollback(self):
        # Arrange
        config_rollbacker = Mock()
        config_rollbacker.rollback.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})

        factory = Mock()
        factory.create_config_rollbacker.side_effect = \
            create_side_effect_dict({(str(self.any_verbose), str(self.any_dry_run),): config_rollbacker})

        generic_updater = generic_update.GenericUpdater(factory)

        # Act
        generic_updater.rollback(self.any_checkpoint_name, self.any_verbose, self.any_dry_run)

        # Assert
        config_rollbacker.rollback.assert_has_calls([call(self.any_checkpoint_name)])

    def test_checkpoint__creates_rollbacker_and_checkpoint(self):
        # Arrange
        config_rollbacker = Mock()
        config_rollbacker.checkpoint.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})

        factory = Mock()
        factory.create_config_rollbacker.side_effect = \
            create_side_effect_dict({(str(self.any_verbose), str(self.any_dry_run),): config_rollbacker})

        generic_updater = generic_update.GenericUpdater(factory)

        # Act
        generic_updater.checkpoint(self.any_checkpoint_name, self.any_verbose, self.any_dry_run)

        # Assert
        config_rollbacker.checkpoint.assert_has_calls([call(self.any_checkpoint_name)])

    def test_delete_checkpoint__creates_rollbacker_and_deletes_checkpoint(self):
        # Arrange
        config_rollbacker = Mock()
        config_rollbacker.delete_checkpoint.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})

        factory = Mock()
        factory.create_config_rollbacker.side_effect = \
            create_side_effect_dict({(str(self.any_verbose), str(self.any_dry_run),): config_rollbacker})

        generic_updater = generic_update.GenericUpdater(factory)

        # Act
        generic_updater.delete_checkpoint(self.any_checkpoint_name, self.any_verbose, self.any_dry_run)

        # Assert
        config_rollbacker.delete_checkpoint.assert_has_calls([call(self.any_checkpoint_name)])

    def test_list_checkpoints__creates_rollbacker_and_list_checkpoints(self):
        # Arrange
        config_rollbacker = Mock()
        config_rollbacker.list_checkpoints.return_value = self.any_checkpoints_list

        factory = Mock()
        factory.create_config_rollbacker.side_effect = \
            create_side_effect_dict({(str(self.any_verbose), str(self.any_dry_run),): config_rollbacker})

        generic_updater = generic_update.GenericUpdater(factory)

        expected = self.any_checkpoints_list

        # Act
        actual = generic_updater.list_checkpoints(self.any_verbose, self.any_dry_run)

        # Assert
        self.assertListEqual(expected, actual)

class TestConfigDbDecorator(unittest.TestCase):
    def test_apply__converts_to_yang_and_calls_decorated_class(self):
        # Arrange
        config_db_decorator = self.__create_config_db_decorator()

        # Act
        config_db_decorator.apply(CONFIG_DB_AS_JSON)

        # Assert
        config_db_decorator.patchwrapper.convert_config_db_patch_to_sonic_yang_patch.assert_has_calls( \
            [call(CONFIG_DB_AS_JSON)])
        config_db_decorator.decorated_patch_applier.apply.assert_has_calls([call(SONIC_YANG_AS_JSON)])

    def test_replace__converts_to_yang_and_calls_decorated_class(self):
        # Arrange
        config_db_decorator = self.__create_config_db_decorator()

        # Act
        config_db_decorator.replace(CONFIG_DB_AS_JSON)

        # Assert
        config_db_decorator.configwrapper.convert_config_db_to_sonic_yang.assert_has_calls([call(CONFIG_DB_AS_JSON)])
        config_db_decorator.decorated_config_replacer.replace.assert_has_calls([call(SONIC_YANG_AS_JSON)])

    def __create_config_db_decorator(self):
        patchapplier = Mock()
        patchapplier.apply.side_effect = create_side_effect_dict({(str(SONIC_YANG_AS_JSON),): 0})

        patchwrapper = Mock()
        patchwrapper.convert_config_db_patch_to_sonic_yang_patch.side_effect = \
            create_side_effect_dict({(str(CONFIG_DB_AS_JSON),): SONIC_YANG_AS_JSON})

        config_replacer = Mock()
        config_replacer.replace.side_effect = create_side_effect_dict({(str(SONIC_YANG_AS_JSON),): 0})

        configwrapper = Mock()
        configwrapper.convert_config_db_to_sonic_yang.side_effect = \
            create_side_effect_dict({(str(CONFIG_DB_AS_JSON),): SONIC_YANG_AS_JSON})

        return generic_update.ConfigDbDecorator( \
            decorated_patch_applier=patchapplier, \
                decorated_config_replacer=config_replacer, \
                    patchwrapper=patchwrapper, \
                        configwrapper=configwrapper)

class TestConfigLockDecorator(unittest.TestCase):
    def setUp(self):
        self.any_checkpoint_name = "anycheckpoint"

    def test_apply__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.apply(SINGLE_OPERATION_SONIC_YANG_PATCH)

        # Assert
        config_lock_decorator.configlock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_patch_applier.apply.assert_has_calls([call(SINGLE_OPERATION_SONIC_YANG_PATCH)])
        config_lock_decorator.configlock.release_lock.assert_called_once()

    def test_replace__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.replace(SONIC_YANG_AS_JSON)

        # Assert
        config_lock_decorator.configlock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_config_replacer.replace.assert_has_calls([call(SONIC_YANG_AS_JSON)])
        config_lock_decorator.configlock.release_lock.assert_called_once()

    def test_rollback__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.rollback(self.any_checkpoint_name)

        # Assert
        config_lock_decorator.configlock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_config_rollbacker.rollback.assert_has_calls([call(self.any_checkpoint_name)])
        config_lock_decorator.configlock.release_lock.assert_called_once()

    def test_checkpoint__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.checkpoint(self.any_checkpoint_name)

        # Assert
        config_lock_decorator.configlock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_config_rollbacker.checkpoint.assert_has_calls([call(self.any_checkpoint_name)])
        config_lock_decorator.configlock.release_lock.assert_called_once()

    def __create_config_lock_decorator(self):
        configlock = Mock()

        patchapplier = Mock()
        patchapplier.apply.side_effect = create_side_effect_dict({(str(SINGLE_OPERATION_SONIC_YANG_PATCH),): 0})

        config_replacer = Mock()
        config_replacer.replace.side_effect = create_side_effect_dict({(str(SONIC_YANG_AS_JSON),): 0})

        config_rollbacker = Mock()
        config_rollbacker.rollback.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})
        config_rollbacker.checkpoint.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})

        return generic_update.ConfigLockDecorator( \
            configlock=configlock, \
                decorated_patch_applier=patchapplier, \
                    decorated_config_replacer=config_replacer, \
                        decorated_config_rollbacker=config_rollbacker)

#### resources ####
CONFIG_DB_AS_DICT = {
    "VLAN_MEMBER": {
        ("Vlan1000", "Ethernet0"): {
            "tagging_mode": "untagged"
        },
        ("Vlan1000", "Ethernet4"): {
            "tagging_mode": "untagged"
        },
        ("Vlan1000", "Ethernet8"): {
            "tagging_mode": "untagged"
        }
    },
    "VLAN": {
        "Vlan1000": {
            "vlanid": "1000",
            "dhcp_servers": [
                "192.0.0.1",
                "192.0.0.2",
                "192.0.0.3",
                "192.0.0.4"
            ]
        }
    },
    "ACL_TABLE": {
        "NO-NSW-PACL-V4": {
            "type": "L3",
            "policy_desc": "NO-NSW-PACL-V4",
            "ports": [
                "Ethernet0"
            ]
        },
        "DATAACL": {
            "policy_desc": "DATAACL",
            "ports": [
                "Ethernet4"
            ],
            "stage": "ingress",
            "type": "L3"
        },
        "EVERFLOW": {
            "policy_desc": "EVERFLOW",
            "ports": [
                "Ethernet8"
            ],
            "stage": "ingress",
            "type": "MIRROR"
        },
        "EVERFLOWV6": {
            "policy_desc": "EVERFLOWV6",
            "ports": [
                "Ethernet4",
                "Ethernet8"
            ],
            "stage": "ingress",
            "type": "MIRRORV6"
        },
        "NO-NSW-PACL-V4": {
            "type": "L3",
            "policy_desc": "NO-NSW-PACL-V4",
            "ports": [
                "Ethernet0"
            ]
        }
    },
    "VLAN": {
        "Vlan1000": {
            "vlanid": "1000",
            "dhcp_servers": [
                "192.0.0.1",
                "192.0.0.2",
                "192.0.0.3",
                "192.0.0.4"
            ]
        }
    },
    "PORT": {
        "Ethernet0": {
            "alias": "Eth1",
            "lanes": "65, 66, 67, 68",
            "description": "Ethernet0 100G link",
            "speed": "100000"
        },
        "Ethernet4": {
            "admin_status": "up",
            "alias": "fortyGigE0/4",
            "description": "Servers0:eth0",
            "index": "1",
            "lanes": "29,30,31,32",
            "mtu": "9100",
            "pfc_asym": "off",
            "speed": "40000"
        },
        "Ethernet8": {
            "admin_status": "up",
            "alias": "fortyGigE0/8",
            "description": "Servers1:eth0",
            "index": "2",
            "lanes": "33,34,35,36",
            "mtu": "9100",
            "pfc_asym": "off",
            "speed": "40000"
        }
    },
    "WRED_PROFILE": {
        "AZURE_LOSSLESS": {
            "wred_green_enable": "true",
            "wred_yellow_enable": "true",
            "wred_red_enable": "true",
            "ecn": "ecn_all",
            "green_max_threshold": "2097152",
            "green_min_threshold": "1048576",
            "yellow_max_threshold": "2097152",
            "yellow_min_threshold": "1048576",
            "red_max_threshold": "2097152",
            "red_min_threshold": "1048576",
            "green_drop_probability": "5",
            "yellow_drop_probability": "5",
            "red_drop_probability": "5"
        }
    }
}

CONFIG_DB_AS_JSON = {
    "VLAN_MEMBER": {
        "Vlan1000|Ethernet0": {
            "tagging_mode": "untagged"
        },
        "Vlan1000|Ethernet4": {
            "tagging_mode": "untagged"
        },
        "Vlan1000|Ethernet8": {
            "tagging_mode": "untagged"
        }
    },
    "VLAN": {
        "Vlan1000": {
            "vlanid": "1000",
            "dhcp_servers": [
                "192.0.0.1",
                "192.0.0.2",
                "192.0.0.3",
                "192.0.0.4"
            ]
        }
    },
    "ACL_TABLE": {
        "NO-NSW-PACL-V4": {
            "type": "L3",
            "policy_desc": "NO-NSW-PACL-V4",
            "ports": [
                "Ethernet0"
            ]
        },
        "DATAACL": {
            "policy_desc": "DATAACL",
            "ports": [
                "Ethernet4"
            ],
            "stage": "ingress",
            "type": "L3"
        },
        "EVERFLOW": {
            "policy_desc": "EVERFLOW",
            "ports": [
                "Ethernet8"
            ],
            "stage": "ingress",
            "type": "MIRROR"
        },
        "EVERFLOWV6": {
            "policy_desc": "EVERFLOWV6",
            "ports": [
                "Ethernet4",
                "Ethernet8"
            ],
            "stage": "ingress",
            "type": "MIRRORV6"
        }
    },
    "PORT": {
        "Ethernet0": {
            "alias": "Eth1",
            "lanes": "65, 66, 67, 68",
            "description": "Ethernet0 100G link",
            "speed": "100000"
        },
        "Ethernet4": {
            "admin_status": "up",
            "alias": "fortyGigE0/4",
            "description": "Servers0:eth0",
            "index": "1",
            "lanes": "29,30,31,32",
            "mtu": "9100",
            "pfc_asym": "off",
            "speed": "40000"
        },
        "Ethernet8": {
            "admin_status": "up",
            "alias": "fortyGigE0/8",
            "description": "Servers1:eth0",
            "index": "2",
            "lanes": "33,34,35,36",
            "mtu": "9100",
            "pfc_asym": "off",
            "speed": "40000"
        }
    },
    "WRED_PROFILE": {
        "AZURE_LOSSLESS": {
            "wred_green_enable": "true",
            "wred_yellow_enable": "true",
            "wred_red_enable": "true",
            "ecn": "ecn_all",
            "green_max_threshold": "2097152",
            "green_min_threshold": "1048576",
            "yellow_max_threshold": "2097152",
            "yellow_min_threshold": "1048576",
            "red_max_threshold": "2097152",
            "red_min_threshold": "1048576",
            "green_drop_probability": "5",
            "yellow_drop_probability": "5",
            "red_drop_probability": "5"
        }
    }
}

CROPPED_CONFIG_DB_AS_JSON = {
    "VLAN_MEMBER": {
        "Vlan1000|Ethernet0": {
            "tagging_mode": "untagged"
        },
        "Vlan1000|Ethernet4": {
            "tagging_mode": "untagged"
        },
        "Vlan1000|Ethernet8": {
            "tagging_mode": "untagged"
        }
    },
    "VLAN": {
        "Vlan1000": {
            "vlanid": "1000",
            "dhcp_servers": [
                "192.0.0.1",
                "192.0.0.2",
                "192.0.0.3",
                "192.0.0.4"
            ]
        }
    },
    "ACL_TABLE": {
        "NO-NSW-PACL-V4": {
            "type": "L3",
            "policy_desc": "NO-NSW-PACL-V4",
            "ports": [
                "Ethernet0"
            ]
        },
        "DATAACL": {
            "policy_desc": "DATAACL",
            "ports": [
                "Ethernet4"
            ],
            "stage": "ingress",
            "type": "L3"
        },
        "EVERFLOW": {
            "policy_desc": "EVERFLOW",
            "ports": [
                "Ethernet8"
            ],
            "stage": "ingress",
            "type": "MIRROR"
        },
        "EVERFLOWV6": {
            "policy_desc": "EVERFLOWV6",
            "ports": [
                "Ethernet4",
                "Ethernet8"
            ],
            "stage": "ingress",
            "type": "MIRRORV6"
        }
    },
    "PORT": {
        "Ethernet0": {
            "alias": "Eth1",
            "lanes": "65, 66, 67, 68",
            "description": "Ethernet0 100G link",
            "speed": "100000"
        },
        "Ethernet4": {
            "admin_status": "up",
            "alias": "fortyGigE0/4",
            "description": "Servers0:eth0",
            "index": "1",
            "lanes": "29,30,31,32",
            "mtu": "9100",
            "pfc_asym": "off",
            "speed": "40000"
        },
        "Ethernet8": {
            "admin_status": "up",
            "alias": "fortyGigE0/8",
            "description": "Servers1:eth0",
            "index": "2",
            "lanes": "33,34,35,36",
            "mtu": "9100",
            "pfc_asym": "off",
            "speed": "40000"
        }
    }
}

SONIC_YANG_AS_JSON = {
    "sonic-vlan:sonic-vlan": {
        "sonic-vlan:VLAN_MEMBER": {
            "VLAN_MEMBER_LIST": [
                {
                    "vlan_name": "Vlan1000",
                    "port": "Ethernet0",
                    "tagging_mode": "untagged"
                },
                {
                    "vlan_name": "Vlan1000",
                    "port": "Ethernet4",
                    "tagging_mode": "untagged"
                },
                {
                    "vlan_name": "Vlan1000",
                    "port": "Ethernet8",
                    "tagging_mode": "untagged"
                }
            ]
        },
        "sonic-vlan:VLAN": {
            "VLAN_LIST": [
                {
                    "vlan_name": "Vlan1000",
                    "vlanid": 1000,
                    "dhcp_servers": [
                        "192.0.0.1",
                        "192.0.0.2",
                        "192.0.0.3",
                        "192.0.0.4"
                    ]
                }
            ]
        }
    },
    "sonic-acl:sonic-acl": {
        "sonic-acl:ACL_TABLE": {
            "ACL_TABLE_LIST": [
                {
                    "ACL_TABLE_NAME": "NO-NSW-PACL-V4",
                    "type": "L3",
                    "policy_desc": "NO-NSW-PACL-V4",
                    "ports": [
                        "Ethernet0"
                    ]
                },
                {
                    "ACL_TABLE_NAME": "DATAACL",
                    "policy_desc": "DATAACL",
                    "ports": [
                        "Ethernet4"
                    ],
                    "stage": "ingress",
                    "type": "L3"
                },
                {
                    "ACL_TABLE_NAME": "EVERFLOW",
                    "policy_desc": "EVERFLOW",
                    "ports": [
                        "Ethernet8"
                    ],
                    "stage": "ingress",
                    "type": "MIRROR"
                },
                {
                    "ACL_TABLE_NAME": "EVERFLOWV6",
                    "policy_desc": "EVERFLOWV6",
                    "ports": [
                        "Ethernet4",
                        "Ethernet8"
                    ],
                    "stage": "ingress",
                    "type": "MIRRORV6"
                }
            ]
        }
    },
    "sonic-port:sonic-port": {
        "sonic-port:PORT": {
            "PORT_LIST": [
                {
                    "port_name": "Ethernet0",
                    "alias": "Eth1",
                    "lanes": "65, 66, 67, 68",
                    "description": "Ethernet0 100G link",
                    "speed": 100000
                },
                {
                    "port_name": "Ethernet4",
                    "admin_status": "up",
                    "alias": "fortyGigE0/4",
                    "description": "Servers0:eth0",
                    "index": 1,
                    "lanes": "29,30,31,32",
                    "mtu": 9100,
                    "pfc_asym": "off",
                    "speed": 40000
                },
                {
                    "port_name": "Ethernet8",
                    "admin_status": "up",
                    "alias": "fortyGigE0/8",
                    "description": "Servers1:eth0",
                    "index": 2,
                    "lanes": "33,34,35,36",
                    "mtu": 9100,
                    "pfc_asym": "off",
                    "speed": 40000
                }
            ]
        }
    }
}

SONIC_YANG_AS_JSON_INVALID = {
    "sonic-vlan:sonic-vlan": {
        "sonic-vlan:VLAN_MEMBER": {
            "VLAN_MEMBER_LIST": [
                {
                    "vlan_name": "Vlan1000",
                    "port": "Ethernet4",
                    "tagging_mode": "untagged"
                }
            ]
        }
    }
}

SINGLE_OPERATION_CONFIG_DB_PATCH = jsonpatch.JsonPatch([
    {
        "op": "remove",
        "path": "/VLAN_MEMBER/Vlan1000|Ethernet8"
    }
])

SINGLE_OPERATION_SONIC_YANG_PATCH = jsonpatch.JsonPatch([
    {
        "op": "remove",
        "path": "/sonic-vlan:sonic-vlan/sonic-vlan:VLAN_MEMBER/VLAN_MEMBER_LIST/2"
    }
])

MULTI_OPERATION_CONFIG_DB_PATCH = jsonpatch.JsonPatch([
    {
        "op": "add",
        "path": "/PORT/Ethernet3",
        "value": {
            "alias": "Eth1/4",
            "lanes": "68",
            "description": "",
            "speed": "10000"
        }
    },
    {
        "op": "add",
        "path": "/PORT/Ethernet1",
        "value": {
            "alias": "Eth1/2",
            "lanes": "66",
            "description": "",
            "speed": "10000"
        }
    },
    {
        "op": "add",
        "path": "/PORT/Ethernet2",
        "value": {
            "alias": "Eth1/3",
            "lanes": "67",
            "description": "",
            "speed": "10000"
        }
    },
    {
        "op": "replace",
        "path": "/PORT/Ethernet0/lanes",
        "value": "65"
    },
    {
        "op": "replace",
        "path": "/PORT/Ethernet0/alias",
        "value": "Eth1/1"
    },
    {
        "op": "replace",
        "path": "/PORT/Ethernet0/description",
        "value": ""
    },
    {
        "op": "replace",
        "path": "/PORT/Ethernet0/speed",
        "value": "10000"
    },
    {
        "op": "add",
        "path": "/VLAN_MEMBER/Vlan100|Ethernet2",
        "value": {
            "tagging_mode": "untagged"
        }
    },
    {
        "op": "add",
        "path": "/VLAN_MEMBER/Vlan100|Ethernet3",
        "value": {
            "tagging_mode": "untagged"
        }
    },
    {
        "op": "add",
        "path": "/VLAN_MEMBER/Vlan100|Ethernet1",
        "value": {
            "tagging_mode": "untagged"
        }
    },
    {
        "op": "add",
        "path": "/ACL_TABLE/NO-NSW-PACL-V4/ports/1",
        "value": "Ethernet1"
    },
    {
        "op": "add",
        "path": "/ACL_TABLE/NO-NSW-PACL-V4/ports/2",
        "value": "Ethernet2"
    },
    {
        "op": "add",
        "path": "/ACL_TABLE/NO-NSW-PACL-V4/ports/3",
        "value": "Ethernet3"
    }
])

MULTI_OPERATION_SONIC_YANG_PATCH = jsonpatch.JsonPatch([
    {
        "op": "add",
        "path": "/sonic-vlan:sonic-vlan/sonic-vlan:VLAN_MEMBER/VLAN_MEMBER_LIST/3",
        "value": {
            "vlan_name": "Vlan100",
            "port": "Ethernet2",
            "tagging_mode": "untagged"
        }
    },
    {
        "op": "add",
        "path": "/sonic-vlan:sonic-vlan/sonic-vlan:VLAN_MEMBER/VLAN_MEMBER_LIST/4",
        "value": {
            "vlan_name": "Vlan100",
            "port": "Ethernet3",
            "tagging_mode": "untagged"
        }
    },
    {
        "op": "add",
        "path": "/sonic-vlan:sonic-vlan/sonic-vlan:VLAN_MEMBER/VLAN_MEMBER_LIST/5",
        "value": {
            "vlan_name": "Vlan100",
            "port": "Ethernet1",
            "tagging_mode": "untagged"
        }
    },
    {
        "op": "replace",
        "path": "/sonic-port:sonic-port/sonic-port:PORT/PORT_LIST/0/lanes",
        "value": "65"
    },
    {
        "op": "replace",
        "path": "/sonic-port:sonic-port/sonic-port:PORT/PORT_LIST/0/alias",
        "value": "Eth1/1"
    },
    {
        "op": "replace",
        "path": "/sonic-port:sonic-port/sonic-port:PORT/PORT_LIST/0/speed",
        "value": 10000
    },
    {
        "op": "replace",
        "path": "/sonic-port:sonic-port/sonic-port:PORT/PORT_LIST/0/description",
        "value": ""
    },
    {
        "op": "add",
        "path": "/sonic-port:sonic-port/sonic-port:PORT/PORT_LIST/3",
        "value": {
            "port_name": "Ethernet3",
            "alias": "Eth1/4",
            "lanes": "68",
            "description": "",
            "speed": 10000
        }
    },
    {
        "op": "add",
        "path": "/sonic-port:sonic-port/sonic-port:PORT/PORT_LIST/4",
        "value": {
            "port_name": "Ethernet1",
            "alias": "Eth1/2",
            "lanes": "66",
            "description": "",
            "speed": 10000
        }
    },
    {
        "op": "add",
        "path": "/sonic-port:sonic-port/sonic-port:PORT/PORT_LIST/5",
        "value": {
            "port_name": "Ethernet2",
            "alias": "Eth1/3",
            "lanes": "67",
            "description": "",
            "speed": 10000
        }
    },
    {
        "op": "add",
        "path": "/sonic-acl:sonic-acl/sonic-acl:ACL_TABLE/ACL_TABLE_LIST/0/ports/1",
        "value": "Ethernet1"
    },
    {
        "op": "add",
        "path": "/sonic-acl:sonic-acl/sonic-acl:ACL_TABLE/ACL_TABLE_LIST/0/ports/2",
        "value": "Ethernet2"
    },
    {
        "op": "add",
        "path": "/sonic-acl:sonic-acl/sonic-acl:ACL_TABLE/ACL_TABLE_LIST/0/ports/3",
        "value": "Ethernet3"
    }
])

SONIC_YANG_AFTER_MULTI_PATCH = {
    "sonic-vlan:sonic-vlan": {
        "sonic-vlan:VLAN_MEMBER": {
            "VLAN_MEMBER_LIST": [
                {
                    "vlan_name": "Vlan1000",
                    "port": "Ethernet0",
                    "tagging_mode": "untagged"
                },
                {
                    "vlan_name": "Vlan1000",
                    "port": "Ethernet4",
                    "tagging_mode": "untagged"
                },
                {
                    "vlan_name": "Vlan1000",
                    "port": "Ethernet8",
                    "tagging_mode": "untagged"
                },
                {
                    "vlan_name": "Vlan100",
                    "port": "Ethernet2",
                    "tagging_mode": "untagged"
                },
                {
                    "vlan_name": "Vlan100",
                    "port": "Ethernet3",
                    "tagging_mode": "untagged"
                },
                {
                    "vlan_name": "Vlan100",
                    "port": "Ethernet1",
                    "tagging_mode": "untagged"
                }
            ]
        },
        "sonic-vlan:VLAN": {
            "VLAN_LIST": [
                {
                    "vlan_name": "Vlan1000",
                    "vlanid": 1000,
                    "dhcp_servers": [
                        "192.0.0.1",
                        "192.0.0.2",
                        "192.0.0.3",
                        "192.0.0.4"
                    ]
                }
            ]
        }
    },
    "sonic-acl:sonic-acl": {
        "sonic-acl:ACL_TABLE": {
            "ACL_TABLE_LIST": [
                {
                    "ACL_TABLE_NAME": "NO-NSW-PACL-V4",
                    "type": "L3",
                    "policy_desc": "NO-NSW-PACL-V4",
                    "ports": [
                        "Ethernet0",
                        "Ethernet1",
                        "Ethernet2",
                        "Ethernet3"
                    ]
                },
                {
                    "ACL_TABLE_NAME": "DATAACL",
                    "policy_desc": "DATAACL",
                    "ports": [
                        "Ethernet4"
                    ],
                    "stage": "ingress",
                    "type": "L3"
                },
                {
                    "ACL_TABLE_NAME": "EVERFLOW",
                    "policy_desc": "EVERFLOW",
                    "ports": [
                        "Ethernet8"
                    ],
                    "stage": "ingress",
                    "type": "MIRROR"
                },
                {
                    "ACL_TABLE_NAME": "EVERFLOWV6",
                    "policy_desc": "EVERFLOWV6",
                    "ports": [
                        "Ethernet4",
                        "Ethernet8"
                    ],
                    "stage": "ingress",
                    "type": "MIRRORV6"
                }
            ]
        }
    },
    "sonic-port:sonic-port": {
        "sonic-port:PORT": {
            "PORT_LIST": [
                {
                    "port_name": "Ethernet0",
                    "alias": "Eth1/1",
                    "lanes": "65",
                    "description": "",
                    "speed": 10000
                },
                {
                    "port_name": "Ethernet4",
                    "admin_status": "up",
                    "alias": "fortyGigE0/4",
                    "description": "Servers0:eth0",
                    "index": 1,
                    "lanes": "29,30,31,32",
                    "mtu": 9100,
                    "pfc_asym": "off",
                    "speed": 40000
                },
                {
                    "port_name": "Ethernet8",
                    "admin_status": "up",
                    "alias": "fortyGigE0/8",
                    "description": "Servers1:eth0",
                    "index": 2,
                    "lanes": "33,34,35,36",
                    "mtu": 9100,
                    "pfc_asym": "off",
                    "speed": 40000
                },
                {
                    "port_name": "Ethernet3",
                    "alias": "Eth1/4",
                    "lanes": "68",
                    "description": "",
                    "speed": 10000
                },
                {
                    "port_name": "Ethernet1",
                    "alias": "Eth1/2",
                    "lanes": "66",
                    "description": "",
                    "speed": 10000
                },
                {
                    "port_name": "Ethernet2",
                    "alias": "Eth1/3",
                    "lanes": "67",
                    "description": "",
                    "speed": 10000
                }
            ]
        }
    }
}
