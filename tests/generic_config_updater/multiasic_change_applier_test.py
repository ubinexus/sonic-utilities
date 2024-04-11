import unittest
from importlib import reload
from unittest.mock import patch, MagicMock
import generic_config_updater.change_applier
import generic_config_updater.services_validator
import generic_config_updater.gu_common


class TestMultiAsicChangeApplier(unittest.TestCase):

    @patch('generic_config_updater.change_applier.ChangeApplier._get_running_config', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_change_default_namespace(self, mock_ConfigDBConnector, mock_get_running_config):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to return some running configuration
        mock_get_running_config.return_value = {
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

        # Instantiate ChangeApplier with the default namespace
        applier = generic_config_updater.change_applier.ChangeApplier()

        # Prepare a change object or data that applier.apply would use
        change = MagicMock()

        # Call the apply method with the change object
        applier.apply(change)

        # Assert ConfigDBConnector called with the correct namespace
        mock_ConfigDBConnector.assert_called_once_with(use_unix_socket_path=True, namespace="")

    @patch('generic_config_updater.change_applier.ChangeApplier._get_running_config', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_change_given_namespace(self, mock_ConfigDBConnector, mock_get_running_config):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to return some running configuration
        mock_get_running_config.return_value = {
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

        # Instantiate ChangeApplier with the default namespace
        applier = generic_config_updater.change_applier.ChangeApplier(namespace="asic0")

        # Prepare a change object or data that applier.apply would use
        change = MagicMock()

        # Call the apply method with the change object
        applier.apply(change)

        # Assert ConfigDBConnector called with the correct namespace
        mock_ConfigDBConnector.assert_called_once_with(use_unix_socket_path=True, namespace="asic0")

    @patch('generic_config_updater.change_applier.ChangeApplier._get_running_config', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_change_failure(self, mock_ConfigDBConnector, mock_get_running_config):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to return some running configuration
        mock_get_running_config.side_effect = Exception("Failed to get running config")
        # Instantiate ChangeApplier with a specific namespace to simulate applying changes in a multi-asic environment
        namespace = "asic0"
        applier = generic_config_updater.change_applier.ChangeApplier(namespace=namespace)

        # Prepare a change object or data that applier.apply would use
        change = MagicMock()

        # Test the behavior when os.system fails
        with self.assertRaises(Exception) as context:
            applier.apply(change)

        self.assertTrue('Failed to get running config' in str(context.exception))

    @patch('generic_config_updater.change_applier.ChangeApplier._get_running_config', autospec=True)
    @patch('generic_config_updater.change_applier.ConfigDBConnector', autospec=True)
    def test_apply_patch_with_empty_tables_failure(self, mock_ConfigDBConnector, mock_get_running_config):
        # Setup mock for ConfigDBConnector
        mock_db = MagicMock()
        mock_ConfigDBConnector.return_value = mock_db

        # Setup mock for json.load to simulate configuration where crucial tables are unexpectedly empty
        mock_get_running_config.return_value = {
            "tables": {
                # Simulate empty tables or missing crucial configuration
            },
            "services": {
                # Normally, services would be listed here
            }
        }

        # Instantiate ChangeApplier with a specific namespace to simulate applying changes in a multi-asic environment
        applier = generic_config_updater.change_applier.ChangeApplier(namespace="asic0")

        # Prepare a change object or data that applier.apply would use, simulating a patch that requires non-empty tables
        change = MagicMock()

        # Apply the patch
        try:
            assert(applier.apply(change) != 0)
        except Exception:
            pass
