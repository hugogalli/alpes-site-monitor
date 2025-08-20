import httpx
import re

GENERIC_ERROR_PATTERNS = [
    r"account suspended",
    r"temporariamente indispon[ií]vel",
    r"error\s5\d\d",
    r"service unavailable",
    r"bad gateway",
    r"origin is unreachable",
    r"cloudflare\serror",
    r"blocked by",
    r"maintenance",
    r"suspended",
]

def check_http(domain: str, timeout: float, min_bytes: int) -> dict:
    """
    Faz uma requisição HTTPS ao domínio com follow redirects e timeout.
    Aplica heurísticas básicas de saúde do HTML.
    """
    url = f"https://{domain}"
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "alpes-monitor/1.0"}
        ) as c:
            r = c.get(url)

        ok_status = 200 <= r.status_code < 400
        ok_size = len(r.content) >= min_bytes

        # texto limitado para evitar custo alto em páginas grandes
        body_txt = r.text.lower()[:5000]
        has_error_word = any(re.search(pat, body_txt, re.I) for pat in GENERIC_ERROR_PATTERNS)

        return {
            "url": url,
            "status_code": r.status_code,
            "final_url": str(r.url),
            "content_length": len(r.content),
            "ok_status": ok_status,
            "ok_size": ok_size,
            "error_marker": has_error_word,
            "ok": bool(ok_status and ok_size and not has_error_word),
        }
    except Exception as e:
        return {
            "url": url,
            "ok": False,
            "error": str(e),
        }
