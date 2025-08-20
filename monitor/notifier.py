import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any

def send_discord(webhook_url: str, title: str, description: str, fields: List[Dict[str, Any]], color: int = 0xE63946):
    """
    Envia um embed simples para o Discord. Se webhook_url estiver vazio, imprime payload (modo debug).
    """
    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": fields[:25],  # limite do Discord
            }
        ]
    }

    if not webhook_url:
        print("(debug) Webhook não configurado. Payload:")
        print(payload)
        return

    with httpx.Client(timeout=10) as c:
        r = c.post(webhook_url, json=payload)
        r.raise_for_status()
