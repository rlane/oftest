# Distributed under the OpenFlow Software License (see LICENSE)
# Copyright (c) 2010 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
"""
Test flow installation into every table
"""

import logging

from oftest import config
import oftest.base_tests as base_tests
import ofp

from oftest.testutils import *

class AddMissFlows(base_tests.SimpleProtocol):
    """
    Insert a table-miss flow into every table

    Verifies the flows were installed with table stats and flow stats.
    """
    def runTest(self):
        delete_all_flows(self.controller)

        table_stats = get_stats(self, ofp.message.table_stats_request())
        for entry in table_stats:
            self.assertEquals(entry.active_count, 0);
            request = ofp.message.flow_add(
                table_id=entry.table_id,
                cookie=entry.table_id,
                buffer_id=ofp.OFP_NO_BUFFER)

            logging.info("Inserting flow into table %d", entry.table_id)
            self.controller.message_send(request)

        do_barrier(self.controller)

        table_stats = get_stats(self, ofp.message.table_stats_request())
        flow_stats = get_stats(self,
            ofp.message.flow_stats_request(
                table_id=ofp.OFPTT_ALL,
                out_port=ofp.OFPP_ANY,
                out_group=ofp.OFPG_ANY))

        self.assertEquals(len(table_stats), len(flow_stats))

        for entry in flow_stats:
            self.assertEquals(entry.table_id, entry.cookie)
            self.assertTrue([x for x in table_stats if x.table_id == entry.table_id],
                            "Missing corresponding entry in table stats")

        for entry in table_stats:
            self.assertEquals(entry.active_count, 1);
            self.assertTrue([x for x in flow_stats if x.table_id == entry.table_id],
                            "Missing corresponding entry in flow stats")
