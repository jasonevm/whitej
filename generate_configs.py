#!/usr/bin/env python3
"""
WhiteJ Config Aggregator v2
Collect → Parse → Dedup → TCP-test → Score → Export
"""

import asyncio
import aiohttp
import re
import base64
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse, parse_qs, unquote

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

TARGET_COUNT   = 100
FETCH_TIMEOUT  = 10      # sec, per source
TCP_TIMEOUT    = 3       # sec, per endpoint
MAX_FETCH_CONC = 40      # parallel source fetches
MAX_TEST_CONC  = 80      # parallel TCP probes

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
    "https://raw.githubusercontent.com/pyatovsergey0105-maker/-/refs/heads/main/Whie_spiksik",
    *[f"https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/{i}.txt"
      for i in range(1, 21)],
]

# SNI whitelisting: конфиги с такими доменами в SNI имеют split-routing приоритет
WHITELIST_DOMAINS = [
    'gosuslugi.ru', 'mos.ru', 'nalog.ru', 'kremlin.ru', 'government.ru',
    'sberbank.ru', 'tbank.ru', 'alfabank.ru', 'vtb.ru', 'vk.com', 'ok.ru',
    'mail.ru', 'yandex.ru', 'dzen.ru', 'rutube.ru', 'ozon.ru', 'wildberries.ru',
    'avito.ru', 'rbc.ru', 'tass.ru', '2gis.ru', 'rzd.ru', 'hh.ru',
]

_TLD_MAP = {
    '.ir': ('🇮🇷', 'Iran'),     '.ru': ('🇷🇺', 'Russia'),  '.de': ('🇩🇪', 'Germany'),
    '.us': ('🇺🇸', 'USA'),      '.nl': ('🇳🇱', 'NL'),       '.fi': ('🇫🇮', 'Finland'),
    '.pl': ('🇵🇱', 'Poland'),   '.kz': ('🇰🇿', 'KZ'),       '.tr': ('🇹🇷', 'Turkey'),
    '.fr': ('🇫🇷', 'France'),   '.gb': ('🇬🇧', 'UK'),        '.se': ('🇸🇪', 'Sweden'),
    '.ch': ('🇨🇭', 'CH'),       '.at': ('🇦🇹', 'Austria'),  '.cz': ('🇨🇿', 'CZ'),
    '.ua': ('🇺🇦', 'Ukraine'),  '.am': ('🇦🇲', 'Armenia'),  '.ge': ('🇬🇪', 'Georgia'),
    '.az': ('🇦🇿', 'AZ'),       '.lt': ('🇱🇹', 'LT'),        '.lv': ('🇱🇻', 'LV'),
    '.ee': ('🇪🇪', 'EE'),       '.jp': ('🇯🇵', 'Japan'),    '.sg': ('🇸🇬', 'SG'),
    '.hk': ('🇭🇰', 'HK'),       '.tw': ('🇹🇼', 'Taiwan'),   '.ro': ('🇷🇴', 'Romania'),
    '.hu': ('🇭🇺', 'Hungary'),  '.sk': ('🇸🇰', 'SK'),        '.bg': ('🇧🇬', 'BG'),
    '.rs': ('🇷🇸', 'Serbia'),   '.md': ('🇲🇩', 'Moldova'),  '.mk': ('🇲🇰', 'MK'),
    '.si': ('🇸🇮', 'Slovenia'), '.hr': ('🇭🇷', 'Croatia'),  '.ba': ('🇧🇦', 'BA'),
    '.ca': ('🇨🇦', 'Canada'),   '.au': ('🇦🇺', 'AU'),        '.br': ('🇧🇷', 'Brazil'),
    '.cn': ('🇨🇳', 'China'),    '.kr': ('🇰🇷', 'Korea'),    '.in': ('🇮🇳', 'India'),
}

# ── LOGGING ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('whitej')

# ── DATA MODEL ────────────────────────────────────────────────────────────────

@dataclass
class Config:
    protocol: str
    host:     str
    port:     int
    uid:      str          # uuid / password / key prefix
    raw:      str          # URI без fragment
    sni:      str  = ''
    security: str  = ''
    network:  str  = ''
    latency:  Optional[float] = None

    def key(self) -> str:
        """Канонический ключ для дедупликации."""
        return f"{self.protocol}|{self.host.lower()}|{self.port}|{self.uid[:12]}"

    @property
    def score(self) -> int:
        s = 0
        sec = self.security.lower()
        if sec == 'reality':  s += 50
        elif sec == 'tls':    s += 25
        if self.sni and any(d in self.sni for d in WHITELIST_DOMAINS):
            s += 30
        if self.latency is not None:
            # 0 ms → +30, 3000 ms → 0, линейно
            s += max(0, 30 - int(self.latency / 100))
        return s

# ── HELPERS ───────────────────────────────────────────────────────────────────

def _b64dec(s: str) -> Optional[str]:
    """Декодирует base64 строку. Возвращает None при неудаче."""
    try:
        s = s.strip()
        pad = (-len(s)) % 4
        decoded = base64.b64decode(s + '=' * pad)
        return decoded.decode('utf-8', errors='replace')
    except Exception:
        return None

def _country(host: str) -> tuple[str, str]:
    h = host.lower()
    for tld, pair in _TLD_MAP.items():
        if h.endswith(tld) or (tld + '.') in h:
            return pair
    return '🌐', 'Unknown'

# ── PROTOCOL PARSERS ──────────────────────────────────────────────────────────

def _parse_vless(raw: str) -> Optional[Config]:
    try:
        p  = urlparse(raw)
        qs = parse_qs(p.query)
        host = p.hostname or ''
        port = p.port or 443
        if not host or not port:
            return None
        return Config(
            protocol='vless',
            host=host, port=port,
            uid=p.username or '',
            raw=raw,
            sni=qs.get('sni', [''])[0],
            security=qs.get('security', [''])[0].lower(),
            network=qs.get('type', [''])[0].lower(),
        )
    except Exception:
        return None

def _parse_vmess(raw: str) -> Optional[Config]:
    """vmess:// — тело это base64(JSON)."""
    try:
        decoded = _b64dec(raw[8:])
        if not decoded:
            return None
        d = json.loads(decoded)
        host = str(d.get('add', '')).strip()
        port = int(d.get('port', 443))
        if not host or not port:
            return None
        sni = (d.get('sni') or d.get('host') or '').strip()
        tls = 'tls' if str(d.get('tls', '')).lower() == 'tls' else ''
        return Config(
            protocol='vmess',
            host=host, port=port,
            uid=str(d.get('id', '')),
            raw=raw,
            sni=sni,
            security=tls,
            network=str(d.get('net', '')).lower(),
        )
    except Exception:
        return None

def _parse_trojan(raw: str) -> Optional[Config]:
    try:
        p  = urlparse(raw)
        qs = parse_qs(p.query)
        host = p.hostname or ''
        port = p.port or 443
        if not host:
            return None
        return Config(
            protocol='trojan',
            host=host, port=port,
            uid=p.username or '',
            raw=raw,
            sni=qs.get('sni', [''])[0] or host,
            security='tls',   # trojan всегда TLS
            network=qs.get('type', [''])[0].lower(),
        )
    except Exception:
        return None

def _parse_ss(raw: str) -> Optional[Config]:
    """
    Два формата:
      ss://BASE64(method:pass)@host:port
      ss://BASE64(method:pass@host:port)
    """
    try:
        p = urlparse(raw)
        qs = parse_qs(p.query)
        if p.hostname:
            # Стандартный формат: userinfo = base64(method:pass)
            host = p.hostname
            port = p.port or 8388
            uid  = p.username or ''
        else:
            # Старый формат: вся netloc — base64
            decoded = _b64dec(p.netloc)
            if not decoded:
                return None
            m = re.match(r'(.+)@([^:@]+):(\d+)$', decoded)
            if not m:
                return None
            uid, host, port = m.group(1), m.group(2), int(m.group(3))
        if not host:
            return None
        return Config(
            protocol='ss',
            host=host, port=port,
            uid=uid[:20],
            raw=raw,
            sni=qs.get('sni', [''])[0],
            security='none',
            network=qs.get('type', [''])[0].lower(),
        )
    except Exception:
        return None

_PARSERS: dict[str, callable] = {
    'vless://':  _parse_vless,
    'vmess://':  _parse_vmess,
    'trojan://': _parse_trojan,
    'ss://':     _parse_ss,
}

def _parse_line(line: str) -> Optional[Config]:
    uri = line.split('#')[0].strip()   # убираем fragment
    for prefix, fn in _PARSERS.items():
        if uri.startswith(prefix):
            return fn(uri)
    return None

# ── SOURCE FETCHER ────────────────────────────────────────────────────────────

_PROTO_PREFIXES = tuple(_PARSERS.keys())

async def _fetch(session: aiohttp.ClientSession, url: str) -> list[str]:
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT),
            ssl=False, allow_redirects=True,
        ) as r:
            if r.status != 200:
                log.debug('HTTP %d  %s', r.status, url)
                return []
            text = (await r.text(errors='replace')).strip()
    except Exception as e:
        log.debug('Fetch error  %s  %s', url, e)
        return []

    # Если в первых строках нет URI-схемы — пробуем base64
    sample = '\n'.join(text.splitlines()[:5])
    if not any(p in sample for p in _PROTO_PREFIXES):
        decoded = _b64dec(text.replace('\n', '').replace('\r', ''))
        if decoded and any(p in decoded for p in _PROTO_PREFIXES):
            text = decoded

    results = []
    for line in text.splitlines():
        line = line.strip()
        if any(line.startswith(p) for p in _PROTO_PREFIXES):
            results.append(line.split('#')[0])  # fragment уже здесь
    return results

# ── TCP PROBE ─────────────────────────────────────────────────────────────────

async def _tcp_latency(host: str, port: int) -> Optional[float]:
    try:
        t0 = time.monotonic()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=TCP_TIMEOUT
        )
        ms = (time.monotonic() - t0) * 1000
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), timeout=1)
        except Exception:
            pass
        return round(ms, 1)
    except Exception:
        return None

# ── MAIN ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    t_start = time.monotonic()
    log.info('Sources: %d', len(SOURCES))

    # ── 1. Fetch all sources ──────────────────────────────────────────────────
    connector = aiohttp.TCPConnector(limit=MAX_FETCH_CONC, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        raw_batches = await asyncio.gather(
            *[_fetch(session, url) for url in SOURCES],
            return_exceptions=False,
        )

    raw_lines = [line for batch in raw_batches for line in batch]
    log.info('Raw lines collected: %d', len(raw_lines))

    # ── 2. Parse + dedup ──────────────────────────────────────────────────────
    seen: dict[str, Config] = {}
    invalid = 0
    for line in raw_lines:
        cfg = _parse_line(line)
        if cfg is None or not cfg.host or not (1 <= cfg.port <= 65535):
            invalid += 1
            continue
        k = cfg.key()
        if k not in seen:
            seen[k] = cfg

    unique = list(seen.values())
    log.info('Unique configs: %d  (invalid/dup discarded: %d)', len(unique), invalid)

    # ── 3. TCP latency test ───────────────────────────────────────────────────
    log.info('TCP probing %d endpoints (timeout=%ds, concurrency=%d)...',
             len(unique), TCP_TIMEOUT, MAX_TEST_CONC)
    sem = asyncio.Semaphore(MAX_TEST_CONC)

    async def _probe(cfg: Config) -> None:
        async with sem:
            cfg.latency = await _tcp_latency(cfg.host, cfg.port)

    await asyncio.gather(*[_probe(c) for c in unique])

    alive = [c for c in unique if c.latency is not None]
    dead  = len(unique) - len(alive)
    log.info('TCP alive: %d  dead: %d', len(alive), dead)

    # ── 4. Score + sort + slice ───────────────────────────────────────────────
    alive.sort(key=lambda c: c.score, reverse=True)
    final = alive[:TARGET_COUNT]

    # ── 5. Build output ───────────────────────────────────────────────────────
    ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    header = [
        '#profile-title: WhiteJ 100',
        '#profile-update-interval: 1',
        f'#announce: ⚡️ WhiteJ {len(final)} configs | {ts} ⚡️',
        '#profile-web-page-url: https://github.com/jasonevm/whitej',
        '',
    ]

    body = []
    for i, cfg in enumerate(final):
        flag, ctry = _country(cfg.host)
        proto  = cfg.protocol.upper()
        sec    = cfg.security.upper() or '—'
        sni    = cfg.sni or '—'
        lat    = f'{cfg.latency:.0f}ms' if cfg.latency else '?'
        name   = f'{flag} {ctry} | {proto} | {sec} | {sni} | {lat} | #{i+1}'
        body.append(f'{cfg.raw}#{name}')

    out = 'configs.txt'
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header + body) + '\n')

    # ── 6. Stats ──────────────────────────────────────────────────────────────
    proto_cnt:   dict[str, int] = {}
    sec_cnt:     dict[str, int] = {}
    country_cnt: dict[str, int] = {}
    for cfg in final:
        proto_cnt[cfg.protocol]                  = proto_cnt.get(cfg.protocol, 0) + 1
        sec_cnt[cfg.security or 'none']          = sec_cnt.get(cfg.security or 'none', 0) + 1
        _, ctry = _country(cfg.host)
        country_cnt[ctry]                        = country_cnt.get(ctry, 0) + 1

    top5 = sorted(country_cnt.items(), key=lambda x: -x[1])[:5]
    elapsed = time.monotonic() - t_start

    log.info('─' * 50)
    log.info('Saved → %s  (%d configs)', out, len(final))
    log.info('Protocol : %s', proto_cnt)
    log.info('Security : %s', sec_cnt)
    log.info('Top countries: %s', top5)
    log.info('Elapsed: %.1fs', elapsed)

if __name__ == '__main__':
    asyncio.run(main())
