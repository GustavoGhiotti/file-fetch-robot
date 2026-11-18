import requests


# import os
# import requests

# TOKEN = os.getenv("TOKEN") 
# base = f"https://api.telegram.org/bot{TOKEN}"

# resp = requests.get(f"{base}/getUpdates")
# resp.raise_for_status()
# data = resp.json()

# chat_infos = {}
# for update in data.get("result", []):
#     # pode haver message, edited_message, channel_post, etc.
#     msg = update.get("message") or update.get("edited_message") or update.get("channel_post")
#     if not msg:
#         continue
#     chat = msg.get("chat", {})
#     chat_id = chat.get("id")
#     title = chat.get("title")            
#     username = chat.get("username")       
#     first_name = chat.get("first_name")   
#     chat_type = chat.get("type")          
#     chat_infos[chat_id] = {
#         "type": chat_type,
#         "title": title,
#         "username": username,
#         "first_name": first_name,
#     }

# for cid, info in chat_infos.items():
#     print(f"chat_id: {cid} — type: {info['type']} — title/username: {info['title'] or info['username'] or info['first_name']}")


def enviar_telegram(token: str, chat_id: str, texto: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML" 
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            return True
        else:
            print(f"Telegram envio falhou. Status: {r.status_code}, resp: {r.text}")
            return False
    except Exception as e:
        print(f"Erro ao chamar Telegram API: {e}")
        return False
