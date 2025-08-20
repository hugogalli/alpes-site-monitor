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

def load_domains(config_path="configs/domains.yml") -> list[str]:
    """Carrega domínios do YAML de configuração"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return sorted(set(data.get("domains", [])))
    except FileNotFoundError:
        return []

def _get_env(name: str, default: str = "") -> str:
    v = os.getenv(name)
    if v is None:
        v = os.getenv("\ufeff" + name) 
    return v.strip() if v else default