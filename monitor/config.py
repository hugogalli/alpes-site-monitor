from dataclasses import dataclass
import os
from dotenv import load_dotenv, find_dotenv
import yaml

load_dotenv(dotenv_path=find_dotenv(usecwd=True), override=True)

@dataclass
class Settings:
    webhook_url: str
    expected_ips: set[str]
    vhosts_root: str
    min_body_bytes: int
    timeout: float

def load_settings() -> Settings:
    webhook = _get_env("DISCORD_WEBHOOK_URL")
    expected = {ip.strip() for ip in _get_env("EXPECTED_IPS").split(",") if ip.strip()}
    vhosts_root = _get_env("VHOSTS_ROOT", r"Z:\home\sites\vhosts")
    min_bytes = int(_get_env("MIN_BODY_BYTES", "1024"))
    timeout = float(_get_env("REQUEST_TIMEOUT_SECONDS", "10"))
    return Settings(webhook, expected, vhosts_root, min_bytes, timeout)

def load_domains(config_path="configs/domains.yml") -> list[dict]:
    """
    Retorna lista normalizada e sem duplicatas:
    { "host": str, "skip_ip_check": bool, "expected_ips": set[str] | None }
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return []

    raw = data.get("domains", [])
    if not isinstance(raw, list):
        return []

    by_host = {}  # último wins
    for item in raw:
        if isinstance(item, str):
            host = item.strip().lower()
            if host:
                by_host[host] = {"host": host, "skip_ip_check": False, "expected_ips": None}
        elif isinstance(item, dict):
            host = str(item.get("host", "")).strip().lower()
            if not host:
                continue
            skip = bool(item.get("skip_ip_check", False))
            exp = item.get("expected_ips")
            if isinstance(exp, list):
                exp = {str(ip).strip() for ip in exp if str(ip).strip()}
            else:
                exp = None
            by_host[host] = {"host": host, "skip_ip_check": skip, "expected_ips": exp}
    return list(by_host.values())



def _get_env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    if v is None:
        v = os.getenv("\ufeff" + name) 
    return v.strip() if v else default