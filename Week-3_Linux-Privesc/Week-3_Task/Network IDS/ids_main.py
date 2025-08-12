from scapy.all import rdpcap, IP, TCP, ICMP
from collections import defaultdict

# -------- Threshold Settings -------- #
ICMP_THRESHOLD = 10
SYN_THRESHOLD = 20

# Summary data store
summary_data = []

def detect_from_pcap(pcap_file):
    print("\n==============================")
    print(f"📂 Processing file: {pcap_file}")
    print("==============================")

    icmp_count = defaultdict(int)
    syn_count = defaultdict(int)
    total_packets = 0
    alert_count = 0
    suspicious_count = 0

    packets = rdpcap(pcap_file)
    total_packets = len(packets)

    for pkt in packets:
        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst

            # ICMP Detection
            if ICMP in pkt:
                icmp_type = pkt[ICMP].type
                if icmp_type == 8:  # Echo Request
                    print(f"[ALERT] ICMP Echo Request from {src} to {dst}")
                    icmp_count[src] += 1
                    alert_count += 1
                elif icmp_type == 0:  # Echo Reply
                    print(f"[ALERT] ICMP Echo Reply from {src} to {dst}")
                    alert_count += 1
                else:
                    print(f"[NORMAL] ICMP type {icmp_type} from {src} to {dst}")

            # TCP Detection
            elif TCP in pkt:
                flags = pkt[TCP].flags
                dport = pkt[TCP].dport
                if flags == 'S':
                    print(f"[ALERT] TCP SYN from {src} to {dst}:{dport}")
                    syn_count[src] += 1
                    alert_count += 1
                elif flags == 'F':
                    print(f"[ALERT] TCP FIN Scan from {src} to {dst}:{dport}")
                    alert_count += 1
                elif flags == 0:
                    print(f"[ALERT] TCP NULL Scan from {src} to {dst}:{dport}")
                    alert_count += 1
                else:
                    print(f"[NORMAL] TCP from {src} to {dst}:{dport} with flags {flags}")
            else:
                print(f"[NORMAL] Non-TCP/ICMP traffic from {src} to {dst}")

    # -------- Suspicious Reason Summary -------- #
    suspicious_found = False
    for ip, count in icmp_count.items():
        if count > ICMP_THRESHOLD:
            print(f"[SUSPICIOUS] Reason: Possible ICMP flood from {ip} | Total ICMP Echo Requests: {count}")
            suspicious_found = True
            suspicious_count += 1

    for ip, count in syn_count.items():
        if count > SYN_THRESHOLD:
            print(f"[SUSPICIOUS] Reason: Possible TCP SYN scan from {ip} | Total SYN packets: {count}")
            suspicious_found = True
            suspicious_count += 1

    if not suspicious_found:
        print("[INFO] No suspicious activity detected for this file.")

    # Add to summary table
    summary_data.append({
        "file": pcap_file,
        "total_packets": total_packets,
        "alert_count": alert_count,
        "suspicious_count": suspicious_count
    })

def print_summary_table():
    print("\n================ SUMMARY TABLE ================")
    print(f"{'File Name':<25} {'Packets':<10} {'Alerts':<10} {'Suspicious':<12}")
    print("-" * 60)
    for entry in summary_data:
        print(f"{entry['file']:<25} {entry['total_packets']:<10} {entry['alert_count']:<10} {entry['suspicious_count']:<12}")
    print("================================================")

def main():
    # Set file names
    normal_file = "N-Files/tfp_capture.pcapng"   # normal traffic
    attack_file = "Atck-Files/nmap_OS_scan"        # suspicious traffic

    detect_from_pcap(normal_file)
    detect_from_pcap(attack_file)
    print_summary_table()

if __name__ == "__main__":
    main()