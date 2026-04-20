
import requests
import re
import os

# 1. SOURCES
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/all.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/light.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/vless.txt",
    "https://raw.githubusercontent.com/MahanKenway/Freedom-V2Ray/main/configs/mix.txt",
    "https://raw.githubusercontent.com/MahanKenway/Freedom-V2Ray/main/configs/vless.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-checker-backend/main/checked/RU_Best/ru_white.txt"
]
for i in range(1, 21):
    SOURCES.append(f"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/{i}.txt")

# 2. WHITELIST DOMAINS
WHITELIST_DOMAINS = [
    'gosuslugi.ru', 'mos.ru', 'nalog.ru', 'kremlin.ru', 'government.ru',
    'sberbank.ru', 'tbank.ru', 'alfabank.ru', 'vtb.ru', 'vk.com', 'ok.ru',
    'mail.ru', 'yandex.ru', 'dzen.ru', 'rutube.ru', 'ozon.ru', 'wildberries.ru',
    'avito.ru', 'rbc.ru', 'tass.ru', '2gis.ru', 'rzd.ru', 'hh.ru'
]

# 3. COUNTRY FLAG
def extract_flag_and_country(text):
    if '🇺🇸' in text: return {'flag': '🇺🇸', 'country': 'США'}
    if '🇬🇧' in text: return {'flag': '🇬🇧', 'country': 'Великобритания'}
    if '🇩🇪' in text: return {'flag': '🇩🇪', 'country': 'Германия'}
    if '🇫🇷' in text: return {'flag': '🇫🇷', 'country': 'Франция'}
    if '🇫🇮' in text: return {'flag': '🇫🇮', 'country': 'Финляндия'}
    if '🇳🇱' in text: return {'flag': '🇳🇱', 'country': 'Нидерланды'}
    if '🇵🇱' in text: return {'flag': '🇵🇱', 'country': 'Польша'}
    if '🇰🇿' in text: return {'flag': '🇰🇿', 'country': 'Казахстан'}
    return {'flag': '🌐', 'country': 'Anycast'}

# 4. EXTRACT SNI
def extract_sni(url_part, comment):
    sni = ''
    match = re.search(r'[?&]sni=([^&]+)', url_part + '#' + comment)
    if match: 
        sni = requests.utils.unquote(match.group(1))
    return sni or 'sni отсутствует'

# 5. CHECK SNI IN WHITELIST
def is_whitelisted_sni(sni):
    if not sni: return False
    lower = sni.lower()
    return any(domain in lower or lower.endswith('.' + domain) for domain in WHITELIST_DOMAINS)

# 6. FUNCTION: parse line, return { url, newName } or null
def parse_config_line(line):
    line = line.strip()
    if not line: return None
    
    parts = line.split('#', 1)
    url_part = parts[0].strip()
    comment = parts[1].strip() if len(parts) > 1 else ''

    if not url_part.startswith('vless://') and not url_part.startswith('vmess://') and not url_part.startswith('trojan://'):
        return None
    
    flag_country = extract_flag_and_country(comment + ' ' + url_part)
    sni = extract_sni(url_part, comment)
    
    if not is_whitelisted_sni(sni):
        return None
                          
    return {'url': url_part, 'newName': f"{flag_country['flag']} {flag_country['country']} | sni = {sni} | от катлер"}

# 7. FUNCTION: download and parse one sourse
def fetch_source(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return [
            parse_config_line(line)
            for line in response.text.split('\n')
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

# 8. MAIN FUNCTION: collection, filtration, storage
def main():
    LIMIT = 500 # Default limit, can be made configurable if needed
    
    all_configs = []
    url_set = set()
    
    for url in SOURCES:
        if len(all_configs) >= LIMIT: break
        configs = fetch_source(url)
        for cfg in configs:
            if cfg and cfg['url'] not in url_set:
                url_set.add(cfg['url'])
                all_configs.append(cfg)
                if len(all_configs) >= LIMIT: break

    
    import datetime
    current_version = datetime.datetime.now().strftime("%Y%m%d.%H%M")

    header = [
        "#profile-title: WhiteJ",
        "#profile-update-interval: 2",
        f"#announce: ⚡️ WhiteJ version: {1} ⚡️",
        "#profile-web-page-url: https://github.com/jasonevm/whitej",
        ""
    ]
    
    content = '\n'.join(header)
    for cfg in all_configs:
        content += f"\n{cfg['url']}#{cfg['newName']}"
    
    # Print to stdout, which will be captured by the GitHub Action and saved to a file
    print(content)

if __name__ == '__main__':
    main()
