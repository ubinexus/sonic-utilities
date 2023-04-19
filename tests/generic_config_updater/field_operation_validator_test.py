import io
import unittest
import mock
import json
import subprocess
import generic_config_updater
import generic_config_updater.field_operation_validators as fov
import generic_config_updater.gu_common as gu_common

from unittest.mock import MagicMock, Mock, mock_open
from mock import patch
from sonic_py_common.device_info import get_hwsku, get_sonic_version_info


class TestValidateFieldOperation(unittest.TestCase):

    @patch("sonic_py_common.device_info.get_sonic_version_info", mock.Mock(return_value={"build_version": "SONiC.20181131"}))
    @patch("generic_config_updater.field_operation_validators.get_asic_name", mock.Mock(return_value="unknown"))
    def test_rdma_config_update_validator_unknown_asic(self):
        path = "/PFC_WD/GLOBAL/POLL_INTERVAL"
        operation = "replace"
        assert generic_config_updater.field_operation_validators.rdma_config_update_validator(path, operation) == False

    @patch("sonic_py_common.device_info.get_sonic_version_info", mock.Mock(return_value={"build_version": "SONiC.20171131"}))
    @patch("generic_config_updater.field_operation_validators.get_asic_name", mock.Mock(return_value="spc1"))
    @patch("os.path.exists", mock.Mock(return_value=True))
    @patch("builtins.open", mock_open(read_data='{"tables": {"pfc_wd": {"validator_data": {"rdma_config_update_validator": {"PFCWD enable/disable": {"fields": ["detection_time", "action"], "operations": ["remove", "replace", "add"], "platforms": {"spc1": "20181100"}}}}}}}'))
    def test_rdma_config_update_validator_spc_asic_invalid_version(self):
        path = "/PFC_WD/Ethernet8/action"
        operation = "replace"
        assert generic_config_updater.field_operation_validators.rdma_config_update_validator(path, operation) == False
    
    @patch("sonic_py_common.device_info.get_sonic_version_info", mock.Mock(return_value={"build_version": "SONiC.20181131"}))
    @patch("generic_config_updater.field_operation_validators.get_asic_name", mock.Mock(return_value="spc1"))
    @patch("os.path.exists", mock.Mock(return_value=True))
    @patch("builtins.open", mock_open(read_data='{"tables": {"pfc_wd": {"validator_data": {"rdma_config_update_validator": {"PFCWD enable/disable": {"fields": ["detection_time", "action"], "operations": ["remove", "replace", "add"], "platforms": {"spc1": "20181100"}}}}}}}'))
    def test_rdma_config_update_validator_spc_asic_valid_version(self):
        path = "/PFC_WD/Ethernet8/action"
        operation = "replace"
        assert generic_config_updater.field_operation_validators.rdma_config_update_validator(path, operation) == True
   
    @patch("sonic_py_common.device_info.get_sonic_version_info", mock.Mock(return_value={"build_version": "SONiC.20181131"}))
    @patch("generic_config_updater.field_operation_validators.get_asic_name", mock.Mock(return_value="spc1"))
    @patch("os.path.exists", mock.Mock(return_value=True))
    @patch("builtins.open", mock_open(read_data='{"tables": {"pfc_wd": {"validator_data": {"rdma_config_update_validator": {"PFCWD enable/disable": {"fields": ["detection_time", "action"], "operations": ["remove", "replace", "add"], "platforms": {"spc1": "20181100"}}}}}}}'))
    def test_rdma_config_update_validator_spc_asic_invalid_op(self):
        path = "/PFC_WD/Ethernet8/action"
        operation = "invalid-op"
        assert generic_config_updater.field_operation_validators.rdma_config_update_validator(path, operation) == False
    
    @patch("sonic_py_common.device_info.get_sonic_version_info", mock.Mock(return_value={"build_version": "SONiC.20181131"}))
    @patch("generic_config_updater.field_operation_validators.get_asic_name", mock.Mock(return_value="spc1"))
    @patch("os.path.exists", mock.Mock(return_value=True))
    @patch("builtins.open", mock_open(read_data='{"tables": {"pfc_wd": {"validator_data": {"rdma_config_update_validator": {"PFCWD enable/disable": {"fields": ["detection_time", "action"], "operations": ["remove", "replace", "add"], "platforms": {"spc1": "20181100"}}}}}}}'))
    def test_rdma_config_update_validator_spc_asic_other_field(self):
        path = "/PFC_WD/Ethernet8/other_field"
        operation = "invalid-op"
        assert generic_config_updater.field_operation_validators.rdma_config_update_validator(path, operation) == False
    
    @patch("sonic_py_common.device_info.get_sonic_version_info", mock.Mock(return_value={"build_version": "SONiC.20181131"}))
    @patch("generic_config_updater.field_operation_validators.get_asic_name", mock.Mock(return_value="unknown"))
    def test_rdma_config_update_validator_unknown_asic(self):
        path = "/PFC_WD/GLOBAL/POLL_INTERVAL"
        operation = "replace"
    
    @patch("sonic_py_common.device_info.get_sonic_version_info", mock.Mock(return_value={"asic_type": "mellanox", "build_version": "SONiC.20181131"}))
    def test_validate_field_operation_legal__pfcwd(self):
        old_config = {"PFC_WD": {"GLOBAL": {"POLL_INTERVAL": "60"}}}
        target_config = {"PFC_WD": {"GLOBAL": {"POLL_INTERVAL": "40"}}}
        config_wrapper = gu_common.ConfigWrapper()
        config_wrapper.validate_field_operation(old_config, target_config)
        
    def test_validate_field_operation_illegal__pfcwd(self):
        old_config = {"PFC_WD": {"GLOBAL": {"POLL_INTERVAL": "60"}}}
        target_config = {"PFC_WD": {"GLOBAL": {}}}
        config_wrapper = gu_common.ConfigWrapper()
        self.assertRaises(gu_common.IllegalPatchOperationError, config_wrapper.validate_field_operation, old_config, target_config)
    
    def test_validate_field_operation_legal__rm_loopback1(self):
        old_config = {
            "LOOPBACK_INTERFACE": {
                "Loopback0": {},
                "Loopback0|10.1.0.32/32": {},
                "Loopback1": {},
                "Loopback1|10.1.0.33/32": {}
            }
        }
        target_config = {
            "LOOPBACK_INTERFACE": {
                "Loopback0": {},
                "Loopback0|10.1.0.32/32": {}
            }
        }
        config_wrapper = gu_common.ConfigWrapper()
        config_wrapper.validate_field_operation(old_config, target_config)
        
    def test_validate_field_operation_illegal__rm_loopback0(self):
        old_config = {
            "LOOPBACK_INTERFACE": {
                "Loopback0": {},
                "Loopback0|10.1.0.32/32": {},
                "Loopback1": {},
                "Loopback1|10.1.0.33/32": {}
            }
        }
        target_config = {
            "LOOPBACK_INTERFACE": {
                "Loopback1": {},
                "Loopback1|10.1.0.33/32": {}
            }
        }
        config_wrapper = gu_common.ConfigWrapper()
        self.assertRaises(gu_common.IllegalPatchOperationError, config_wrapper.validate_field_operation, old_config, target_config)

class TestGetAsicName(unittest.TestCase):

    @patch('sonic_py_common.device_info.get_hwsku')
    @patch('sonic_py_common.device_info.get_sonic_version_info')
    @patch('subprocess.Popen')
    def test_get_asic_spc1(self, mock_popen, mock_get_sonic_version_info, mock_get_hwsku):
        mock_get_hwsku.return_value = 'ACS-MSN2700'
        mock_get_sonic_version_info.return_value = {'asic_type': ''}
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.stdout.readlines.return_value = ""
        mock_popen.return_value.returncode = 0
        self.assertEqual(fov.get_asic_name(), "spc1")
    
    @patch('sonic_py_common.device_info.get_hwsku')
    @patch('sonic_py_common.device_info.get_sonic_version_info')
    @patch('subprocess.Popen')
    def test_get_asic_th(self, mock_popen, mock_get_sonic_version_info, mock_get_hwsku):
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.stdout.readlines.return_value = "Broadcom Limited Device b960"
        mock_popen.return_value.returncode = 0
        self.assertEqual(fov.get_asic_name(), "th")
    
    @patch('sonic_py_common.device_info.get_hwsku')
    @patch('sonic_py_common.device_info.get_sonic_version_info')
    @patch('subprocess.Popen')
    def test_get_asic_th2(self, mock_popen, mock_get_sonic_version_info, mock_get_hwsku):
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.stdout.readlines.return_value = "Broadcom Limited Device b971"
        mock_popen.return_value.returncode = 0
        self.assertEqual(fov.get_asic_name(), "th2")
    
    @patch('sonic_py_common.device_info.get_hwsku')
    @patch('sonic_py_common.device_info.get_sonic_version_info')
    @patch('subprocess.Popen')
    def test_get_asic_td2(self, mock_popen, mock_get_sonic_version_info, mock_get_hwsku):
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.stdout.readlines.return_value = "Broadcom Limited Device b850"
        mock_popen.return_value.returncode = 0
        self.assertEqual(fov.get_asic_name(), "td2")
    
    @patch('sonic_py_common.device_info.get_hwsku')
    @patch('sonic_py_common.device_info.get_sonic_version_info')
    @patch('subprocess.Popen')
    def test_get_asic_td3(self, mock_popen, mock_get_sonic_version_info, mock_get_hwsku):
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.stdout.readlines.return_value = "Broadcom Limited Device b870"
        mock_popen.return_value.returncode = 0
        self.assertEqual(fov.get_asic_name(), "td3")
    
    @patch('sonic_py_common.device_info.get_hwsku')
    @patch('sonic_py_common.device_info.get_sonic_version_info')
    @patch('subprocess.Popen')
    def test_get_asic_cisco(self, mock_popen, mock_get_sonic_version_info, mock_get_hwsku):
        mock_get_sonic_version_info.return_value = {'asic_type': 'cisco-8000'}
        mock_popen.return_value = mock.Mock()
        mock_popen.return_value.stdout.readlines.return_value = ""
        mock_popen.return_value.returncode = 0
        self.assertEqual(fov.get_asic_name(), "cisco-8000")
