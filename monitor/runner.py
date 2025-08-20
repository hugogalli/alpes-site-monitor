from .config import load_settings, load_domains
from .dns_utils import resolve_records, ips_from_answers
from .http_utils import check_http
from .notifier import send_discord

def evaluate_domain(domain: str, expected_ips: set[str], timeout: float, min_bytes: int):
    dns_ans = resolve_records(domain)
    ips = ips_from_answers(dns_ans)
    http = check_http(domain, timeout, min_bytes)

    domain_ok = True
    problems = []

    # 1) IPs esperados
    if expected_ips:
        if not ips:
            domain_ok = False
            problems.append("DNS não retornou A/AAAA")
        elif not any(ip in expected_ips for ip in ips):
            domain_ok = False
            problems.append(f"A/AAAA diferente dos IPs esperados: {sorted(ips)}")

    # 2) Saúde HTTP
    if not http.get("ok", False):
        domain_ok = False
        reason = []
        if not http.get("ok_status", True):
            reason.append("status inválido")
        if not http.get("ok_size", True):
            reason.append("payload muito pequeno")
        if http.get("error_marker"):
            reason.append("marcador de erro no HTML")
        if http.get("error"):
            reason.append(f"exceção: {http['error']}")
        problems.append("HTTP falhou: " + ", ".join(reason) if reason else "HTTP falhou")

    details = {
        "dns": dns_ans,
        "ips": sorted(ips),
        "http": http,
    }
    return domain_ok, problems, details

def main():
    s = load_settings()
    domains = load_domains()
    if not domains:
        print("Nenhum domínio configurado em configs/domains.yml")
        return

    for d in domains:
        ok, probs, details = evaluate_domain(d, s.expected_ips, s.timeout, s.min_body_bytes)
        fields = [
            {"name": "Domínio", "value": d, "inline": False},
            {"name": "IPs resolvidos", "value": ", ".join(details["ips"]) or "—", "inline": False},
            {"name": "NS", "value": ", ".join(details["dns"].get("NS", [])) or "—", "inline": False},
            {"name": "HTTP", "value": f"{details['http'].get('status_code','?')} {details['http'].get('final_url','')}", "inline": False},
        ]

        if ok:
            send_discord(s.webhook_url, "✅ Site OK", "Tudo certo no último check", fields, color=0x2ECC71)
        else:
            fields.append({"name": "Problemas", "value": "\n".join(f"- {p}" for p in probs)[:950] or "—", "inline": False})
            send_discord(s.webhook_url, "🚨 Alerta: site com problemas", "Algumas verificações falharam", fields, color=0xE74C3C)

if __name__ == "__main__":
    main()
