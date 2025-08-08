import unicodedata
import difflib

def load_safe_domains(filename="safe_domains.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

def extract_domain(url):
    url = url.lower().strip()
    if "://" in url:
        url = url.split("://", 1)[1]
    if url.startswith("www."):
        url = url[4:]
    if "/" in url:
        url = url.split("/",1)[0]
    return url

def normalize_domain(domain):
    return unicodedata.normalize("NFKC", domain)

def is_homoglyph(domain, safe_domains):
    normalized = normalize_domain(domain)
    if normalized in safe_domains:
        return False
    match = difflib.get_close_matches(normalized, safe_domains, n=1, cutoff=0.8)
    if match:
        return True
    return False

def highlight_and_reason(domain, safe_domains):
    normalized = normalize_domain(domain)
    match = difflib.get_close_matches(normalized, safe_domains, n=1, cutoff=0.8)
    if not match:
        return domain, "Looks very different from legitimate domains"

    legit = match[0]
    highlighted = ""
    reasons = []
    for i, (c_input, c_legit) in enumerate(zip(domain, legit)):
        if c_input != c_legit:
            try:
                name_input = unicodedata.name(c_input)
                name_legit = unicodedata.name(c_legit)
                if name_input != name_legit:
                    reasons.append(f"position {i+1}: '{c_input}' is {name_input}, should be '{c_legit}' ({name_legit})")
            except Exception:
                reasons.append(f"position {i+1}: '{c_input}' is suspicious char")
            highlighted += f"[{c_input}]"
        else:
            highlighted += c_input
    highlighted += domain[len(legit):]
    if reasons:
        return highlighted, "; ".join(reasons)
    else:
        return domain, "Very similar - possible suspicious pattern"

def check_single_url(url, safe_domains):
    domain = extract_domain(url)
    if is_homoglyph(domain, safe_domains):
        highlighted, reason = highlight_and_reason(domain, safe_domains)
        print(f"\033[91m⚠  Suspicious: {url}\033[0m")
        print(f"      Highlight: {highlighted}")
        print(f"      Reason:    {reason}\n")
    else:
        print(f"✅ Safe:       {url}\n")

if __name__ == "__main__":
    safe_domains = load_safe_domains()
    print("Type 'exit' to quit.")
    while True:
        user_input = input("Please enter a URL/domain to check: ").strip()
        if user_input.lower() == "exit":
            print("Thanks for using the homoglyph detector! Bye.")
            break
        if user_input == "":
            continue
        check_single_url(user_input, safe_domains)