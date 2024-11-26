# tests/test_reboot_helper.py
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

sys.modules['sonic_platform'] = MagicMock()

sys.path.append("scripts")
import reboot_helper  # noqa: E402


class TestRebootHelper(object):
    @pytest.fixture(scope='class')
    def mock_load_platform_chassis(self):
        with patch('reboot_helper.load_platform_chassis', return_value=True) as mock:
            yield mock

    @pytest.fixture(scope='class')
    def mock_load_and_verify(self):
        with patch('reboot_helper.load_and_verify', return_value=True) as mock:
            yield mock

    @pytest.fixture(scope='class')
    def mock_is_smartswitch(self):
        with patch('reboot_helper.is_smartswitch', return_value=True) as mock:
            yield mock

    @pytest.fixture(scope='class')
    def mock_open_file(self):
        return mock_open()

    @pytest.fixture(scope='class')
    def mock_platform_chassis(self):
        with patch('reboot_helper.platform_chassis') as mock:
            yield mock

    @pytest.fixture(scope='class')
    def mock_platform(self):
        with patch('reboot_helper.sonic_platform.platform.Platform') as mock:
            yield mock

    @pytest.fixture(scope='class')
    def mock_get_dpu_list(self):
        with patch('reboot_helper.get_dpu_list', return_value=["dpu1"]) as mock:
            yield mock

    def test_load_platform_chassis_success(self, mock_platform_chassis):
        mock_platform_chassis.get_chassis.return_value = MagicMock()
        result = reboot_helper.load_platform_chassis()
        assert result

    def test_load_platform_chassis_exception(self, mock_platform):
        mock_platform.side_effect = RuntimeError
        result = reboot_helper.load_platform_chassis()
        assert not result

    def test_load_platform_chassis_none(self, mock_platform_chassis):
        mock_platform_chassis.get_chassis.return_value = None
        result = reboot_helper.load_platform_chassis()
        assert not result

    def test_load_and_verify_chassis_fail(self, mock_load_platform_chassis):
        mock_load_platform_chassis.return_value = False
        assert not reboot_helper.load_and_verify("DPU1")

    def test_load_and_verify_not_smartswitch(self, mock_is_smartswitch, mock_load_platform_chassis):
        mock_is_smartswitch.return_value = False
        mock_load_platform_chassis.return_value = True
        assert not reboot_helper.load_and_verify("DPU1")

    def test_load_and_verify_not_found(self, mock_is_smartswitch, mock_load_platform_chassis, mock_get_dpu_list):
        mock_is_smartswitch.return_value = True
        mock_load_platform_chassis.return_value = True
        mock_get_dpu_list.return_value = ["dpu1"]

        assert not reboot_helper.load_and_verify("DPU2")

    def test_load_and_verify_empty_dpu_list(self, mock_is_smartswitch, mock_load_platform_chassis, mock_get_dpu_list):
        mock_is_smartswitch.return_value = True
        mock_load_platform_chassis.return_value = True
        mock_get_dpu_list.return_value = []

        assert not reboot_helper.load_and_verify("DPU1")

    def test_load_and_verify_success(self, mock_is_smartswitch, mock_load_platform_chassis, mock_get_dpu_list):
        mock_is_smartswitch.return_value = True
        mock_load_platform_chassis.return_value = True
        mock_get_dpu_list.return_value = ["dpu1"]

        result = reboot_helper.load_and_verify("DPU1")
        assert result

    def test_reboot_dpu_load_and_verify_fail(self, mock_load_and_verify):
        mock_load_and_verify.return_value = False
        result = reboot_helper.reboot_dpu("DPU1", "DPU")
        assert not result

    def test_reboot_dpu_success(self, mock_load_and_verify, mock_platform_chassis):
        mock_load_and_verify.return_value = True
        mock_platform_chassis.reboot.return_value = True
        assert reboot_helper.reboot_dpu("DPU1", "DPU")

    def test_reboot_dpu_no_reboot_method(self, mock_load_and_verify, mock_platform_chassis):
        mock_load_and_verify.return_value = True
        with patch('reboot_helper.hasattr', return_value=False):
            assert not reboot_helper.reboot_dpu("DPU1", "DPU")

    def test_pci_detach_module_load_and_verify_fail(self, mock_load_and_verify):
        mock_load_and_verify.return_value = False
        assert not reboot_helper.pci_detach_module("DPU1")

    def test_pci_detach_module_success(self, mock_load_and_verify, mock_platform_chassis):
        mock_load_and_verify.return_value = True
        mock_platform_chassis.pci_detach.return_value = True
        assert reboot_helper.pci_detach_module("DPU1")

    def test_pci_detach_module_no_detach_method(self, mock_load_and_verify, mock_platform_chassis):
        mock_load_and_verify.return_value = True
        with patch('reboot_helper.hasattr', return_value=False):
            assert not reboot_helper.pci_detach_module("DPU1")

    def test_pci_reattach_module_load_and_verify_fail(self, mock_load_and_verify):
        mock_load_and_verify.return_value = False
        assert not reboot_helper.pci_reattach_module("DPU1")

    def test_pci_reattach_module_success(self, mock_load_and_verify, mock_platform_chassis):
        mock_load_and_verify.return_value = True
        mock_platform_chassis.pci_reattach.return_value = True
        assert reboot_helper.pci_reattach_module("DPU1")

    def test_pci_reattach_module_no_reattach_method(self, mock_load_and_verify, mock_platform_chassis):
        mock_load_and_verify.return_value = True
        with patch('reboot_helper.hasattr', return_value=False):
            assert not reboot_helper.pci_reattach_module("DPU1")
