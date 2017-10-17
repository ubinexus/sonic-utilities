#!/usr/bin/env python
#
# psu_base.py
#
# Abstract base class for implementing platform-specific
#  PSU control functionality for SONiC
#

try:
    import abc
except ImportError, e:
    raise ImportError (str(e) + " - required module not found")

class PsuBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_num_psus(self):
        """
        Retrieves the number of PSUs available on the device

        :return: An integer, the number of PSUs available on the device
        """
        return 0

    @abc.abstractmethod
    def get_psu_status(self, index):
        """
        Retrieves the operational status of power supply unit (PSU) defined
                by index <index>

        :param index: An integer, index of the PSU of which to query status
        :return: Boolean, True if PSU is operating properly, False if PSU is faulty
        """
        return False

    @abc.abstractmethod
    def get_psu_presence(self, index):
        """
        Retrieves the presence status of power supply unit (PSU) defined
                by index <index>

        :param index: An integer, index of the PSU of which to query status
        :return: Boolean, True if PSU is plugged, False if not
        """
        return False

