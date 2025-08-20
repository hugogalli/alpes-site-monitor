import ipaddress
import dns.resolver

def resolve_records(domain: str):
    """
    Resolve A, AAAA, NS, CNAME e TXT do domínio.
    Retorna dict: {"A": [], "AAAA": [], "NS": [], "CNAME": [], "TXT": []}
    """
    res = dns.resolver.Resolver()
    # timeouts mais curtos evitam travar o runner
    res.lifetime = 5.0
    res.timeout = 3.0

    answers = {"A": [], "AAAA": [], "NS": [], "CNAME": [], "TXT": []}
    for rtype in ["A", "AAAA", "NS", "CNAME", "TXT"]:
        try:
            ans = res.resolve(domain, rtype)
            for r in ans:
                if hasattr(r, "target"):  # NS/CNAME
                    answers[rtype].append(str(r.target).strip("."))
                else:
                    answers[rtype].append(str(r).strip("."))
        except Exception:
            # silencioso por robustez: domínio pode não ter todos os tipos
            pass
    return answers

def ips_from_answers(answers: dict) -> set[str]:
    """
    Extrai e valida os IPs das listas A e AAAA.
    """
    ips = set()
    for ip in answers.get("A", []):
        try:
            ipaddress.ip_address(ip)
            ips.add(ip)
        except ValueError:
            pass
    for ip6 in answers.get("AAAA", []):
        try:
            ipaddress.ip_address(ip6)
            ips.add(ip6)
        except ValueError:
            pass
    return ips
