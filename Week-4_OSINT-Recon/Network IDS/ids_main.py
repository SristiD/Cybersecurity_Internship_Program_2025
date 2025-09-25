from scapy.all import rdpcap
from collection import defaultdict

ICMP_THRESHOLD = 10
SYN_THRESHOLD = 20

summary_data = []

def detect_from_pcap(pcap_file):
    print("\n==============================")
    print(f"📂 Processing file: {pcap_file}")
    print("==============================")

    icmp_count = defaultdict(int)
    syn_count = defaultdict(int)

    for pkt in packets:
        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst

            if ICMP in pkt:
                icmp_type = pkt[ICMP].type
                if icmp_type == 8:
                    print(f"[ALERT] ICMP Echo Request from {src} to {dst}")
                    icmp_count[src] += 1
                    alert_count += 1
                else:
                    print(f"[NORMAL] ICMP type {icmp_type} from {src} to {dst}")
                    
            elif TCP in pkt:
                flags = pkt[TCP]
                dport = pkt[TCP].dport
                if flags == 'S':
                    print(f"[ALERT] TCP SYN from {src} to {dst}:{dport}")
                    syn_count[src] += 1
                    alert_count += 1
                elif flags == 0:
                    print(f"[ALERT] TCP NULL Scan from {src} to {dst}:{dport}")
                    alert_count += 1
                else:
                    print(f"[NORMAL] TCP from {src} to {dst}:{dport} with flags {flags}")
            else:
                print(f"[NORMAL] Non-TCP/ICMP traffic from {src} to {dst}")

    suspicious_found = False
    for ip, count in icmp_count.items():
        if count > ICMP_THRESHOLD:
            print(f"[SUSPICIOUS] Reason: Possible ICMP flood from {ip} | Total ICMP Echo Requests: {count}")

    for ip, count in syn_count.items():
        if count > SYN_THRESHOLD:
            print(f"[SUSPICIOUS] Reason: Possible TCP SYN scan from {ip} | Total SYN packets: {count}")

    if not suspicious_found:
        print("[INFO] No suspicious activity detected for this file.")

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
    normal_file = "N-Files"   
    attack_file = "Atck-Files"       

    detect_from_pcap(normal_file)
    detect_from_pcap(attack_file)
    print_summary_table()

if __name__ == "__main__":

    main()
