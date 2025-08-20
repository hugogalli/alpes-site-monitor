from .config import load_settings, load_domains
from .dns_utils import resolve_records, ips_from_answers
from .http_utils import check_http
from .notifier import send_discord
from .cf_utils import cloudflare_status  # novo import

def evaluate_domain(domain: str, expected_ips: set[str], timeout: float, min_bytes: int):
    dns_ans = resolve_records(domain)
    ips = ips_from_answers(dns_ans)

    domain_ok = True
    problems = []

    # 0) DNS precisa resolver SEMPRE
    if not ips:
        domain_ok = False
        problems.append("DNS não retornou A/AAAA")
        cf = cloudflare_status(domain)  # opcional; retorna vazio aqui
        http = {"status_code": "—", "final_url": "", "ok": False}
        details = {"dns": dns_ans, "ips": [], "http": http, "cf": cf}
        return domain_ok, problems, details

    # 1) Cloudflare primeiro
    cf = cloudflare_status(domain)
    if cf["mode"] == "dns_only_expondo_origem":
        domain_ok = False
        problems.append("Cloudflare em NS, mas IP não é Cloudflare (DNS Only expondo origin)")

    # 2) Checagem de IPs esperados só quando NÃO está proxied pela Cloudflare
    if expected_ips and cf["mode"] == "nao_cloudflare":
        if not any(ip in expected_ips for ip in ips):
            domain_ok = False
            problems.append(f"A/AAAA diferente dos IPs esperados: {sorted(ips)}")

    # 3) HTTP
    http = check_http(domain, timeout, min_bytes)
    if not http.get("ok", False):
        domain_ok = False
        reason = []
        if not http.get("ok_status", True): reason.append("status inválido")
        if not http.get("ok_size", True): reason.append("payload muito pequeno")
        if http.get("error_marker"): reason.append("marcador de erro no HTML")
        if http.get("error"): reason.append(f"exceção: {http['error']}")
        problems.append("HTTP falhou: " + ", ".join(reason) if reason else "HTTP falhou")

    details = {"dns": dns_ans, "ips": sorted(ips), "http": http, "cf": cf}
    return domain_ok, problems, details

def main():
    s = load_settings()
    domains = load_domains()
    if not domains:
        print("Nenhum domínio configurado em configs/domains.yml")
        return

    for entry in domains:
        host = entry["host"]
        skip_ip_check = entry["skip_ip_check"]
        expected_set = set(entry["expected_ips"]) if entry["expected_ips"] else s.expected_ips

        ok, probs, details = evaluate_domain(
            host,
            expected_set if not skip_ip_check else set(),
            s.timeout,
            s.min_body_bytes
        )

        fields = [
            {"name": "Domínio", "value": host, "inline": False},
            {"name": "IPs resolvidos", "value": ", ".join(details["ips"]) or "—", "inline": False},
            {"name": "NS", "value": ", ".join(details["dns"].get("NS", [])) or "—", "inline": False},
            {"name": "Cloudflare", "value": details["cf"]["mode"], "inline": False},  # novo
            {"name": "HTTP", "value": f"{details['http'].get('status_code','?')} {details['http'].get('final_url','')}".strip(), "inline": False},
        ]

        if ok:
            send_discord(s.webhook_url, "✅ Site OK", "Tudo certo no último check", fields, color=0x2ECC71)
        else:
            fields.append({"name": "Problemas", "value": "\n".join(f"- {p}" for p in probs)[:950] or "—", "inline": False})
            send_discord(s.webhook_url, "🚨 Alerta: site com problemas", "Algumas verificações falharam", fields, color=0xE74C3C)

if __name__ == "__main__":
    main()
