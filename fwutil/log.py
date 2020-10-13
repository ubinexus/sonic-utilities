#
# log.py
#
# Logging library for command-line interface for interacting with platform components within SONiC
#

try:
    import click
    from sonic_py_common import logger
except ImportError as e:
    raise ImportError("Required module not found: {}".format(str(e)))

# ========================= Constants ==========================================

SYSLOG_IDENTIFIER = "fwutil"

# ========================= Variables ==========================================

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)
log.set_min_log_priority_info()

# ========================= Helper classes =====================================

class LogHelper(object):
    """
    LogHelper
    """
    FW_ACTION_DOWNLOAD = "download"
    FW_ACTION_INSTALL = "install"
    FW_ACTION_UPDATE = "update"
    FW_ACTION_AUTO_UPDATE = "auto-update"

    STATUS_SUCCESS = "success"
    STATUS_FAILURE = "failure"

    def __log_fw_action_start(self, action, component, firmware, boot=None):
        caption = "Firmware {} started".format(action)
        template = "{}: component={}, firmware={}"

        log.log_info(
            template.format(
                caption,
                component,
                firmware
            )
        )

    def __log_fw_action_end(self, action, component, firmware, status, exception=None, boot=None):
        caption = "Firmware {} ended".format(action)

        status_template = "{}: component={}, firmware={}, status={}"
        status_boot_template = "{}: component={}, firmware={}, boot={}, status={}"
        exception_template = "{}: component={}, firmware={}, status={}, exception={}"
        exception_boot_template = "{}: component={}, firmware={}, boot={}, status={}, exception={}"

        if status:
            if boot is None:
                log.log_info(
                    status_template.format(
                        caption,
                        component,
                        firmware,
                        self.STATUS_SUCCESS
                    )
                )
            else:
                log.log_info(
                    status_boot_template.format(
                        caption,
                        component,
                        firmware,
                        boot,
                        self.STATUS_SUCCESS
                    )
                )
        else:
            if exception:
                if boot is None:
                    log.log_error(
                        status_template.format(
                            caption,
                            component,
                            firmware,
                            self.STATUS_FAILURE
                        )
                    )
                else:
                    log.log_info(
                        status_boot_template.format(
                            caption,
                            component,
                            firmware,
                            boot,
                            self.STATUS_FAILURE
                        )
                    )
            else:
                if boot is None:
                    log.log_error(
                        status_template.format(
                            caption,
                            component,
                            firmware,
                            self.STATUS_FAILURE,
                            str(exception)
                        )
                    )
                else:
                    log.log_error(
                        exception_boot_template.format(
                            caption,
                            component,
                            firmware,
                            boot,
                            self.STATUS_FAILURE,
                            str(exception)
                        )
                    )

    def log_fw_download_start(self, component, firmware):
        self.__log_fw_action_start(self.FW_ACTION_DOWNLOAD, component, firmware)

    def log_fw_download_end(self, component, firmware, status, exception=None):
        self.__log_fw_action_end(self.FW_ACTION_DOWNLOAD, component, firmware, status, exception)

    def log_fw_install_start(self, component, firmware):
        self.__log_fw_action_start(self.FW_ACTION_INSTALL, component, firmware)

    def log_fw_install_end(self, component, firmware, status, exception=None):
        self.__log_fw_action_end(self.FW_ACTION_INSTALL, component, firmware, status, exception)

    def log_fw_update_start(self, component, firmware):
        self.__log_fw_action_start(self.FW_ACTION_UPDATE, component, firmware)

    def log_fw_update_end(self, component, firmware, status, exception=None):
        self.__log_fw_action_end(self.FW_ACTION_UPDATE, component, firmware, status, exception)

    def log_fw_auto_update_start(self, component, firmware, boot):
        self.__log_fw_action_start(self.FW_ACTION_AUTO_UPDATE, component, firmware, boot)

    def log_fw_auto_update_end(self, component, firmware, status, exception=None, boot=None):
        self.__log_fw_action_end(self.FW_ACTION_AUTO_UPDATE, component, firmware, status, exception, boot)

    def print_error(self, msg):
        click.echo("Error: {}.".format(msg))

    def print_warning(self, msg):
        click.echo("Warning: {}.".format(msg))

    def print_info(self, msg):
        click.echo("Info: {}.".format(msg))
