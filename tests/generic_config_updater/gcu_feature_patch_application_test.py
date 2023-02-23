import jsonpatch
import unittest
from unittest.mock import MagicMock, Mock

import generic_config_updater.patch_sorter as ps
from .gutest_helpers import Files
from generic_config_updater.gu_common import ConfigWrapper, PatchWrapper, OperationWrapper, \
                                             GenericConfigUpdaterError, OperationType, JsonChange, PathAddressing


class TestFeaturePatchApplication(unittest.TestCase):
    def setUp(self):
        self.config_wrapper = ConfigWrapper()

    def test_feature_patch_application_success(self):
        # Format of the JSON file containing the test-cases:
        #
        # {
        #     "<unique_name_for_the_test>":{
        #         "desc":"<brief explanation of the test case>",
        #         "current_config":<the running config to be modified>,
        #         "patch":<the JsonPatch to apply>,
        #         "expected_config":<the config after jsonpatch modification>
        #     },
        #     .
        #     .
        #     .
        # }
        data = Files.FEATURE_PATCH_APPLICATION_TEST_SUCCESS
        for test_case_name in data:
            with self.subTest(name=test_case_name):
                self.run_single_success_case(data[test_case_name])

    def test_feature_patch_application_failure(self):
        # Fromat of the JSON file containing the test-cases:
        #
        # {
        #     "<unique_name_for_the_test>":{
        #         "desc":"<brief explanation of the test case>",
        #         "current_config":<the running config to be modified>,
        #         "patch":<the JsonPatch to apply>,
        #         "expected_config":<the config after jsonpatch modification>
        #     },
        #     .
        #     .
        #     .
        # }
        data = Files.FEATURE_PATCH_APPLICATION_TEST_FAILURE
        for test_case_name in data:
            with self.subTest(name=test_case_name):
                self.run_single_failure_case(data[test_case_name])
    
    def create_strict_patch_sorter(self, config):
        config_wrapper = self.config_wrapper
        config_wrapper.get_config_db_as_json = MagicMock(return_value=config)
        patch_wrapper = PatchWrapper(config_wrapper)
        operation_wrapper = OperationWrapper()
        path_addressing = ps.PathAddressing(config_wrapper)
        sort_algorithm_factory = ps.SortAlgorithmFactory(operation_wrapper, config_wrapper, path_addressing)
        return ps.StrictPatchSorter(config_wrapper, patch_wrapper)
   
    def run_single_success_case(self, data):
        current_config = data["current_config"]
        expected_config = data["expected_config"]
        patch = jsonpatch.JsonPatch(data["patch"])
        sorter = self.create_strict_patch_sorter(current_config)
        actual_changes = sorter.sort(patch)
        target_config = patch.apply(current_config)
        simulated_config = current_config
        for change in actual_changes:
            simulated_config = change.apply(simulated_config)
            is_valid, error = self.config_wrapper.validate_config_db_config(simulated_config)
            self.assertTrue(is_valid, f"Change will produce invalid config. Error: {error}")
        self.assertEqual(target_config, simulated_config)
        self.assertEqual(simulated_config, expected_config)

    def run_single_failure_case(self, data):
        current_config = data["current_config"]
        patch = jsonpatch.JsonPatch(data["patch"])
        expected_error_substrings = data["expected_error_substrings"]

        try:
            sorter = self.create_strict_patch_sorter(current_config)
            sorter.sort(patch)
            self.fail("An exception was supposed to be thrown")
        except Exception as ex:
            notfound_substrings = []
            error = str(ex)
            for substring in expected_error_substrings:
                if substring not in error:
                    notfound_substrings.append(substring)

            if notfound_substrings:
                self.fail(f"Did not find the expected substrings {notfound_substrings} in the error: '{error}'")


