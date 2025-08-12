from scapy.all import IP, ICMP, TCP, Ether
from ids_main import detect_from_pcap

def test_icmp_echo_request():
    # Make a Dummy ICMP packet
    pkt = Ether()/IP(src="1.2.3.4", dst="5.6.7.8")/ICMP(type=8)
    assert pkt[ICMP].type == 8

def test_tcp_syn_flag():
    pkt = Ether()/IP(src="1.2.3.4", dst="5.6.7.8")/TCP(flags="S")
    assert pkt[TCP].flags == "S"
    