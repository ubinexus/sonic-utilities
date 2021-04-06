import json
import jsonpatch
import os
import shutil
import unittest
from imp import load_source
from unittest.mock import Mock, call
load_source('gu', \
    os.path.join(os.path.dirname(__file__), '../..', 'generic_config_updater', 'generic_updater.py'))
import gu

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

class FilesLoader:
    def __getattr__(self, attr):
        return self.__load(attr)

    def __load(self, file_name):
        normalized_file_name = file_name.lower()

        # Try load dict file
        json_file_path = os.path.join("files", f"{normalized_file_name}.py-dict")
        if os.path.isfile(json_file_path):
            with open(json_file_path) as fh:
                text = fh.read()
                return eval(text)

        # Try load json file
        json_file_path = os.path.join("files", f"{normalized_file_name}.json")
        if os.path.isfile(json_file_path):
            with open(json_file_path) as fh:
                text = fh.read()
                return json.loads(text)

        # Try load json-patch file
        jsonpatch_file_path = os.path.join("files", f"{normalized_file_name}.json-patch")
        if os.path.isfile(jsonpatch_file_path):
            with open(jsonpatch_file_path) as fh:
                text = fh.read()
                return jsonpatch.JsonPatch(json.loads(text))
        
        raise ValueError(f"There is no file called '{file_name}' in 'files/' directory")
        
# Files.File_Name will look for a file called "file_name" in the "files/" directory
Files = FilesLoader()

class TestConfigWrapper(unittest.TestCase):
    def test_ctor__default_values_set(self):
        config_wrapper = gu.ConfigWrapper()

        self.assertEqual(None, config_wrapper.default_config_db_connector)
        self.assertEqual("/usr/local/yang-models", gu.YANG_DIR)

    def test_get_config_db_as_json__returns_config_db_as_json(self):
        # Arrange
        config_db_connector_mock = self.__get_config_db_connector_mock(Files.CONFIG_DB_AS_DICT)
        config_wrapper = gu.ConfigWrapper(default_config_db_connector = config_db_connector_mock)
        expected = Files.CONFIG_DB_AS_JSON

        # Act
        actual = config_wrapper.get_config_db_as_json()

        # Assert
        self.assertDictEqual(expected, actual)

    def test_get_sonic_yang_as_json__returns_sonic_yang_as_json(self):
        # Arrange
        config_db_connector_mock = self.__get_config_db_connector_mock(Files.CONFIG_DB_AS_DICT)
        config_wrapper = gu.ConfigWrapper(default_config_db_connector = config_db_connector_mock)
        expected = Files.SONIC_YANG_AS_JSON

        # Act
        actual = config_wrapper.get_sonic_yang_as_json()

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_config_db_to_sonic_yang__empty_config_db__returns_empty_sonic_yang(self):
        # Arrange
        config_wrapper = gu.ConfigWrapper()
        expected = {}

        # Act
        actual = config_wrapper.convert_config_db_to_sonic_yang({})

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_config_db_to_sonic_yang__non_empty_config_db__returns_sonic_yang_as_json(self):
        # Arrange
        config_wrapper = gu.ConfigWrapper()
        expected = Files.SONIC_YANG_AS_JSON

        # Act
        actual = config_wrapper.convert_config_db_to_sonic_yang(Files.CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_sonic_yang_to_config_db__empty_sonic_yang__returns_empty_config_db(self):
        # Arrange
        config_wrapper = gu.ConfigWrapper()
        expected = {}

        # Act
        actual = config_wrapper.convert_sonic_yang_to_config_db({})

        # Assert
        self.assertDictEqual(expected, actual)

    def test_convert_sonic_yang_to_config_db__non_empty_sonic_yang__returns_config_db_as_json(self):
        # Arrange
        config_wrapper = gu.ConfigWrapper()
        expected = Files.CROPPED_CONFIG_DB_AS_JSON

        # Act
        actual = config_wrapper.convert_sonic_yang_to_config_db(Files.SONIC_YANG_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_validate_sonic_yang_config__valid_config__returns_true(self):
        # Arrange
        config_wrapper = gu.ConfigWrapper()
        expected = True

        # Act
        actual = config_wrapper.validate_sonic_yang_config(Files.SONIC_YANG_AS_JSON)

        # Assert
        self.assertEqual(expected, actual)

    def test_validate_sonic_yang_config__invvalid_config__returns_false(self):
        # Arrange
        config_wrapper = gu.ConfigWrapper()
        expected = False

        # Act
        actual = config_wrapper.validate_sonic_yang_config(Files.SONIC_YANG_AS_JSON_INVALID)

        # Assert
        self.assertEqual(expected, actual)

    def test_crop_tables_without_yang__returns_cropped_config_db_as_json(self):
        # Arrange
        config_wrapper = gu.ConfigWrapper()
        expected = Files.CROPPED_CONFIG_DB_AS_JSON

        # Act
        actual = config_wrapper.crop_tables_without_yang(Files.CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def __get_config_db_connector_mock(self, config_db_as_dict):
        mock_connector = Mock()
        mock_connector.get_config.return_value = config_db_as_dict
        return mock_connector

class TestPatchWrapper(unittest.TestCase):
    def test_validate_config_db_patch__table_without_yang_model__returns_false(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()
        patch = [ { 'op': 'remove', 'path': '/TABLE_WITHOUT_YANG' } ]
        expected = False

        # Act
        actual = patch_wrapper.validate_config_db_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_validate_config_db_patch__table_with_yang_model__returns_true(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()
        patch = [ { 'op': 'remove', 'path': '/ACL_TABLE' } ]
        expected = True

        # Act
        actual = patch_wrapper.validate_config_db_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__invalid_config_db_patch__failure(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()
        patch = [ { 'op': 'remove', 'path': '/TABLE_WITHOUT_YANG' } ]

        # Act and Assert
        self.assertRaises(Exception, patch_wrapper.convert_config_db_patch_to_sonic_yang_patch, patch)

    def test_same_patch__no_diff__returns_true(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()

        # Act and Assert
        self.assertTrue(patch_wrapper.verify_same_json(Files.CONFIG_DB_AS_JSON, Files.CONFIG_DB_AS_JSON))

    def test_same_patch__diff__returns_false(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()

        # Act and Assert
        self.assertFalse(patch_wrapper.verify_same_json(Files.CONFIG_DB_AS_JSON, Files.CROPPED_CONFIG_DB_AS_JSON))

    def test_generate_patch__no_diff__empty_patch(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()

        # Act
        patch = patch_wrapper.generate_patch(Files.CONFIG_DB_AS_JSON, Files.CONFIG_DB_AS_JSON)

        # Assert
        self.assertFalse(patch)

    def test_simulate_patch__empty_patch__no_changes(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()
        patch = jsonpatch.JsonPatch([])
        expected = Files.CONFIG_DB_AS_JSON

        # Act
        actual = patch_wrapper.simulate_patch(patch, Files.CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_simulate_patch__non_empty_patch__changes_applied(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()
        patch = Files.SINGLE_OPERATION_CONFIG_DB_PATCH
        expected = Files.SINGLE_OPERATION_CONFIG_DB_PATCH.apply(Files.CONFIG_DB_AS_JSON)

        # Act
        actual = patch_wrapper.simulate_patch(patch, Files.CONFIG_DB_AS_JSON)

        # Assert
        self.assertDictEqual(expected, actual)

    def test_generate_patch__diff__non_empty_patch(self):
        # Arrange
        patch_wrapper = gu.PatchWrapper()
        after_update_json = Files.SINGLE_OPERATION_CONFIG_DB_PATCH.apply(Files.CONFIG_DB_AS_JSON)
        expected = Files.SINGLE_OPERATION_CONFIG_DB_PATCH

        # Act
        actual = patch_wrapper.generate_patch(Files.CONFIG_DB_AS_JSON, after_update_json)

        # Assert
        self.assertTrue(actual)
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__empty_patch__returns_empty_patch(self):
        # Arrange
        config_wrapper = self.__get_config_wrapper_mock(Files.CONFIG_DB_AS_DICT)
        patch_wrapper = gu.PatchWrapper(config_wrapper = config_wrapper)
        patch = jsonpatch.JsonPatch([])
        expected = jsonpatch.JsonPatch([])

        # Act
        actual = patch_wrapper.convert_config_db_patch_to_sonic_yang_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__single_operation_patch__returns_sonic_yang_patch(self):
        # Arrange
        config_wrapper = self.__get_config_wrapper_mock(Files.CONFIG_DB_AS_DICT)
        patch_wrapper = gu.PatchWrapper(config_wrapper = config_wrapper)
        patch = Files.SINGLE_OPERATION_CONFIG_DB_PATCH
        expected = Files.SINGLE_OPERATION_SONIC_YANG_PATCH

        # Act
        actual = patch_wrapper.convert_config_db_patch_to_sonic_yang_patch(patch)

        # Assert
        self.assertEqual(expected, actual)

    def test_convert_config_db_patch_to_sonic_yang_patch__multiple_operations_patch__returns_sonic_yang_patch(self):
        # Arrange
        config_wrapper = self.__get_config_wrapper_mock(Files.CONFIG_DB_AS_DICT)
        patch_wrapper = gu.PatchWrapper(config_wrapper = config_wrapper)
        config_db_patch = Files.MULTI_OPERATION_CONFIG_DB_PATCH

        # Act
        sonic_yang_patch = patch_wrapper.convert_config_db_patch_to_sonic_yang_patch(config_db_patch)

        # Assert
        self.__assert_same_patch(config_db_patch, sonic_yang_patch, config_wrapper, patch_wrapper)

    def __assert_same_patch(self, config_db_patch, sonic_yang_patch, config_wrapper, patch_wrapper):
        sonic_yang = config_wrapper.get_sonic_yang_as_json()
        config_db = config_wrapper.get_config_db_as_json()

        after_update_sonic_yang = patch_wrapper.simulate_patch(sonic_yang_patch, sonic_yang)
        after_update_config_db = patch_wrapper.simulate_patch(config_db_patch, config_db)

        after_update_config_db_as_sonic_yang = \
            config_wrapper.convert_config_db_to_sonic_yang(after_update_config_db)

        self.assertTrue(patch_wrapper.verify_same_json(after_update_sonic_yang, after_update_config_db_as_sonic_yang))

    def __get_config_wrapper_mock(self, config_db_as_dict):
        config_db_connector_mock = self.__get_config_db_connector_mock(config_db_as_dict)
        config_wrapper = gu.ConfigWrapper(default_config_db_connector = config_db_connector_mock)
        return config_wrapper

    def __get_config_db_connector_mock(self, config_db_as_dict):
        mock_connector = Mock()
        mock_connector.get_config.return_value = config_db_as_dict
        return mock_connector

class TestPatchApplier(unittest.TestCase):
    def test_apply__invalid_sonic_yang__failure(self):
        # Arrange
        patch_applier = self.__create_patch_applier(valid_sonic_yang=False)

        # Act and assert
        self.assertRaises(Exception, patch_applier.apply, Files.MULTI_OPERATION_SONIC_YANG_PATCH)

    def test_apply__json_not_fully_updated__failure(self):
        # Arrange
        patch_applier = self.__create_patch_applier(verified_same_config=False)

        # Act and assert
        self.assertRaises(Exception, patch_applier.apply, Files.MULTI_OPERATION_SONIC_YANG_PATCH)

    def test_apply__no_errors__update_successful(self):
        # Arrange
        changes = [Mock(), Mock()]
        patch_applier = self.__create_patch_applier(changes)

        # Act
        patch_applier.apply(Files.MULTI_OPERATION_SONIC_YANG_PATCH)

        # Assert
        patch_applier.config_wrapper.get_sonic_yang_as_json.assert_has_calls([call(), call()])
        patch_applier.patch_wrapper.simulate_patch.assert_has_calls( \
            [call(Files.MULTI_OPERATION_SONIC_YANG_PATCH, Files.SONIC_YANG_AS_JSON)])
        patch_applier.config_wrapper.validate_sonic_yang_config.assert_has_calls( \
            [call(Files.SONIC_YANG_AFTER_MULTI_PATCH)])
        patch_applier.patchorderer.order.assert_has_calls([call(Files.MULTI_OPERATION_SONIC_YANG_PATCH)])
        patch_applier.changeapplier.apply.assert_has_calls([call(changes[0]), call(changes[1])])
        patch_applier.patch_wrapper.verify_same_json.assert_has_calls( \
            [call(Files.SONIC_YANG_AFTER_MULTI_PATCH, Files.SONIC_YANG_AFTER_MULTI_PATCH)])

    def __create_patch_applier(self, changes=None, valid_sonic_yang=True, verified_same_config=True):
        config_wrapper = Mock()
        config_wrapper.get_sonic_yang_as_json.side_effect = \
            [Files.SONIC_YANG_AS_JSON, Files.SONIC_YANG_AFTER_MULTI_PATCH]
        config_wrapper.validate_sonic_yang_config.side_effect = \
            create_side_effect_dict({(str(Files.SONIC_YANG_AFTER_MULTI_PATCH),): valid_sonic_yang})

        patch_wrapper = Mock()
        patch_wrapper.simulate_patch.side_effect = \
            create_side_effect_dict( \
                {(str(Files.MULTI_OPERATION_SONIC_YANG_PATCH), str(Files.SONIC_YANG_AS_JSON)): \
                    Files.SONIC_YANG_AFTER_MULTI_PATCH})
        patch_wrapper.verify_same_json.side_effect = \
            create_side_effect_dict( \
                {(str(Files.SONIC_YANG_AFTER_MULTI_PATCH), str(Files.SONIC_YANG_AFTER_MULTI_PATCH)): \
                    verified_same_config})

        changes = [Mock(), Mock()] if not changes else changes
        patchorderer = Mock()
        patchorderer.order.side_effect = \
            create_side_effect_dict({(str(Files.MULTI_OPERATION_SONIC_YANG_PATCH),): changes})

        changeapplier = Mock()
        changeapplier.apply.side_effect = create_side_effect_dict({(str(changes[0]),): 0, (str(changes[1]),): 0})

        return gu.PatchApplier(patchorderer, changeapplier, config_wrapper, patch_wrapper)

class TestConfigReplacer(unittest.TestCase):
    def test_replace__invalid_sonic_yang__failure(self):
        # Arrange
        config_replacer = self.__create_config_replacer(valid_sonic_yang=False)

        # Act and assert
        self.assertRaises(Exception, config_replacer.replace, Files.SONIC_YANG_AFTER_MULTI_PATCH)

    def test_replace__json_not_fully_updated__failure(self):
        # Arrange
        config_replacer = self.__create_config_replacer(verified_same_config=False)

        # Act and assert
        self.assertRaises(Exception, config_replacer.replace, Files.SONIC_YANG_AFTER_MULTI_PATCH)

    def test_replace__no_errors__update_successful(self):
        # Arrange
        config_replacer = self.__create_config_replacer()

        # Act
        config_replacer.replace(Files.SONIC_YANG_AFTER_MULTI_PATCH)

        # Assert
        config_replacer.config_wrapper.validate_sonic_yang_config.assert_has_calls( \
            [call(Files.SONIC_YANG_AFTER_MULTI_PATCH)])
        config_replacer.config_wrapper.get_sonic_yang_as_json.assert_has_calls([call(), call()])
        config_replacer.patch_wrapper.generate_patch.assert_has_calls( \
            [call(Files.SONIC_YANG_AS_JSON, Files.SONIC_YANG_AFTER_MULTI_PATCH)])
        config_replacer.patch_applier.apply.assert_has_calls([call(Files.MULTI_OPERATION_SONIC_YANG_PATCH)])
        config_replacer.patch_wrapper.verify_same_json.assert_has_calls( \
            [call(Files.SONIC_YANG_AFTER_MULTI_PATCH, Files.SONIC_YANG_AFTER_MULTI_PATCH)])

    def __create_config_replacer(self, changes=None, valid_sonic_yang=True, verified_same_config=True):
        config_wrapper = Mock()
        config_wrapper.validate_sonic_yang_config.side_effect = \
            create_side_effect_dict({(str(Files.SONIC_YANG_AFTER_MULTI_PATCH),): valid_sonic_yang})
        config_wrapper.get_sonic_yang_as_json.side_effect = \
            [Files.SONIC_YANG_AS_JSON, Files.SONIC_YANG_AFTER_MULTI_PATCH]

        patch_wrapper = Mock()
        patch_wrapper.generate_patch.side_effect = \
            create_side_effect_dict( \
                {(str(Files.SONIC_YANG_AS_JSON), str(Files.SONIC_YANG_AFTER_MULTI_PATCH)): \
                    Files.MULTI_OPERATION_SONIC_YANG_PATCH})
        patch_wrapper.verify_same_json.side_effect = \
            create_side_effect_dict( \
                {(str(Files.SONIC_YANG_AFTER_MULTI_PATCH), str(Files.SONIC_YANG_AFTER_MULTI_PATCH)): \
                    verified_same_config})

        changes = [Mock(), Mock()] if not changes else changes
        patchorderer = Mock()
        patchorderer.order.side_effect = create_side_effect_dict({(str(Files.MULTI_OPERATION_SONIC_YANG_PATCH),): \
            changes})

        patch_applier = Mock()
        patch_applier.apply.side_effect = create_side_effect_dict({(str(Files.MULTI_OPERATION_SONIC_YANG_PATCH),): 0})

        return gu.ConfigReplacer(patch_applier, config_wrapper, patch_wrapper)

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

        config_wrapper = Mock()
        config_wrapper.get_sonic_yang_as_json.return_value = self.any_config

        return gu.FileSystemConfigRollbacker( \
            checkpoints_dir=self.checkpoints_dir, \
                config_replacer=replacer, \
                    config_wrapper=config_wrapper)

class TestGenericUpdateFactory(unittest.TestCase):
    def setUp(self):
        self.any_verbose=True
        self.any_dry_run=True

    def test_create_patch_applier__invalid_config_format__failure(self):
        # Arrange
        factory = gu.GenericUpdateFactory()

        # Act and assert
        self.assertRaises( \
            ValueError, factory.create_patch_applier, "INVALID_FORMAT", self.any_verbose, self.any_dry_run)

    def test_create_patch_applier__different_options(self):
        # Arrange
        options = [
            {"verbose": {True: None, False: None}},
            {"dry_run": {True: None, False: gu.ConfigLockDecorator}},
            {
                "config_format": {
                    gu.ConfigFormat.SONICYANG: None,
                    gu.ConfigFormat.CONFIGDB: gu.ConfigDbDecorator
                }
            },
        ]

        # Act and assert
        self.recursively_test_create_func(options, 0, {}, [], self.validate_create_patch_applier)

    def test_create_config_replacer__invalid_config_format__failure(self):
        # Arrange
        factory = gu.GenericUpdateFactory()

        # Act and assert
        self.assertRaises( \
            ValueError, factory.create_config_replacer, "INVALID_FORMAT", self.any_verbose, self.any_dry_run)

    def test_create_config_replacer__different_options(self):
        # Arrange
        options = [
            {"verbose": {True: None, False: None}},
            {"dry_run": {True: None, False: gu.ConfigLockDecorator}},
            {
                "config_format": {
                    gu.ConfigFormat.SONICYANG: None,
                    gu.ConfigFormat.CONFIGDB: gu.ConfigDbDecorator
                }
            },
        ]

        # Act and assert
        self.recursively_test_create_func(options, 0, {}, [], self.validate_create_config_replacer)

    def test_create_config_rollbacker__different_options(self):
        # Arrange
        options = [
            {"verbose": {True: None, False: None}},
            {"dry_run": {True: None, False: gu.ConfigLockDecorator}}
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
        factory = gu.GenericUpdateFactory()
        patch_applier = factory.create_patch_applier(params["config_format"], params["verbose"], params["dry_run"])
        for decorator_type in expected_decorators:
            self.assertIsInstance(patch_applier, decorator_type)

            patch_applier = patch_applier.decorated_patch_applier

        self.assertIsInstance(patch_applier, gu.PatchApplier)
        if params["dry_run"]:
            self.assertIsInstance(patch_applier.config_wrapper, gu.DryRunConfigWrapper)
        else:
            self.assertIsInstance(patch_applier.config_wrapper, gu.ConfigWrapper)

    def validate_create_config_replacer(self, params, expected_decorators):
        factory = gu.GenericUpdateFactory()
        config_replacer = factory.create_config_replacer(params["config_format"], params["verbose"], params["dry_run"])
        for decorator_type in expected_decorators:
            self.assertIsInstance(config_replacer, decorator_type)

            config_replacer = config_replacer.decorated_config_replacer

        self.assertIsInstance(config_replacer, gu.ConfigReplacer)
        if params["dry_run"]:
            self.assertIsInstance(config_replacer.config_wrapper, gu.DryRunConfigWrapper)
            self.assertIsInstance(config_replacer.patch_applier.config_wrapper, gu.DryRunConfigWrapper)
        else:
            self.assertIsInstance(config_replacer.config_wrapper, gu.ConfigWrapper)
            self.assertIsInstance(config_replacer.patch_applier.config_wrapper, gu.ConfigWrapper)

    def validate_create_config_rollbacker(self, params, expected_decorators):
        factory = gu.GenericUpdateFactory()
        config_rollbacker = factory.create_config_rollbacker(params["verbose"], params["dry_run"])
        for decorator_type in expected_decorators:
            self.assertIsInstance(config_rollbacker, decorator_type)

            config_rollbacker = config_rollbacker.decorated_config_rollbacker

        self.assertIsInstance(config_rollbacker, gu.FileSystemConfigRollbacker)
        if params["dry_run"]:
            self.assertIsInstance(config_rollbacker.config_wrapper, gu.DryRunConfigWrapper)
            self.assertIsInstance(config_rollbacker.config_replacer.config_wrapper, gu.DryRunConfigWrapper)
            self.assertIsInstance( \
                config_rollbacker.config_replacer.patch_applier.config_wrapper, gu.DryRunConfigWrapper)
        else:
            self.assertIsInstance(config_rollbacker.config_wrapper, gu.ConfigWrapper)
            self.assertIsInstance(config_rollbacker.config_replacer.config_wrapper, gu.ConfigWrapper)
            self.assertIsInstance( \
                config_rollbacker.config_replacer.patch_applier.config_wrapper, gu.ConfigWrapper)

class TestGenericUpdater(unittest.TestCase):
    def setUp(self):
        self.any_checkpoint_name = "anycheckpoint"
        self.any_other_checkpoint_name = "anyothercheckpoint"
        self.any_checkpoints_list = [self.any_checkpoint_name, self.any_other_checkpoint_name]
        self.any_config_format = gu.ConfigFormat.SONICYANG
        self.any_verbose = True
        self.any_dry_run = True

    def test_apply_patch__creates_applier_and_apply(self):
        # Arrange
        patch_applier = Mock()
        patch_applier.apply.side_effect = create_side_effect_dict({(str(Files.SINGLE_OPERATION_SONIC_YANG_PATCH),): 0})

        factory = Mock()
        factory.create_patch_applier.side_effect = \
            create_side_effect_dict( \
                {(str(self.any_config_format), str(self.any_verbose), str(self.any_dry_run),): patch_applier})

        generic_updater = gu.GenericUpdater(factory)

        # Act
        generic_updater.apply_patch( \
            Files.SINGLE_OPERATION_SONIC_YANG_PATCH, self.any_config_format, self.any_verbose, self.any_dry_run)

        # Assert
        patch_applier.apply.assert_has_calls([call(Files.SINGLE_OPERATION_SONIC_YANG_PATCH)])

    def test_replace__creates_replacer_and_replace(self):
        # Arrange
        config_replacer = Mock()
        config_replacer.replace.side_effect = create_side_effect_dict({(str(Files.SONIC_YANG_AS_JSON),): 0})

        factory = Mock()
        factory.create_config_replacer.side_effect = \
            create_side_effect_dict( \
                {(str(self.any_config_format), str(self.any_verbose), str(self.any_dry_run),): config_replacer})

        generic_updater = gu.GenericUpdater(factory)

        # Act
        generic_updater.replace(Files.SONIC_YANG_AS_JSON, self.any_config_format, self.any_verbose, self.any_dry_run)

        # Assert
        config_replacer.replace.assert_has_calls([call(Files.SONIC_YANG_AS_JSON)])

    def test_rollback__creates_rollbacker_and_rollback(self):
        # Arrange
        config_rollbacker = Mock()
        config_rollbacker.rollback.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})

        factory = Mock()
        factory.create_config_rollbacker.side_effect = \
            create_side_effect_dict({(str(self.any_verbose), str(self.any_dry_run),): config_rollbacker})

        generic_updater = gu.GenericUpdater(factory)

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

        generic_updater = gu.GenericUpdater(factory)

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

        generic_updater = gu.GenericUpdater(factory)

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

        generic_updater = gu.GenericUpdater(factory)

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
        config_db_decorator.apply(Files.CONFIG_DB_AS_JSON)

        # Assert
        config_db_decorator.patch_wrapper.convert_config_db_patch_to_sonic_yang_patch.assert_has_calls( \
            [call(Files.CONFIG_DB_AS_JSON)])
        config_db_decorator.decorated_patch_applier.apply.assert_has_calls([call(Files.SONIC_YANG_AS_JSON)])

    def test_replace__converts_to_yang_and_calls_decorated_class(self):
        # Arrange
        config_db_decorator = self.__create_config_db_decorator()

        # Act
        config_db_decorator.replace(Files.CONFIG_DB_AS_JSON)

        # Assert
        config_db_decorator.config_wrapper.convert_config_db_to_sonic_yang.assert_has_calls( \
            [call(Files.CONFIG_DB_AS_JSON)])
        config_db_decorator.decorated_config_replacer.replace.assert_has_calls([call(Files.SONIC_YANG_AS_JSON)])

    def __create_config_db_decorator(self):
        patch_applier = Mock()
        patch_applier.apply.side_effect = create_side_effect_dict({(str(Files.SONIC_YANG_AS_JSON),): 0})

        patch_wrapper = Mock()
        patch_wrapper.convert_config_db_patch_to_sonic_yang_patch.side_effect = \
            create_side_effect_dict({(str(Files.CONFIG_DB_AS_JSON),): Files.SONIC_YANG_AS_JSON})

        config_replacer = Mock()
        config_replacer.replace.side_effect = create_side_effect_dict({(str(Files.SONIC_YANG_AS_JSON),): 0})

        config_wrapper = Mock()
        config_wrapper.convert_config_db_to_sonic_yang.side_effect = \
            create_side_effect_dict({(str(Files.CONFIG_DB_AS_JSON),): Files.SONIC_YANG_AS_JSON})

        return gu.ConfigDbDecorator( \
            decorated_patch_applier=patch_applier, \
                decorated_config_replacer=config_replacer, \
                    patch_wrapper=patch_wrapper, \
                        config_wrapper=config_wrapper)

class TestConfigLockDecorator(unittest.TestCase):
    def setUp(self):
        self.any_checkpoint_name = "anycheckpoint"

    def test_apply__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.apply(Files.SINGLE_OPERATION_SONIC_YANG_PATCH)

        # Assert
        config_lock_decorator.config_lock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_patch_applier.apply.assert_has_calls( \
            [call(Files.SINGLE_OPERATION_SONIC_YANG_PATCH)])
        config_lock_decorator.config_lock.release_lock.assert_called_once()

    def test_replace__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.replace(Files.SONIC_YANG_AS_JSON)

        # Assert
        config_lock_decorator.config_lock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_config_replacer.replace.assert_has_calls([call(Files.SONIC_YANG_AS_JSON)])
        config_lock_decorator.config_lock.release_lock.assert_called_once()

    def test_rollback__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.rollback(self.any_checkpoint_name)

        # Assert
        config_lock_decorator.config_lock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_config_rollbacker.rollback.assert_has_calls([call(self.any_checkpoint_name)])
        config_lock_decorator.config_lock.release_lock.assert_called_once()

    def test_checkpoint__lock_config(self):
        # Arrange
        config_lock_decorator = self.__create_config_lock_decorator()

        # Act
        config_lock_decorator.checkpoint(self.any_checkpoint_name)

        # Assert
        config_lock_decorator.config_lock.acquire_lock.assert_called_once()
        config_lock_decorator.decorated_config_rollbacker.checkpoint.assert_has_calls([call(self.any_checkpoint_name)])
        config_lock_decorator.config_lock.release_lock.assert_called_once()

    def __create_config_lock_decorator(self):
        config_lock = Mock()

        patch_applier = Mock()
        patch_applier.apply.side_effect = create_side_effect_dict({(str(Files.SINGLE_OPERATION_SONIC_YANG_PATCH),): 0})

        config_replacer = Mock()
        config_replacer.replace.side_effect = create_side_effect_dict({(str(Files.SONIC_YANG_AS_JSON),): 0})

        config_rollbacker = Mock()
        config_rollbacker.rollback.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})
        config_rollbacker.checkpoint.side_effect = create_side_effect_dict({(self.any_checkpoint_name,): 0})

        return gu.ConfigLockDecorator( \
            config_lock=config_lock, \
                decorated_patch_applier=patch_applier, \
                    decorated_config_replacer=config_replacer, \
                        decorated_config_rollbacker=config_rollbacker)
