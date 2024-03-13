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
