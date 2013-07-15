import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp
import loxi.of13 as of13
import oftest.parse

from oftest.testutils import *

@nonstandard
class OutputExact(base_tests.SimpleDataPlane):
    """
    Test output function for an exact-match flow

    For each port A, adds a flow directing matching packets to that port.
    Then, for all other ports B, verifies that sending a matching packet
    to B results in an output to A.
    """
    def runTest(self):
        ports = sorted(config["port_map"].keys())

        delete_all_flows(self.controller)

        parsed_pkt = simple_tcp_packet()
        pkt = str(parsed_pkt)
        match = oftest.parse.packet_to_flow_match_v4(parsed_pkt)

        for out_port in ports:
            request = of13.message.flow_add(
                    table_id=0,
                    cookie=42,
                    match=match,
                    instructions=[
                        of13.instruction.apply_actions(
                            actions=[
                                of13.action.output(
                                    port=out_port,
                                    max_len=of13.OFPCML_NO_BUFFER)])],
                    buffer_id=0xffffffff,
                    priority=1000)

            logging.info("Inserting flow sending matching packets to port %d", out_port)
            logging.info(request.show())
            logging.info(repr(request.instructions[0].pack()))
            logging.info(len(request.instructions[0].pack()))
            self.controller.message_send(request)
            do_barrier(self.controller)

            for in_port in ports:
                if in_port == out_port:
                    continue
                logging.info("OutputExact test, ports %d to %d", in_port, out_port)
                self.dataplane.send(in_port, pkt)
                receive_pkt_verify(self, [out_port], pkt, in_port)

@nonstandard
class FlowStats(base_tests.SimpleProtocol):
    """
    Flow stats multipart transaction

    Only verifies we get a reply.
    """
    def runTest(self):
        delete_all_flows(self.controller)

        parsed_pkt = simple_tcp_packet()
        pkt = str(parsed_pkt)
        match = oftest.parse.packet_to_flow_match_v4(parsed_pkt)

        request = of13.message.flow_add(
                table_id=0,
                cookie=42,
                match=match,
                instructions=[
                    of13.instruction.apply_actions(
                        actions=[
                            of13.action.output(
                                port=1,
                                max_len=of13.OFPCML_NO_BUFFER)])],
                buffer_id=0xffffffff,
                priority=1000)

        logging.info("Inserting flow")
        logging.info(request.show())
        self.controller.message_send(request)
        do_barrier(self.controller)

        req = of13.message.flow_stats_request(match=of13.match(),
                                              table_id=of13.OFPTT_ALL,
                                              out_port=of13.OFPP_ANY,
                                              out_group=of13.OFPG_ANY)

        logging.info("Sending flow stats request")
        stats = get_stats(self, req)
        logging.info("Received %d flow stats entries", len(stats))
        for entry in stats:
            logging.info(entry.show())

        self.assertEquals(len(stats), 1)
        stat = stats[0]
        self.assertEquals(stat.match, match)
        self.assertEquals(stat.instructions, request.instructions)
