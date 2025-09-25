from scapy.all
from ids_main import detect_from_pcap

def test_icmp_echo_request():
    pkt = Ether()/IP(src="1.2.3.4", dst="5.6.7.8")/ICMP(type)
    assert pkt[ICMP]

def test_tcp_syn_flag():
    pkt = Ether()/IP(src="1.2.3.4", dst="5.6.7.8")/TCP(flag)
    assert pkt[TCP]
    
