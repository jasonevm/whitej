import requests
import re
import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, unquote

# --- CONFIGURATION ---
# URL for testing connectivity (simulated in this script environment)
CHECK_URL = "https://www.gstatic.com/generate_204"
TARGET_COUNT = 100
TIMEOUT = 5
MAX_WORKERS = 20

# 1. SOURCES (Combined from fds.txt and existing sources)
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/all.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/light.txt",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/vless.txt",
    "https://raw.githubusercontent.com/MahanKenway/Freedom-V2Ray/main/configs/mix.txt",
    "https://raw.githubusercontent.com/MahanKenway/Freedom-V2Ray/main/configs/vless.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-checker-backend/main/checked/RU_Best/ru_white.txt",
    "https://raw.githubusercontent.com/EtoNeYaProject/etoneyaproject.github.io/refs/heads/main/1",
    "https://gitverse.ru/api/repos/bywarm/rser/raw/branch/master/selected.txt",
    "https://gitverse.ru/api/repos/bywarm/rser/raw/branch/master/wl.txt",
    "https://gitverse.ru/api/repos/bywarm/rser/raw/branch/master/merged.txt",
    "https://wlrus.lol/confs/blackl.txt",
    "https://github.com/AvenCores/goida-vpn-configs/raw/refs/heads/main/githubmirror/26.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
    "https://raw.githubusercontent.com/prominbro/KfWL/refs/heads/main/KfWL.txt",
    "https://raw.githubusercontent.com/prominbro/sub/refs/heads/main/212.txt",
    "https://obwl.vercel.app/sub.txt",
    "https://raw.githubusercontent.com/vsevjik/OBWLautoupd/refs/heads/main/ru_vless_reality.txt",
    "https://raw.githubusercontent.com/tankist939-afk/Obhod-WL/refs/heads/main/Obhod%20WL",
    "https://raw.githubusercontent.com/AirLinkVPN1/AirLinkVPN/refs/heads/main/rkn_white_list",
    "https://raw.githubusercontent.com/RKPchannel/RKP_bypass_configs/refs/heads/main/configs/url_work.txt",
    "https://raw.githubusercontent.com/gergew452/Generation-Liberty/refs/heads/main/githubmirror/best.txt",
    "https://mygala.ru/vpn/premium.php",
    "https://raw.githubusercontent.com/Sanuyyq/sub-storage1/refs/heads/main/bs.txt",
    "https://gbr.mydan.online/configs",
    "https://raw.githubusercontent.com/Temnuk/naabuzil/refs/heads/main/Svoboda",
    "https://raw.githubusercontent.com/ewecrow78-gif/whitelist1/main/list.txt",
    "https://ety.twinkvibe.gay/whitelist",
    "https://raw.githubusercontent.com/LimeHi/LimeVPN/refs/heads/main/LimeVPN.txt?v=1",
    "https://raw.githubusercontent.com/ShatakVPN/ConfigForge-V2Ray/main/configs/ru/vless.txt",
    "https://subrostunnel.vercel.app/gen.txt",
    "https://subrostunnel.vercel.app/wl.txt",
    "https://rostunnel.vercel.app/mega.txt",
    "https://github.com/ksenkovsolo/HardVPN-bypass-WhiteLists-/raw/refs/heads/main/vpn-lte/WHITELIST-ALL.txt",
    "https://raw.githubusercontent.com/ByeWhiteLists/ByeWhiteLists2/refs/heads/main/ByeWhiteLists2.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-checker-backend/refs/heads/main/checked/RU_Best/ru_white_all_WHITE.txt",
    "https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta6.txt",
    "https://raw.githubusercontent.com/Ilyacom4ik/free-v2ray-2026/main/subscriptions/FreeCFGHub1.txt",
    "https://raw.githubusercontent.com/LimeHi/LimeVPNGenerator/main/Keys.txt?v=1",
    "http://livpnsub.dpdns.org/sub.php?token=20fd9e97b840e2f9",
    "https://subvpn.dpdns.org/sub.txt",
    "https://autosub-config.vercel.app/sub.txt",
    "https://raw.githubusercontent.com/CidVpn/cid-vpn-config/refs/heads/main/general.txt",
    "https://gitverse.ru/api/repos/cid-uskoritel/cid-white/raw/branch/master/whitelist.txt",
    "https://gitverse.ru/api/repos/Vsevj/OBS/raw/branch/master/wwh",
    "https://subrostunnel.vercel.app/std.txt",
    "https://raw.githubusercontent.com/kangaroo255075-collab/KrolekVPNReborn/refs/heads/main/Whitelist.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/all-servers.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/all-white-sub.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/all-white-lists-servers.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/best-white-lists-russia.txt",
    "https://raw.githubusercontent.com/SER38Off/happ-subscription/refs/heads/main/russia-white-lists.txt",
    "https://llxickvpn.vercel.app/api/index",
    "https://raw.githubusercontent.com/clowovx/clowovxVPN/refs/heads/main/clowovxVPN",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt",
    "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/26.txt",
    "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/27.txt",
    "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/28.txt",
    "https://raw.githubusercontent.com/pyatovsergey0105-maker/-/refs/heads/main/Whie_spiksik"
]

# Add Goida dynamic sources
for i in range(1, 21):
    SOURCES.append(f"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/{i}.txt")

# 2. WHITELIST DOMAINS (For SNI check)
WHITELIST_DOMAINS = [
    'gosuslugi.ru', 'mos.ru', 'nalog.ru', 'kremlin.ru', 'government.ru',
    'sberbank.ru', 'tbank.ru', 'alfabank.ru', 'vtb.ru', 'vk.com', 'ok.ru',
    'mail.ru', 'yandex.ru', 'dzen.ru', 'rutube.ru', 'ozon.ru', 'wildberries.ru',
    'avito.ru', 'rbc.ru', 'tass.ru', '2gis.ru', 'rzd.ru', 'hh.ru'
]

def decode_base64(data):
    try:
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8')
    except:
        return None

def extract_sni(config_url):
    match = re.search(r'[?&]sni=([^&]+)', config_url)
    if match:
        return unquote(match.group(1))
    return None

def is_whitelisted_sni(sni):
    if not sni: return False
    lower = sni.lower()
    return any(domain in lower or lower.endswith('.' + domain) for domain in WHITELIST_DOMAINS)

def get_country_info(config_url):
    lower = config_url.lower()
    if '.ir' in lower: return {'flag': '🇮🇷', 'country': 'Iran'}
    if '.ru' in lower: return {'flag': '🇷🇺', 'country': 'Russia'}
    if '.de' in lower: return {'flag': '🇩🇪', 'country': 'Germany'}
    if '.us' in lower: return {'flag': '🇺🇸', 'country': 'USA'}
    if '.nl' in lower: return {'flag': '🇳🇱', 'country': 'Netherlands'}
    if '.fi' in lower: return {'flag': '🇫🇮', 'country': 'Finland'}
    if '.pl' in lower: return {'flag': '🇵🇱', 'country': 'Poland'}
    if '.kz' in lower: return {'flag': '🇰🇿', 'country': 'Kazakhstan'}
    if '.tr' in lower: return {'flag': '🇹🇷', 'country': 'Turkey'}
    return {'flag': '🌐', 'country': 'Anycast'}

def fetch_source(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200: return []
        content = resp.text.strip()
        
        decoded = decode_base64(content)
        lines = (decoded or content).splitlines()
        
        configs = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if any(line.startswith(p) for p in ['vless://', 'vmess://', 'trojan://', 'ss://']):
                configs.append(line.split('#')[0])
        return configs
    except:
        return []

def format_name(config_url, index):
    country = get_country_info(config_url)
    protocol = config_url.split('://')[0].upper()
    sni = extract_sni(config_url) or "No SNI"
    return f"{country['flag']} {country['country']} | {protocol} | {sni} | #{index+1} | WhiteJ"

def main():
    print(f"Starting collection from {len(SOURCES)} sources...")
    all_configs = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_source, url) for url in SOURCES]
        for future in as_completed(futures):
            all_configs.extend(future.result())
            
    unique_configs = list(set(all_configs))
    print(f"Found {len(unique_configs)} unique configs.")
    
    # Filtering: Prioritize Reality/TLS and Whitelisted SNI
    priority_configs = []
    other_configs = []
    
    for cfg in unique_configs:
        sni = extract_sni(cfg)
        if is_whitelisted_sni(sni) or 'security=reality' in cfg.lower():
            priority_configs.append(cfg)
        else:
            other_configs.append(cfg)
            
    final_list = (priority_configs + other_configs)[:TARGET_COUNT]
    
    header = [
        "#profile-title: WhiteJ 100",
        "#profile-update-interval: 1",
        f"#announce: ⚡️ WhiteJ Optimized (100 Best) ⚡️",
        "#profile-web-page-url: https://github.com/jasonevm/whitej",
        ""
    ]
    
    output_lines = header
    for i, cfg in enumerate(final_list):
        name = format_name(cfg, i)
        output_lines.append(f"{cfg}#{name}")
        
    with open('configs.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
        
    print(f"Successfully saved {len(final_list)} configs to configs.txt")

if __name__ == "__main__":
    main()
