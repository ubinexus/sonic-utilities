import sys
import pytest
from unittest import mock
from utilities_common.util_base import UtilHelper
from utilities_common.module_base import ModuleHelper, INVALID_MODULE_INDEX

sys.modules['sonic_platform'] = mock.MagicMock()

util = UtilHelper()
module_helper = ModuleHelper()


class TestModuleHelper:
    @pytest.fixture
    def mock_load_platform_chassis(self):
        with mock.patch('utilities_common.module_base.util.load_platform_chassis') as mock_load_platform_chassis:
            yield mock_load_platform_chassis

    @pytest.fixture
    def mock_try_get(self):
        with mock.patch('utilities_common.module_base.util.try_get') as mock_try_get:
            yield mock_try_get

    def test_reboot_module_success(self, mock_load_platform_chassis, mock_try_get):
        mock_try_get.return_value = True
        mock_load_platform_chassis.return_value.get_module_index.return_value = 1
        mock_load_platform_chassis.return_value.get_module.return_value.reboot.return_value = True

        result = module_helper.reboot_module("DPU1", "cold")
        assert result is True

    def test_reboot_module_invalid_index(self, mock_load_platform_chassis, mock_try_get):
        mock_try_get.return_value = INVALID_MODULE_INDEX
        mock_load_platform_chassis.return_value.get_module_index.return_value = INVALID_MODULE_INDEX

        result = module_helper.reboot_module("DPU1", "cold")
        assert result is False

    def test_pci_detach_module_success(self, mock_load_platform_chassis, mock_try_get):
        mock_try_get.return_value = True
        mock_load_platform_chassis.return_value.get_module_index.return_value = 1
        mock_load_platform_chassis.return_value.get_module.return_value.pci_detach.return_value = True

        result = module_helper.pci_detach_module("DPU1")
        assert result is True

    def test_pci_detach_module_invalid_index(self, mock_load_platform_chassis, mock_try_get):
        mock_try_get.return_value = INVALID_MODULE_INDEX
        mock_load_platform_chassis.return_value.get_module_index.return_value = INVALID_MODULE_INDEX

        result = module_helper.pci_detach_module("DPU1")
        assert result is False

    def test_pci_reattach_module_success(self, mock_load_platform_chassis, mock_try_get):
        mock_try_get.return_value = True
        mock_load_platform_chassis.return_value.get_module_index.return_value = 1
        mock_load_platform_chassis.return_value.get_module.return_value.pci_reattach.return_value = True

        result = module_helper.pci_reattach_module("DPU1")
        assert result is True

    def test_pci_reattach_module_invalid_index(self, mock_load_platform_chassis, mock_try_get):
        mock_try_get.return_value = INVALID_MODULE_INDEX
        mock_load_platform_chassis.return_value.get_module_index.return_value = INVALID_MODULE_INDEX

        result = module_helper.pci_reattach_module("DPU1")
        assert result is False
