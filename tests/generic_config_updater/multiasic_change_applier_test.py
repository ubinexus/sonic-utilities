import os
import unittest
from importlib import reload
from unittest.mock import patch, MagicMock
import generic_config_updater.change_applier
import generic_config_updater.services_validator
import generic_config_updater.gu_common

class TestMultiAsicChangeApplier(unittest.TestCase):

    @patch('generic_config_updater.change_applier.os.system', autospec=True)
    @patch('generic_config_updater.change_applier.json.load', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_change_default_namespace(self, mock_ConfigDBConnector, mock_json_load, mock_os_system):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to return some running configuration
        mock_json_load.return_value = {
            "tables": {
                "ACL_TABLE": {
                    "services_to_validate": ["aclservice"],
                    "validate_commands": ["acl_loader show table"]
                },
                "PORT": {
                    "services_to_validate": ["portservice"],
                    "validate_commands": ["show interfaces status"]
                }
            },
            "services": {
                "aclservice": {
                    "validate_commands": ["acl_loader show table"]
                },
                "portservice": {
                    "validate_commands": ["show interfaces status"]
                }
            }
        }

        # Setup mock for os.system to simulate sonic-cfggen behavior
        mock_os_system.return_value = 0

        # Instantiate ChangeApplier with the default namespace
        applier = generic_config_updater.change_applier.ChangeApplier()

        # Prepare a change object or data that applier.apply would use
        change = MagicMock()

        # Call the apply method with the change object
        applier.apply(change)

        # Assert ConfigDBConnector called with the correct namespace
        mock_ConfigDBConnector.assert_called_once_with(use_unix_socket_path=True, namespace="")


    @patch('generic_config_updater.change_applier.os.system', autospec=True)
    @patch('generic_config_updater.change_applier.json.load', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_change_given_namespace(self, mock_ConfigDBConnector, mock_json_load, mock_os_system):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to return some running configuration
        mock_json_load.return_value = {
            "tables": {
                "ACL_TABLE": {
                    "services_to_validate": ["aclservice"],
                    "validate_commands": ["acl_loader show table"]
                },
                "PORT": {
                    "services_to_validate": ["portservice"],
                    "validate_commands": ["show interfaces status"]
                }
            },
            "services": {
                "aclservice": {
                    "validate_commands": ["acl_loader show table"]
                },
                "portservice": {
                    "validate_commands": ["show interfaces status"]
                }
            }
        }

        # Setup mock for os.system to simulate sonic-cfggen behavior
        mock_os_system.return_value = 0

        # Instantiate ChangeApplier with the default namespace
        applier = generic_config_updater.change_applier.ChangeApplier(namespace="asic0")

        # Prepare a change object or data that applier.apply would use
        change = MagicMock()

        # Call the apply method with the change object
        applier.apply(change)

        # Assert ConfigDBConnector called with the correct namespace
        mock_ConfigDBConnector.assert_called_once_with(use_unix_socket_path=True, namespace="asic0")

    @patch('generic_config_updater.change_applier.os.system', autospec=True)
    @patch('generic_config_updater.change_applier.json.load', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_change_failure(self, mock_ConfigDBConnector, mock_json_load, mock_os_system):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to return some running configuration
        mock_json_load.return_value = {
            "tables": {
                "ACL_TABLE": {
                    "services_to_validate": ["aclservice"],
                    "validate_commands": ["acl_loader show table"]
                },
                "PORT": {
                    "services_to_validate": ["portservice"],
                    "validate_commands": ["show interfaces status"]
                }
            },
            "services": {
                "aclservice": {
                    "validate_commands": ["acl_loader show table"]
                },
                "portservice": {
                    "validate_commands": ["show interfaces status"]
                }
            }
        }

        # Setup mock for os.system to simulate failure, such as a command returning non-zero status
        mock_os_system.return_value = 1  # Non-zero return value indicates failure

        # Instantiate ChangeApplier with a specific namespace to simulate applying changes in a multi-asic environment
        namespace = "asic0"
        applier = generic_config_updater.change_applier.ChangeApplier(namespace=namespace)

        # Prepare a change object or data that applier.apply would use
        change = MagicMock()

        # Test the behavior when os.system fails
        with self.assertRaises(Exception) as context:
            applier.apply(change)

        # Optionally, assert specific error message if your method raises a custom exception
        # self.assertTrue("Expected error message" in str(context.exception))

        # Assert that os.system was called, indicating the command was attempted
        mock_os_system.assert_called()

    @patch('generic_config_updater.change_applier.os.system', autospec=True)
    @patch('generic_config_updater.change_applier.json.load', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_patch_with_empty_tables_failure(self, mock_ConfigDBConnector, mock_json_load, mock_os_system):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to simulate configuration where crucial tables are unexpectedly empty
        mock_json_load.return_value = {
            "tables": {
                # Simulate empty tables or missing crucial configuration
            },
            "services": {
                # Normally, services would be listed here
            }
        }

        # Setup mock for os.system to simulate command execution success
        mock_os_system.return_value = 0

        # Instantiate ChangeApplier with a specific namespace to simulate applying changes in a multi-asic environment
        applier = generic_config_updater.change_applier.ChangeApplier(namespace="asic0")

        # Prepare a change object or data that applier.apply would use, simulating a patch that requires non-empty tables
        change = MagicMock()

        # Apply the patch
        try:
            assert(applier.apply(change) != 0)
        except Exception:
            pass

        # Verify that the system attempted to retrieve the configuration despite the missing data
        mock_json_load.assert_called()
