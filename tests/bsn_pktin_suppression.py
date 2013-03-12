"""
Tests for the BSN packet-in suppression extension.
"""
import time
import logging
from oftest import config
import ofp
import oftest.base_tests as base_tests
from oftest.testutils import *

class BaseTest(base_tests.SimpleDataPlane):
    def setUp(self):
        super(BaseTest, self).setUp()
        m = ofp.message.bsn_set_pktin_suppression(
            enabled=1,
            priority=0,
            cookie=0xffffffffffffffff,
            idle_timeout=0,
            hard_timeout=5)
        self.controller.message_send(m)

    def tearDown(self):
        m = ofp.message.bsn_set_pktin_suppression(enabled=0)
        self.controller.message_send(m)
        super(BaseTest, self).tearDown()

@nonstandard
class Suppression(BaseTest):
    """
    Basic packet-in suppression test.

    When the switch sends a packet-in to the controller it also installs an exact
    match flow with low priority that drops further packets.
    """
    def runTest(self):
        self.assertTrue(len(config["port_map"]) > 1, "Too few ports for test")
        in_port = config["port_map"].keys()[0]
        negative_timeout = 0.1

        delete_all_flows(self.controller)
        do_barrier(self.controller)

        # Test with a variety of similar packets to ensure that their
        # suppression flows don't interfere with each other.
        pkts = [
            str(simple_tcp_packet(tcp_sport=1)),
            str(simple_tcp_packet(tcp_sport=2)),
            str(simple_udp_packet(udp_sport=1)),
            str(simple_udp_packet(udp_sport=2)),
            str(simple_icmp_packet(icmp_type=1)),
            str(simple_icmp_packet(icmp_type=2)),
            str(simple_tcp_packet(ip_src="192.168.1.1")),
            str(simple_tcp_packet(ip_src="192.168.1.2")),
            str(simple_tcp_packet(eth_src="00:01:02:03:04:05")),
            str(simple_tcp_packet(eth_src="00:01:02:03:04:06")),
            str(simple_tcp_packet(dl_vlan_enable=True, vlan_vid=1)),
            str(simple_tcp_packet(dl_vlan_enable=True, vlan_vid=2)),
            str(simple_tcp_packet(dl_vlan_enable=True, vlan_pcp=1)),
            str(simple_tcp_packet(dl_vlan_enable=True, vlan_pcp=2)),
            str(simple_tcp_packet(ip_tos=1 << 2)),
            str(simple_tcp_packet(ip_tos=2 << 2)),
        ]

        for pkt in pkts:
            # The first packet should be sent as a packet-in
            self.dataplane.send(in_port, pkt)
            pktin1, _ = self.controller.poll(ofp.OFPT_PACKET_IN)
            self.assertTrue(pktin1 is not None, "First packet-in not received for pkt %d" % pkts.index(pkt))
            self.assertEqual(pktin1.data, pkt, "Packet data mismatch")

            # The second packet should be dropped
            self.dataplane.send(in_port, pkt)
            pktin2, _ = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=negative_timeout)
            self.assertTrue(pktin2 is None, "Second packet-in received for pkt %d" % pkts.index(pkt))

        # Deleting all flows should remove the suppression drop flows
        delete_all_flows(self.controller)
        do_barrier(self.controller)

        for pkt in pkts:
            # The first packet should be sent as a packet-in
            self.dataplane.send(in_port, pkt)
            pktin1, _ = self.controller.poll(ofp.OFPT_PACKET_IN)
            self.assertTrue(pktin1 is not None, "First packet-in not received for pkt %d" % pkts.index(pkt))
            self.assertEqual(pktin1.data, pkt, "Packet data mismatch")

            # The second packet should be dropped
            self.dataplane.send(in_port, pkt)
            pktin2, _ = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=negative_timeout)
            self.assertTrue(pktin2 is None, "Second packet-in received for pkt %d" % pkts.index(pkt))

@nonstandard
class NoControllerPortSuppression(BaseTest):
    """
    Output actions to OFPP_CONTROLLER do not go through suppression.
    """
    def runTest(self):
        self.assertTrue(len(config["port_map"]) > 1, "Too few ports for test")
        in_port = config["port_map"].keys()[0]

        delete_all_flows(self.controller)
        do_barrier(self.controller)

        pkt = str(simple_tcp_packet())

        # Install a flow to send matching packets to the controller
        flow_mod = flow_msg_create(self, pkt, ing_port=in_port,
            action_list=[ofp.action.output(port=ofp.OFPP_CONTROLLER)])
        self.controller.message_send(flow_mod)
        do_barrier(self.controller)

        # The first packet should be sent as a packet-in
        self.dataplane.send(in_port, pkt)
        pktin1, _ = self.controller.poll(ofp.OFPT_PACKET_IN)
        self.assertTrue(pktin1 is not None, "First packet-in not received")
        self.assertEqual(pktin1.data, pkt, "Packet data mismatch")

        # The second packet should be sent as a packet-in
        self.dataplane.send(in_port, pkt)
        pktin2, _ = self.controller.poll(ofp.OFPT_PACKET_IN)
        self.assertTrue(pktin2 is not None, "Second packet-in not received")
        self.assertEqual(pktin2.data, pkt, "Packet data mismatch")

@nonstandard
class SuppressionTimeout(BaseTest):
    """
    The flows installed by suppression have a hard timeout of 5 seconds.
    """
    def runTest(self):
        self.assertTrue(len(config["port_map"]) > 1, "Too few ports for test")
        in_port = config["port_map"].keys()[0]

        delete_all_flows(self.controller)
        do_barrier(self.controller)

        pkt = str(simple_tcp_packet())

        # The first packet should be sent as a packet-in
        self.dataplane.send(in_port, pkt)
        pktin, _ = self.controller.poll(ofp.OFPT_PACKET_IN)
        self.assertTrue(pktin is not None, "First packet-in not received")
        self.assertEqual(pktin.data, pkt, "Packet data mismatch")

        # Wait until suppression times out
        for i in range(1,100):
            time.sleep(0.1)
            self.dataplane.send(in_port, pkt)
            pktin, _ = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=0)
            if pktin:
                self.assertEqual(pktin.data, pkt, "Packet data mismatch")
                break

        logging.info("suppression timed out after %f seconds", i/10.0)
        self.assertTrue(20 <= i <= 80, "Expected suppression timeout between 2.0 and 8.0 seconds")

@nonstandard
class SuppressionFlow(BaseTest):
    """
    The flows installed by suppression should have certain values for priority, cookie, etc.
    """
    def runTest(self):
        self.assertTrue(len(config["port_map"]) > 1, "Too few ports for test")
        in_port = config["port_map"].keys()[0]

        delete_all_flows(self.controller)
        do_barrier(self.controller)

        pkt = str(simple_tcp_packet())

        # The first packet should be sent as a packet-in
        self.dataplane.send(in_port, pkt)
        pktin, _ = self.controller.poll(ofp.OFPT_PACKET_IN)
        self.assertTrue(pktin is not None, "First packet-in not received")
        self.assertEqual(pktin.data, pkt, "Packet data mismatch")

        stats = get_flow_stats(self, packet_to_flow_match(self, pkt))
        self.assertEqual(len(stats), 1, "Expected exactly 1 flow stats entry")
        self.assertEqual(stats[0].cookie, 0xffffffffffffffff, "Wrong cookie")
        self.assertEqual(stats[0].priority, 0, "Wrong priority")
        self.assertEqual(stats[0].idle_timeout, 0, "Wrong idle_timeout")
        self.assertEqual(stats[0].hard_timeout, 5, "Wrong hard_timeout")

@nonstandard
@disabled
class SuppressionBurst(BaseTest):
    """
    A burst of identical packets should still result in a single packet-in.
    """
    def runTest(self):
        self.assertTrue(len(config["port_map"]) > 1, "Too few ports for test")
        in_port = config["port_map"].keys()[0]

        delete_all_flows(self.controller)
        do_barrier(self.controller)

        N = 10
        pkts = [str(simple_tcp_packet(tcp_sport=i)) for i in range(0, 10)]

        i = 0
        failed = False
        for pkt in pkts:
            for j in range(0, N):
                self.dataplane.send(in_port, pkt)

            count = 0
            while True:
                pktin, _ = self.controller.poll(ofp.OFPT_PACKET_IN, timeout=0.1)
                if pktin and pktin.data == pkt:
                    count += 1
                else:
                    break

            logging.info("Iteration %d: received %d out of %d pkt-ins (expected 1)", i, count, N)
            if count != 1:
                failed = True
            i += 1

        self.assertTrue(not failed, "Did not receive the expected number of packet-ins")
