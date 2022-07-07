import os
from unittest.mock import Mock, patch

# Import test module
import sonic_installer.bootloader.grub as grub


@patch("sonic_installer.bootloader.grub.subprocess.call", Mock())
@patch("sonic_installer.bootloader.grub.open")
@patch("sonic_installer.bootloader.grub.run_command")
@patch("sonic_installer.bootloader.grub.re.search")
def test_remove_image(open_patch, run_command_patch, re_search_patch):
    # Constants
    image_path_prefix = os.path.join(grub.HOST_PATH, grub.IMAGE_DIR_PREFIX)
    exp_image_path = f'{image_path_prefix}expeliarmus-{grub.IMAGE_PREFIX}abcde'
    image = f'{grub.IMAGE_PREFIX}expeliarmus-{grub.IMAGE_PREFIX}abcde'

    bootloader = grub.GrubBootloader()

    # Verify rm command was executed with image path
    bootloader.remove_image(image)
    args_list = grub.subprocess.call.call_args_list
    assert len(args_list) > 0

    args, _ = args_list[0]
    assert exp_image_path in args[0]

def test_set_fips_uboot():
    cmdline = ""
    def mock_get_linux_cmdline(image):
        return cmdline

    def mock_set_linux_cmdline(image, cmd):
        nonlocal cmdline
        cmdline = cmd

    image = 'test-image'
    bootloader = grub.GrubBootloader()

    bootloader.get_linux_cmdline = mock_get_linux_cmdline
    bootloader.set_linux_cmdline = mock_set_linux_cmdline

    # The the default setting
    assert not bootloader.get_fips(image)

    # Test fips enabled
    bootloader.set_fips(image, True)
    assert bootloader.get_fips(image)

    # Test fips disabled
    bootloader.set_fips(image, False)
    assert not bootloader.get_fips(image)
