import requests
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Example Chartink Screener URL
CHARTINK_URL = "https://chartink.com/screener/f-f-1hr-swing"

def fetch_chartink_results():
    try:
        response = requests.post("https://chartink.com/screener/process", data={"scan_clause": ""})
        data = response.json()
        stocks = [item["nsecode"] for item in data.get("data", [])]
        return stocks
    except Exception as e:
        return [f"Error: {e}"]

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

if __name__ == "__main__":
    stocks = fetch_chartink_results()
    if stocks:
        message = "📊 Chartink Screener Results:\n" + "\n".join(stocks)
    else:
        message = "⚠️ No stocks found."
    send_message(message)
