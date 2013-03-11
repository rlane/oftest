"""
OpenFlow message parsing functions
"""

import sys
import logging
import message
import error
import action
import cstruct
from action_list import action_list
try:
    import scapy.all as scapy
except:
    try:
        import scapy as scapy
    except:
        sys.exit("Need to install scapy for packet parsing")

"""
of_message.py
Contains wrapper functions and classes for the of_message namespace
that are generated by hand.  It includes the rest of the wrapper
function information into the of_message namespace
"""

parse_logger = logging.getLogger("parse")
#parse_logger.setLevel(logging.DEBUG)

# These message types are subclassed
msg_type_subclassed = [
    cstruct.OFPT_STATS_REQUEST,
    cstruct.OFPT_STATS_REPLY,
    cstruct.OFPT_ERROR
]

# Maps from sub-types to classes
stats_reply_to_class_map = {
    cstruct.OFPST_DESC                      : message.desc_stats_reply,
    cstruct.OFPST_AGGREGATE                 : message.aggregate_stats_reply,
    cstruct.OFPST_FLOW                      : message.flow_stats_reply,
    cstruct.OFPST_TABLE                     : message.table_stats_reply,
    cstruct.OFPST_PORT                      : message.port_stats_reply,
    cstruct.OFPST_QUEUE                     : message.queue_stats_reply
}

stats_request_to_class_map = {
    cstruct.OFPST_DESC                      : message.desc_stats_request,
    cstruct.OFPST_AGGREGATE                 : message.aggregate_stats_request,
    cstruct.OFPST_FLOW                      : message.flow_stats_request,
    cstruct.OFPST_TABLE                     : message.table_stats_request,
    cstruct.OFPST_PORT                      : message.port_stats_request,
    cstruct.OFPST_QUEUE                     : message.queue_stats_request
}

error_to_class_map = {
    cstruct.OFPET_HELLO_FAILED              : message.hello_failed_error_msg,
    cstruct.OFPET_BAD_REQUEST               : message.bad_request_error_msg,
    cstruct.OFPET_BAD_ACTION                : message.bad_action_error_msg,
    cstruct.OFPET_FLOW_MOD_FAILED           : message.flow_mod_failed_error_msg,
    cstruct.OFPET_PORT_MOD_FAILED           : message.port_mod_failed_error_msg,
    cstruct.OFPET_QUEUE_OP_FAILED           : message.queue_op_failed_error_msg
}

# Map from header type value to the underlieing message class
msg_type_to_class_map = {
    cstruct.OFPT_HELLO                      : message.hello,
    cstruct.OFPT_ERROR                      : message.error,
    cstruct.OFPT_ECHO_REQUEST               : message.echo_request,
    cstruct.OFPT_ECHO_REPLY                 : message.echo_reply,
    cstruct.OFPT_VENDOR                     : message.vendor,
    cstruct.OFPT_FEATURES_REQUEST           : message.features_request,
    cstruct.OFPT_FEATURES_REPLY             : message.features_reply,
    cstruct.OFPT_GET_CONFIG_REQUEST         : message.get_config_request,
    cstruct.OFPT_GET_CONFIG_REPLY           : message.get_config_reply,
    cstruct.OFPT_SET_CONFIG                 : message.set_config,
    cstruct.OFPT_PACKET_IN                  : message.packet_in,
    cstruct.OFPT_FLOW_REMOVED               : message.flow_removed,
    cstruct.OFPT_PORT_STATUS                : message.port_status,
    cstruct.OFPT_PACKET_OUT                 : message.packet_out,
    cstruct.OFPT_FLOW_MOD                   : message.flow_mod,
    cstruct.OFPT_PORT_MOD                   : message.port_mod,
    cstruct.OFPT_STATS_REQUEST              : message.stats_request,
    cstruct.OFPT_STATS_REPLY                : message.stats_reply,
    cstruct.OFPT_BARRIER_REQUEST            : message.barrier_request,
    cstruct.OFPT_BARRIER_REPLY              : message.barrier_reply,
    cstruct.OFPT_QUEUE_GET_CONFIG_REQUEST   : message.queue_get_config_request,
    cstruct.OFPT_QUEUE_GET_CONFIG_REPLY     : message.queue_get_config_reply
}

def _of_message_to_object(binary_string):
    """
    Map a binary string to the corresponding class.

    Appropriately resolves subclasses
    """
    hdr = message.ofp_header()
    hdr.unpack(binary_string)
    # FIXME: Add error detection
    if not hdr.type in msg_type_subclassed:
        return msg_type_to_class_map[hdr.type]()
    if hdr.type == cstruct.OFPT_STATS_REQUEST:
        sub_hdr = message.ofp_stats_request()
        sub_hdr.unpack(binary_string[cstruct.OFP_HEADER_BYTES:])
        try:
            obj = stats_request_to_class_map[sub_hdr.type]()
        except KeyError:
            obj = None
        return obj
    elif hdr.type == cstruct.OFPT_STATS_REPLY:
        sub_hdr = message.ofp_stats_reply()
        sub_hdr.unpack(binary_string[cstruct.OFP_HEADER_BYTES:])
        try:
            obj = stats_reply_to_class_map[sub_hdr.type]()
        except KeyError:
            obj = None
        return obj
    elif hdr.type == cstruct.OFPT_ERROR:
        sub_hdr = message.ofp_error_msg()
        sub_hdr.unpack(binary_string[cstruct.OFP_HEADER_BYTES:])
        return error_to_class_map[sub_hdr.type]()
    else:
        parse_logger.error("Cannot parse pkt to message")
        return None

def of_message_parse(binary_string, raw=False):
    """
    Parse an OpenFlow packet

    Parses a raw OpenFlow packet into a Python class, with class
    members fully populated.

    @param binary_string The packet (string) to be parsed
    @param raw If true, interpret the packet as an L2 packet.  Not
    yet supported.
    @return An object of some message class or None if fails
    Note that any data beyond that parsed is not returned

    """

    if raw:
        parse_logger.error("raw packet message parsing not supported")
        return None

    obj = _of_message_to_object(binary_string)
    if obj:
        obj.unpack(binary_string)
    return obj


def of_header_parse(binary_string, raw=False):
    """
    Parse only the header from an OpenFlow packet

    Parses the header from a raw OpenFlow packet into a
    an ofp_header Python class.

    @param binary_string The packet (string) to be parsed
    @param raw If true, interpret the packet as an L2 packet.  Not
    yet supported.
    @return An ofp_header object

    """

    if raw:
        parse_logger.error("raw packet message parsing not supported")
        return None

    hdr = message.ofp_header()
    hdr.unpack(binary_string)

    return hdr

map_wc_field_to_match_member = {
    'OFPFW_DL_VLAN'                 : 'vlan_vid',
    'OFPFW_DL_SRC'                  : 'eth_src',
    'OFPFW_DL_DST'                  : 'eth_dst',
    'OFPFW_DL_TYPE'                 : 'eth_type',
    'OFPFW_NW_PROTO'                : 'ip_proto',
    'OFPFW_TP_SRC'                  : 'tcp_src',
    'OFPFW_TP_DST'                  : 'tcp_dst',
    'OFPFW_NW_SRC_SHIFT'            : 'nw_src_shift',
    'OFPFW_NW_SRC_BITS'             : 'nw_src_bits',
    'OFPFW_NW_SRC_MASK'             : 'nw_src_mask',
    'OFPFW_NW_SRC_ALL'              : 'nw_src_all',
    'OFPFW_NW_DST_SHIFT'            : 'nw_dst_shift',
    'OFPFW_NW_DST_BITS'             : 'nw_dst_bits',
    'OFPFW_NW_DST_MASK'             : 'nw_dst_mask',
    'OFPFW_NW_DST_ALL'              : 'nw_dst_all',
    'OFPFW_DL_VLAN_PCP'             : 'vlan_pcp',
    'OFPFW_NW_TOS'                  : 'ip_dscp'
}


def parse_mac(mac_str):
    """
    Parse a MAC address

    Parse a MAC address ':' separated string of hex digits to an
    array of integer values.  '00:d0:05:5d:24:00' => [0, 208, 5, 93, 36, 0]
    @param mac_str The string to convert
    @return Array of 6 integer values
    """
    return map(lambda val: int(val, 16), mac_str.split(":"))

def parse_ip(ip_str):
    """
    Parse an IP address

    Parse an IP address '.' separated string of decimal digits to an
    host ordered integer.  '172.24.74.77' => 
    @param ip_str The string to convert
    @return Integer value
    """
    array = map(lambda val: int(val), ip_str.split("."))
    val = 0
    for a in array:
        val <<= 8
        val += a
    return val

def packet_type_classify(ether):
    try:
        dot1q = ether[scapy.Dot1Q]
    except:
        dot1q = None

    try:
        ip = ether[scapy.IP]
    except:
        ip = None

    try:
        tcp = ether[scapy.TCP]
    except:
        tcp = None

    try:
        udp = ether[scapy.UDP]
    except:
        udp = None

    try:
        icmp = ether[scapy.ICMP]
    except:
        icmp = None

    try:
        arp = ether[scapy.ARP]
    except:
        arp = None
    return (dot1q, ip, tcp, udp, icmp, arp)

def packet_to_flow_match(packet, pkt_format="L2"):
    """
    Create a flow match that matches packet with the given wildcards

    @param packet The packet to use as a flow template
    @param pkt_format Currently only L2 is supported.  Will indicate the 
    overall packet type for parsing
    @return An ofp_match object if successful.  None if format is not
    recognized.  The wildcards of the match will be cleared for the
    values extracted from the packet.

    @todo check min length of packet
    @todo Check if packet is other than L2 format
    @todo Implement ICMP and ARP fields
    """

    #@todo check min length of packet
    if pkt_format.upper() != "L2":
        parse_logger.error("Only L2 supported for packet_to_flow")
        return None

    if type(packet) == type(""):
        ether = scapy.Ether(packet)
    else:
        ether = packet

    # For now, assume ether IP packet and ignore wildcards
    try:
        (dot1q, ip, tcp, udp, icmp, arp) = packet_type_classify(ether)
    except:
        parse_logger.error("packet_to_flow_match: Classify error")
        return None

    match = cstruct.ofp_match()
    match.wildcards = cstruct.OFPFW_ALL
    #@todo Check if packet is other than L2 format
    match.eth_dst = parse_mac(ether.dst)
    match.wildcards &= ~cstruct.OFPFW_DL_DST
    match.eth_src = parse_mac(ether.src)
    match.wildcards &= ~cstruct.OFPFW_DL_SRC
    match.eth_type = ether.type
    match.wildcards &= ~cstruct.OFPFW_DL_TYPE

    if dot1q:
        match.vlan_vid = dot1q.vlan
        match.vlan_pcp = dot1q.prio
        match.eth_type = dot1q.type
    else:
        match.vlan_vid = cstruct.OFP_VLAN_NONE
        match.vlan_pcp = 0
    match.wildcards &= ~cstruct.OFPFW_DL_VLAN
    match.wildcards &= ~cstruct.OFPFW_DL_VLAN_PCP

    if ip:
        match.ipv4_src = parse_ip(ip.src)
        match.wildcards &= ~cstruct.OFPFW_NW_SRC_MASK
        match.ipv4_dst = parse_ip(ip.dst)
        match.wildcards &= ~cstruct.OFPFW_NW_DST_MASK
        match.ip_dscp = ip.tos
        match.wildcards &= ~cstruct.OFPFW_NW_TOS

    if tcp:
        match.ip_proto = 6
        match.wildcards &= ~cstruct.OFPFW_NW_PROTO
    elif not tcp and udp:
        tcp = udp
        match.ip_proto = 17
        match.wildcards &= ~cstruct.OFPFW_NW_PROTO

    if tcp:
        match.tcp_src = tcp.sport
        match.wildcards &= ~cstruct.OFPFW_TP_SRC
        match.tcp_dst = tcp.dport
        match.wildcards &= ~cstruct.OFPFW_TP_DST

    if icmp:
        match.ip_proto = 1
        match.tcp_src = icmp.type
        match.tcp_dst = icmp.code
        match.wildcards &= ~cstruct.OFPFW_NW_PROTO

    if arp:
        match.ip_proto = arp.op
        match.wildcards &= ~cstruct.OFPFW_NW_PROTO
        match.ipv4_src = parse_ip(arp.psrc)
        match.wildcards &= ~cstruct.OFPFW_NW_SRC_MASK
        match.ipv4_dst = parse_ip(arp.pdst)
        match.wildcards &= ~cstruct.OFPFW_NW_DST_MASK

    return match
