import ipaddress
from .dns_utils import resolve_records

# Fontes oficiais de IPs da Cloudflare:
# https://www.cloudflare.com/ips/  e https://developers.cloudflare.com/fundamentals/concepts/cloudflare-ip-addresses/
CF_IPV4_CIDRS = [
    "173.245.48.0/20","103.21.244.0/22","103.22.200.0/22","103.31.4.0/22",
    "141.101.64.0/18","108.162.192.0/18","190.93.240.0/20","188.114.96.0/20",
    "197.234.240.0/22","198.41.128.0/17","162.158.0.0/15","104.16.0.0/13",
    "104.24.0.0/14","172.64.0.0/13","131.0.72.0/22"
]
CF_IPV6_CIDRS = [
    "2400:cb00::/32","2606:4700::/32","2803:f800::/32","2405:b500::/32",
    "2405:8100::/32","2a06:98c0::/29","2c0f:f248::/32"
]

def _in_any_range(ip: str, cidrs: list[str]) -> bool:
    ip_obj = ipaddress.ip_address(ip)
    return any(ip_obj in ipaddress.ip_network(c) for c in cidrs)

def ips_are_cloudflare(ips: set[str]) -> bool:
    for ip in ips:
        if ":" in ip:  # IPv6
            if _in_any_range(ip, CF_IPV6_CIDRS):
                return True
        else:
            if _in_any_range(ip, CF_IPV4_CIDRS):
                return True
    return False

def uses_cloudflare_ns(ns_list: list[str]) -> bool:
    ns = [n.lower() for n in ns_list]
    return any(n.endswith(".cloudflare.com") for n in ns)

def cloudflare_status(domain: str):
    """
    Retorna dict: { mode, ns, ips }
    mode:
      - proxied_ok: NS Cloudflare e IP Cloudflare
      - dns_only_expondo_origem: NS Cloudflare e IP não Cloudflare
      - nao_cloudflare: NS não Cloudflare
      - possivelmente_proxied: IP Cloudflare sem NS Cloudflare (cadeia de CNAME, raro)
    """
    ans = resolve_records(domain)
    ns = ans.get("NS", [])
    aaaa = ans.get("AAAA", [])
    a = ans.get("A", [])
    ips = [*a, *aaaa]

    ns_cf = uses_cloudflare_ns(ns)
    ips_cf = ips_are_cloudflare(set(ips))

    if ns_cf and ips_cf:
        mode = "proxied_ok"
    elif ns_cf and not ips_cf:
        mode = "dns_only_expondo_origem"
    elif not ns_cf and ips_cf:
        mode = "possivelmente_proxied"
    else:
        mode = "nao_cloudflare"

    return {"mode": mode, "ns": ns, "ips": ips}
