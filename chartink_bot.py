import requests
import re
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def fetch_chartink_results():
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    # Step 1: Get main Chartink page to grab CSRF token
    r = session.get("https://chartink.com", headers=headers)
    token_match = re.search(r'<meta name="csrf-token" content="(.*?)"', r.text)
    if not token_match:
        return ["Error: Could not find CSRF token"]
    csrf_token = token_match.group(1)

    # Step 2: POST request with token + scan_clause
    payload = {
        "_token": csrf_token,
        "scan_clause": '( {33489} ( [=1] 30 minute low < [=-1] 30 minute close and [=1] 1 hour close > 1 day ago high and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" < 2 and [=1] 1 hour "close - 1 candle ago close / 1 candle ago close * 100" > 1 ) )'
    }
    process_url = "https://chartink.com/screener/process"
    try:
        resp = session.post(process_url, data=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        stocks = [item["nsecode"] for item in data.get("data", [])]
        return stocks if stocks else ["⚠️ No stocks matched your screener"]
    except Exception as e:
        return [f"Error: {e}\nResponse: {resp.text[:200]}"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

if __name__ == "__main__":
    stocks = fetch_chartink_results()
    if stocks and not stocks[0].startswith("Error"):
        message = "📊 Chartink Screener Results:\n" + "\n".join(stocks)
    else:
        message = "\n".join(stocks)
    send_message(message)
