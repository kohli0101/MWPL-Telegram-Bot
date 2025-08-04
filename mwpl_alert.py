import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
LAST_FILE = 'last_ban_list.txt'

def get_banned_stocks():
    url = 'https://www.niftytrader.in/ban-list'
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print("Failed to access NiftyTrader page:", resp.status_code)
        return set()

    soup = BeautifulSoup(resp.text, 'html5lib')
    rows = soup.select('div.ban-list table tr')
    symbols = set()

    for tr in rows[1:]:  # Skip header row
        cols = tr.find_all('td')
        if cols:
            symbol = cols[0].text.strip()
            if symbol:
                symbols.add(symbol)
    return symbols

def load_last_ban_list():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_current_ban_list(ban_list):
    with open(LAST_FILE, 'w') as f:
        f.write("\n".join(ban_list))

def send_telegram_alert(new_bans):
    if new_bans:
        message = f"🚨 *New MWPL Ban Additions* ({datetime.now().strftime('%d-%b-%Y')}):\n" + "\n".join(f"🔒 {s}" for s in new_bans)
    else:
        message = f"✅ No new stocks added to MWPL ban list on {datetime.now().strftime('%d-%b-%Y')}."
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    response = requests.post(url, data=payload)
    print("Telegram Response:", response.status_code, response.text)

if __name__ == '__main__':
    current_bans = get_banned_stocks()
    last_bans = load_last_ban_list()
    new_additions = current_bans - last_bans

    send_telegram_alert(new_additions)
    save_current_ban_list(current_bans)
