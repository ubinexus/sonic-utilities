import imp
import os
import mock_tables.dbconnector
import mock_tables.mock_multi_asic_for_int_monitor
import internal_links_monitor as int_monitor

class TestPacketChassisInternalLinkMontoring(object):
    @classmethod
    def setup_class(cls):
        imp.reload(mock_tables.mock_multi_asic_for_int_monitor)
        mock_tables.dbconnector.load_namespace_config()        
        os.environ['UTILITIES_UNIT_TESTING'] = "2"

    @classmethod
    def teardown_class(cls):        
        os.environ['UTILITIES_UNIT_TESTING'] = "0"

    def test_get_port_status(self):
        port_name = 'Ethernet-BP204'
        namespace = 'asic3'
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_port_status(namespace, port_name) == 'up'

    def test_isolate_lag_member(self):        
        port_name = 'Ethernet-BP196'
        namespace = 'asic3'
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_port_status(namespace, port_name) == 'up'
        link_monitor.isolate_lag_member(namespace, port_name)
        assert link_monitor.get_port_status(namespace, port_name) == 'down'

    def test_get_lag_name_for_port(self):        
        port_name = 'Ethernet-BP196'
        namespace = 'asic3'
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_lag_name_for_port(namespace, port_name) == 'PortChannel4001'

    def test_get_active_lag_member_count(self):        
        lag_name = 'PortChannel4001'
        namespace = 'asic3'
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_active_lag_member_count(namespace, lag_name) == 4

    def test_mem_down_get_active_lag_member_count(self):        
        lag_name = 'PortChannel4001'
        namespace = 'asic3'
        port_name = 'Ethernet-BP196'
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        link_monitor.isolate_lag_member(namespace, port_name)        
        assert link_monitor.get_active_lag_member_count(namespace, lag_name) == 3

    def test_get_min_links_for_lag(self):        
        lag_name = 'PortChannel4001'
        namespace = 'asic3'
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        assert link_monitor.get_min_links_for_lag(namespace, lag_name) == 3

    def test_attempt_to_mitigate_ports(self):        
        port_list = ['Ethernet-BP192', 'Ethernet-BP196']
        namespace = 'asic3'
        lag_name = 'PortChannel4001'
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        link_monitor.attempt_to_mitigate_ports(namespace, port_list)

        # Only one port should be brought down due to min_links check
        assert link_monitor.get_active_lag_member_count(namespace, lag_name) == 3

    def test_monitor(self):
        link_monitor = int_monitor.PacketChassisInternalLinkMontoring()
        link_monitor.monitor()

        # Validation on asic3
        assert link_monitor.get_port_status('asic3', 'Ethernet-BP192') == 'up'
        assert link_monitor.get_port_status('asic3', 'Ethernet-BP196') == 'up'
        assert link_monitor.get_port_status('asic3', 'Ethernet-BP200') == 'down'
        # Action should be skipped due to min_links check
        assert link_monitor.get_port_status('asic3', 'Ethernet-BP204') == 'up'

        # Validation on asic4
        assert link_monitor.get_port_status('asic4', 'Ethernet-BP256') == 'down'
        assert link_monitor.get_port_status('asic4', 'Ethernet-BP260') == 'up'
        # Action should be skipped due to min_links check
        assert link_monitor.get_port_status('asic4', 'Ethernet-BP264') == 'up'