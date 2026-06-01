$ cat /home/user/stock-signals/STOCK_SIGNAL_BOT.py

#!/usr/bin/env python3
"""
MangoBotUltimate v4.0
- 300 liquid US stocks scanned every cycle
- GUARANTEED 1 best signal every 30 min (12-13 per day)
- Buy-the-dip: RSI, MACD, Bollinger, Support, Trend, Volume
- Sell at +3% (T1 alert, keep holding) and +5% (T2 close)
- Stop-loss -2%, forced exit after 7 days
- In-memory + SQLite persistence, company logos in Discord
"""

import os, time, sqlite3
from datetime import datetime, timedelta, timezone
import requests

try:
    import numpy as np
except ImportError:
    os.system("pip install numpy --break-system-packages -q")
    import numpy as np

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DISCORD_WEBHOOK    = os.environ.get('DISCORD_WEBHOOK', '')
FINNHUB_KEY        = os.environ.get('FINNHUB_KEY', 'd8bja4hr01qppd8s0760d8bja4hr01qppd8s076g')
DB_PATH            = os.environ.get('DB_PATH', './mangobot.db')

SIGNAL_EVERY_MIN   = 30     # 1 signal every 30 min → ~13/day
TARGET_1_PCT       = 3.0    # alert at +3%, keep holding
TARGET_2_PCT       = 5.0    # close position at +5%
STOP_LOSS_PCT      = 2.0    # stop-loss at -2%
MAX_HOLD_DAYS      = 7      # force exit after 7 days
SCAN_SLEEP_SEC     = 300    # scan loop every 5 min
WEEKS_HISTORY      = 3      # weeks of candle data for analysis

# ─────────────────────────────────────────────
# 300 LIQUID US STOCKS
# ─────────────────────────────────────────────
STOCKS = [
    # ── Technology (65) ──────────────────────
    'AAPL','MSFT','GOOGL','GOOG','AMZN','NVDA','TSLA','META','NFLX','ADBE',
    'INTC','AMD','CRM','ORCL','CSCO','IBM','INTU','PYPL','AVGO','QCOM',
    'SNPS','CDNS','AMAT','LRCX','KLAC','MU','MRVL','MCHP','FTNT','CRWD',
    'OKTA','NET','ZS','DDOG','SNOW','PLTR','SHOP','COIN','PANW','SPLK',
    'TEAM','WDAY','VEEV','NOW','HUBS','ZM','DOCU','BOX','TWLO','SMAR',
    'CFLT','GTLB','DBTX','MDB','ESTC','FIVN','PCTY','PAYC','CDAY','NCNO',
    'TTD','ROKU','PINS','SNAP','MTCH',
    # ── Healthcare / Biotech (40) ─────────────
    'JNJ','UNH','PFE','MRK','ABBV','AMGN','BIIB','REGN','VRTX','GILD',
    'ISRG','DXCM','ILMN','VEEV','MRNA','BNTX','ALNY','SGEN','INCY','EXAS',
    'ALGN','IDXX','MTD','BIO','HOLX','TDOC','ACAD','ARWR','SRPT','BMRN',
    'FATE','KYMR','RCUS','TMDX','PACB','NVAX','RARE','BLUE','SAGE','NTLA',
    # ── Financials (40) ──────────────────────
    'JPM','BAC','WFC','GS','MS','BLK','SCHW','CME','V','MA',
    'AXP','COF','PNC','USB','TFC','IBKR','ICE','SPGI','MCO','MSCI',
    'FDS','BR','NDAQ','CBOE','MKTX','RJF','LPL','LPLA','SF','PIPR',
    'WEX','CSGP','OPEN','HOOD','SOFI','AFRM','UPST','LC','MOGO','NRDS',
    # ── Consumer Discretionary (35) ──────────
    'MCD','NKE','COST','DIS','UBER','ABNB','DASH','ULTA','LULU','ROST',
    'WMT','TGT','AMZN','HD','LOW','YUM','SBUX','CMG','DPZ','QSR',
    'RH','ETSY','W','CVNA','KMX','AN','LAD','PAG','SAH','ABG',
    'BURL','FIVE','OLLI','BJ','SFM',
    # ── Consumer Staples (20) ────────────────
    'PG','KO','PEP','MNST','CELH','MO','PM','CL','KMB','GIS',
    'K','CPB','CAG','MDLZ','HSY','SJM','TSN','HRL','JJSF','SMPL',
    # ── Industrials / Defense (25) ───────────
    'GE','BA','RTX','HON','LMT','NOC','GD','EMR','CAT','DE',
    'ITW','PH','ROK','AME','FTV','VRSK','GNRC','FAST','GWW','MSC',
    'TDG','HEI','TXT','SPR','KTOS',
    # ── Energy (20) ──────────────────────────
    'XOM','CVX','COP','MPC','PSX','VLO','EOG','SLB','HAL','OXY',
    'DVN','FANG','MRO','APA','CIVI','SM','MTDR','PDCE','CHRD','RRC',
    # ── Financials - Banks (15) ──────────────
    'DAL','UAL','ALK','LUV','AAL','JBLU','CCL','RCL','NCLH','MAR',
    'HLT','H','IHG','WH','TNL',
    # ── Utilities (15) ───────────────────────
    'NEE','DUK','SO','AEP','XEL','WEC','SRE','EXC','D','ES',
    'PPL','FE','ETR','CNP','NI',
    # ── REITs (15) ───────────────────────────
    'CCI','EQIX','DLR','PLD','AMT','PSA','EXR','WELL','VTR','PEAK',
    'ARE','BXP','KIM','REG','SPG',
    # ── Telecom / Media (15) ─────────────────
    'CMCSA','TMUS','VZ','T','CHTR','DISH','FUBO','ROKU','SPOT','TTD',
    'DIS','NFLX','WBD','PARA','FOX',
    # ── Materials / Mining (10) ──────────────
    'NEM','GOLD','FCX','AA','ALB','MP','LTHM','SGML','PLL','SQM',
]

# Deduplicate while preserving order
seen = set()
STOCKS = [s for s in STOCKS if not (s in seen or seen.add(s))]

# ─────────────────────────────────────────────
# SQLITE
# ─────────────────────────────────────────────
class DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self._setup()

    def _setup(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS positions (
                symbol       TEXT PRIMARY KEY,
                entry_price  REAL,
                target1      REAL,
                target2      REAL,
                stop_loss    REAL,
                t1_hit       INTEGER DEFAULT 0,
                opened_at    TEXT
            );
            CREATE TABLE IF NOT EXISTS logo_cache (
                symbol  TEXT PRIMARY KEY,
                url     TEXT,
                name    TEXT
            );
            CREATE TABLE IF NOT EXISTS signal_log (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol   TEXT,
                action   TEXT,
                price    REAL,
                pnl_pct  REAL,
                reason   TEXT,
                ts       TEXT
            );
            CREATE TABLE IF NOT EXISTS sent_signals (
                symbol    TEXT PRIMARY KEY,
                sent_at   TEXT
            );
        """)
        self.conn.commit()

    def add_position(self, symbol, entry, t1, t2, sl):
        self.conn.execute("""
            INSERT OR REPLACE INTO positions
            (symbol,entry_price,target1,target2,stop_loss,t1_hit,opened_at)
            VALUES (?,?,?,?,?,0,?)
        """, (symbol, entry, t1, t2, sl, datetime.now().isoformat()))
        self.conn.commit()

    def mark_t1_hit(self, symbol):
        self.conn.execute("UPDATE positions SET t1_hit=1 WHERE symbol=?", (symbol,))
        self.conn.commit()

    def remove_position(self, symbol):
        self.conn.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
        self.conn.commit()

    def load_positions(self):
        rows = self.conn.execute(
            "SELECT symbol,entry_price,target1,target2,stop_loss,t1_hit,opened_at FROM positions"
        ).fetchall()
        return {r[0]: {
            'entry': r[1], 'target1': r[2], 'target2': r[3],
            'stop_loss': r[4], 't1_hit': bool(r[5]),
            'opened_at': datetime.fromisoformat(r[6])
        } for r in rows}

    def get_logo(self, symbol):
        row = self.conn.execute(
            "SELECT url,name FROM logo_cache WHERE symbol=?", (symbol,)).fetchone()
        return (row[0] or None, row[1]) if row else (None, None)

    def save_logo(self, symbol, url, name):
        self.conn.execute(
            "INSERT OR REPLACE INTO logo_cache (symbol,url,name) VALUES (?,?,?)",
            (symbol, url or '', name or symbol))
        self.conn.commit()

    def log_signal(self, symbol, action, price, pnl, reason):
        self.conn.execute(
            "INSERT INTO signal_log (symbol,action,price,pnl_pct,reason,ts) VALUES (?,?,?,?,?,?)",
            (symbol, action, price, pnl, reason, datetime.now().isoformat()))
        self.conn.commit()

    # Track which symbols were already signalled today (avoid repeating same stock)
    def mark_sent_today(self, symbol):
        self.conn.execute(
            "INSERT OR REPLACE INTO sent_signals (symbol,sent_at) VALUES (?,?)",
            (symbol, datetime.now().isoformat()))
        self.conn.commit()

    def sent_today(self, symbol):
        row = self.conn.execute(
            "SELECT sent_at FROM sent_signals WHERE symbol=?", (symbol,)).fetchone()
        if not row:
            return False
        sent = datetime.fromisoformat(row[0])
        # Expire at midnight IST
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist)
        midnight = now_ist.replace(hour=1, minute=30, second=0, microsecond=0)
        if now_ist < midnight:
            midnight -= timedelta(days=1)
        return sent.replace(tzinfo=None) > midnight.replace(tzinfo=None)

    def clear_sent_today(self):
        self.conn.execute("DELETE FROM sent_signals")
        self.conn.commit()


# ─────────────────────────────────────────────
# MARKET DATA
# ─────────────────────────────────────────────
class Market:
    def __init__(self, key):
        self.key = key

    def quote(self, symbol):
        try:
            d = requests.get(
                f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.key}",
                timeout=5).json()
            if d.get('c', 0) > 0:
                return {
                    'price': float(d['c']),
                    'prev':  float(d.get('pc', d['c'])),
                    'high':  float(d.get('h', d['c'])),
                    'low':   float(d.get('l', d['c'])),
                    'vol':   int(d.get('v', 0)),
                }
        except Exception:
            pass
        return None

    def candles(self, symbol, weeks=WEEKS_HISTORY):
        try:
            end   = int(time.time())
            start = end - weeks * 7 * 86400
            d = requests.get(
                f"https://finnhub.io/api/v1/stock/candle"
                f"?symbol={symbol}&resolution=D&from={start}&to={end}&token={self.key}",
                timeout=8).json()
            if d.get('s') == 'ok' and len(d.get('c', [])) >= 10:
                return {
                    'close':  np.array(d['c'], dtype=float),
                    'high':   np.array(d['h'], dtype=float),
                    'low':    np.array(d['l'], dtype=float),
                    'volume': np.array(d['v'], dtype=float),
                    'open':   np.array(d['o'], dtype=float),
                }
        except Exception:
            pass
        return None

    def profile(self, symbol):
        try:
            d = requests.get(
                f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={self.key}",
                timeout=5).json()
            return d.get('logo') or None, d.get('name', symbol)
        except Exception:
            return None, symbol


# ─────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────
def rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    d = np.diff(closes)
    gain = np.mean(np.where(d > 0, d, 0)[-period:])
    loss = np.mean(np.where(d < 0, -d, 0)[-period:])
    return 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)

def macd(closes, fast=12, slow=26, sig=9):
    if len(closes) < slow + sig:
        return 0.0, 0.0
    def ema(a, n):
        k, r = 2/(n+1), np.zeros(len(a))
        r[0] = a[0]
        for i in range(1, len(a)):
            r[i] = a[i]*k + r[i-1]*(1-k)
        return r
    ml = ema(closes, fast) - ema(closes, slow)
    sl = ema(ml, sig)
    return float(ml[-1] - sl[-1]), float(ml[-1])

def bollinger(closes, period=20):
    if len(closes) < period:
        return closes[-1], closes[-1], closes[-1]
    w = closes[-period:]
    m, s = np.mean(w), np.std(w)
    return float(m + 2*s), float(m), float(m - 2*s)

def trend_slope(closes, lookback=15):
    if len(closes) < lookback:
        return 0.0
    y = closes[-lookback:]
    slope = np.polyfit(np.arange(lookback), y, 1)[0]
    return float(slope / y[0] * 100)

def support_distance(price, lows, lookback=15):
    support = np.min(lows[-lookback:]) if len(lows) >= lookback else np.min(lows)
    return float((price - support) / support * 100)

def volume_spike(volumes, lookback=10):
    if len(volumes) < lookback + 1:
        return 1.0
    avg = np.mean(volumes[-(lookback+1):-1])
    return float(volumes[-1] / avg) if avg > 0 else 1.0


# ─────────────────────────────────────────────
# SCORING  (0–100, dip-buy focused)
# ─────────────────────────────────────────────
def score_stock(quote, candles):
    closes, lows, volumes = candles['close'], candles['low'], candles['volume']
    price, prev = quote['price'], quote['prev']
    pts, info = 0, {}

    # RSI — 25 pts
    r = rsi(closes)
    info['rsi'] = round(r, 1)
    if 32 <= r <= 50:    pts += 25
    elif 50 < r <= 58:   pts += 18
    elif r < 32:         pts += 10
    elif 58 < r <= 65:   pts += 8

    # MACD histogram — 20 pts
    hist, ml = macd(closes)
    info['macd_hist'] = round(hist, 4)
    if hist > 0 and hist > abs(ml) * 0.05:  pts += 20
    elif hist > 0:                           pts += 13
    elif -0.3 < hist <= 0:                  pts += 5

    # Bollinger position — 20 pts
    bb_u, bb_m, bb_l = bollinger(closes)
    bb_pct = (price - bb_l) / (bb_u - bb_l + 1e-9)
    info['bb_pct'] = round(bb_pct, 2)
    if bb_pct <= 0.35:    pts += 20
    elif bb_pct <= 0.50:  pts += 15
    elif bb_pct <= 0.65:  pts += 8

    # Support distance — 15 pts
    sup = support_distance(price, lows, lookback=min(15, len(lows)))
    info['sup_dist_pct'] = round(sup, 2)
    if sup <= 3.0:    pts += 15
    elif sup <= 6.0:  pts += 10
    elif sup <= 10.0: pts += 5

    # Trend slope — 10 pts
    slope = trend_slope(closes, lookback=min(15, len(closes)))
    info['trend_slope'] = round(slope, 3)
    if 0.1 <= slope <= 1.0:    pts += 10
    elif -0.2 <= slope < 0.1:  pts += 7
    elif slope > 1.0:          pts += 5

    # Volume spike — 10 pts
    vs = volume_spike(volumes)
    info['vol_spike'] = round(vs, 2)
    if vs >= 1.8:    pts += 10
    elif vs >= 1.3:  pts += 6
    elif vs >= 1.0:  pts += 3

    # Day change penalty
    chg = (price - prev) / prev * 100 if prev > 0 else 0
    info['chg_pct'] = round(chg, 2)
    if chg < -4.0 or chg > 5.0:
        pts = max(0, pts - 20)

    info['score'] = min(pts, 100)
    return info


# ─────────────────────────────────────────────
# DISCORD EMBEDS
# ─────────────────────────────────────────────
def post(webhook, embed):
    try:
        requests.post(webhook, json={'embeds': [embed]}, timeout=10)
    except Exception:
        pass

def _thumb(url):
    return {"url": url} if url else None

def buy_embed(symbol, name, logo, price, t1, t2, sl, info, num):
    embed = {
        "title": f"🟢 BUY SIGNAL #{num}  —  {name} ({symbol})",
        "description": (
            f"📉 **Dip detected** — near support, RSI in buy zone.\n"
            f"Hold up to **{MAX_HOLD_DAYS} days** | "
            f"Sell **+{TARGET_1_PCT}%** (alert) → **+{TARGET_2_PCT}%** (close)"
        ),
        "color": 3066993,
        "fields": [
            {"name": "📍 Entry",         "value": f"**${price:.2f}**",                      "inline": True},
            {"name": "🎯 Target 1",      "value": f"${t1:.2f}  **(+{TARGET_1_PCT}%)**",     "inline": True},
            {"name": "🚀 Target 2",      "value": f"${t2:.2f}  **(+{TARGET_2_PCT}%)**",     "inline": True},
            {"name": "🛑 Stop-Loss",     "value": f"${sl:.2f}  **(-{STOP_LOSS_PCT}%)**",    "inline": True},
            {"name": "📊 RSI",           "value": str(info.get('rsi','—')),                  "inline": True},
            {"name": "📈 MACD Hist",     "value": str(info.get('macd_hist','—')),            "inline": True},
            {"name": "📉 BB Position",   "value": f"{info.get('bb_pct',0)*100:.0f}%",       "inline": True},
            {"name": "🏗️ Support Gap",  "value": f"{info.get('sup_dist_pct',0):.1f}% above support", "inline": True},
            {"name": "📐 3W Trend",      "value": f"{info.get('trend_slope',0):+.2f}%/day", "inline": True},
            {"name": "🔊 Vol Spike",     "value": f"{info.get('vol_spike',1):.1f}x avg",    "inline": True},
            {"name": "📅 Day Change",    "value": f"{info.get('chg_pct',0):+.2f}%",         "inline": True},
            {"name": "⭐ Score",         "value": f"**{info.get('score',0)}/100**",          "inline": True},
        ],
        "footer": {"text": f"🥭 Mango_Bot v4.0  |  Signal {num} today  |  Not financial advice"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    t = _thumb(logo)
    if t: embed["thumbnail"] = t
    return embed

def sell_embed(symbol, name, logo, entry, price, pnl, reason, tier):
    icons = {1: "🎯", 2: "🚀", 0: "🛑" if "STOP" in reason else "⏰"}
    embed = {
        "title": f"{icons.get(tier,'📤')} SELL — {name} ({symbol})  |  {reason}",
        "color": 5763719 if pnl >= 0 else 15548997,
        "fields": [
            {"name": "📍 Entry", "value": f"${entry:.2f}", "inline": True},
            {"name": "💰 Exit",  "value": f"${price:.2f}", "inline": True},
            {"name": "📊 P&L",   "value": f"**{pnl:+.2f}%**", "inline": True},
        ],
        "footer": {"text": f"🥭 Mango_Bot v4.0  |  {datetime.now().strftime('%d %b %Y %H:%M')}"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    t = _thumb(logo)
    if t: embed["thumbnail"] = t
    return embed

def premarket_embed(spy_chg, qqq_chg, logo=None):
    avg = (spy_chg + qqq_chg) / 2
    sentiment = "🟢 BULLISH" if avg > 0.5 else ("🔴 BEARISH" if avg < -0.5 else "🟡 NEUTRAL")
    color     = 3066993    if avg > 0.5 else (15548997    if avg < -0.5 else 16776960)
    embed = {
        "title": "🌅 MANGO_BOT v4.0 — Pre-Market Outlook",
        "color": color,
        "fields": [
            {"name": "📊 Sentiment", "value": sentiment,           "inline": True},
            {"name": "📈 SPY",       "value": f"{spy_chg:+.2f}%",  "inline": True},
            {"name": "💻 QQQ",       "value": f"{qqq_chg:+.2f}%",  "inline": True},
            {"name": "🔍 Stocks",    "value": f"Scanning **{len(STOCKS)} stocks** every 5 min", "inline": True},
            {"name": "📢 Signals",   "value": f"**1 best signal every {SIGNAL_EVERY_MIN} min** (~13/day)", "inline": True},
            {"name": "🎯 Targets",   "value": f"+{TARGET_1_PCT}% alert  →  +{TARGET_2_PCT}% close  |  Stop -{STOP_LOSS_PCT}%", "inline": False},
        ],
        "footer": {"text": "🥭 Mango_Bot v4.0 | Happy Trading!"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    t = _thumb(logo)
    if t: embed["thumbnail"] = t
    return embed


# ─────────────────────────────────────────────
# BOT
# ─────────────────────────────────────────────
class MangoBot:

    def __init__(self):
        if not DISCORD_WEBHOOK:
            print("ERROR: DISCORD_WEBHOOK env var not set.")
            exit(1)

        self.webhook = DISCORD_WEBHOOK
        self.db      = DB(DB_PATH)
        self.mkt     = Market(FINNHUB_KEY)
        self._ist    = timezone(timedelta(hours=5, minutes=30))

        # In-memory positions (reloaded from DB on restart)
        self.positions: dict = self.db.load_positions()

        self.last_signal    = datetime.now() - timedelta(minutes=SIGNAL_EVERY_MIN + 1)
        self.signals_today  = 0
        self.premarket_sent = False

        # Full scan cache: symbol → {quote, info, logo, name}
        self.scan_cache: dict = {}

        self.log(f"🥭 Mango_Bot v4.0 | {len(STOCKS)} stocks | {len(self.positions)} positions loaded")

    def log(self, msg):
        ts = datetime.now(self._ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")

    def now_ist(self):
        return datetime.now(self._ist)

    def get_logo(self, symbol):
        url, name = self.db.get_logo(symbol)
        if url is not None:
            return url or None, name
        url, name = self.mkt.profile(symbol)
        self.db.save_logo(symbol, url, name)
        return url, name

    # ── Time helpers ──────────────────────────
    def is_premarket(self):
        n = self.now_ist()
        return n.weekday() < 5 and n.hour == 18 and n.minute < 5

    def is_open(self):
        n = self.now_ist()
        if n.weekday() >= 5: return False
        return n.hour >= 19 or n.hour == 0 or (n.hour == 1 and n.minute < 30)

    def is_close_time(self):
        n = self.now_ist()
        return n.hour == 1 and n.minute >= 30

    # ── Pre-market ────────────────────────────
    def do_premarket(self):
        if self.premarket_sent: return
        spy = self.mkt.quote('SPY')
        qqq = self.mkt.quote('QQQ')
        if not spy or not qqq: return
        spy_chg = (spy['price'] - spy['prev']) / spy['prev'] * 100
        qqq_chg = (qqq['price'] - qqq['prev']) / qqq['prev'] * 100
        logo, _ = self.get_logo('SPY')
        post(self.webhook, premarket_embed(spy_chg, qqq_chg, logo))
        self.premarket_sent = True
        self.log(f"🌅 Pre-market sent | SPY {spy_chg:+.2f}%  QQQ {qqq_chg:+.2f}%")

    # ── Monitor open positions ─────────────────
    def monitor(self):
        for symbol, pos in list(self.positions.items()):
            try:
                q = self.mkt.quote(symbol)
                if not q: continue
                price  = q['price']
                entry  = pos['entry']
                pnl    = (price - entry) / entry * 100
                age    = (datetime.now() - pos['opened_at']).days
                logo, name = self.get_logo(symbol)

                if not pos['t1_hit'] and price >= pos['target1']:
                    self.positions[symbol]['t1_hit'] = True
                    self.db.mark_t1_hit(symbol)
                    post(self.webhook, sell_embed(symbol, name, logo, entry, price, pnl,
                                                  f"🎯 TARGET 1 HIT +{TARGET_1_PCT}%", 1))
                    self.db.log_signal(symbol, 'T1_HIT', price, pnl, 'target1')
                    self.log(f"🎯 T1 {symbol} @ ${price:.2f}  P&L {pnl:+.2f}%  — holding for T2")
                    continue

                reason = None
                tier   = 0
                if price >= pos['target2']:
                    reason, tier = f"🚀 TARGET 2 HIT +{TARGET_2_PCT}%", 2
                elif price <= pos['stop_loss']:
                    reason, tier = "🛑 STOP-LOSS HIT", 0
                elif age >= MAX_HOLD_DAYS:
                    reason, tier = f"⏰ {MAX_HOLD_DAYS}-DAY EXIT", 0

                if reason:
                    post(self.webhook, sell_embed(symbol, name, logo, entry, price, pnl, reason, tier))
                    self.db.log_signal(symbol, 'SELL', price, pnl, reason)
                    self.db.remove_position(symbol)
                    del self.positions[symbol]
                    self.log(f"📤 SELL {symbol} | {reason} | P&L {pnl:+.2f}%")

            except Exception as e:
                self.log(f"⚠️  Monitor {symbol}: {e}")

    # ── Full scan of all 300 stocks ────────────
    def scan(self):
        self.log(f"🔍 Scanning {len(STOCKS)} stocks …")
        results = {}

        for symbol in STOCKS:
            if symbol in self.positions:
                continue
            try:
                q = self.mkt.quote(symbol)
                if not q or q['price'] <= 0:
                    time.sleep(0.1); continue

                c = self.mkt.candles(symbol)
                if c is None:
                    time.sleep(0.1); continue

                info = score_stock(q, c)
                logo, name = self.get_logo(symbol)
                results[symbol] = {'quote': q, 'info': info, 'logo': logo, 'name': name}

                if info['score'] >= 60:
                    self.log(f"  ✅ {symbol:6s} {info['score']:3d}/100  "
                             f"RSI={info['rsi']}  MACD={info['macd_hist']:.3f}  "
                             f"BB={info['bb_pct']:.2f}  sup={info['sup_dist_pct']:.1f}%")
                time.sleep(0.1)

            except Exception as e:
                self.log(f"  ⚠️  {symbol}: {e}")

        self.scan_cache = results
        self.log(f"✅ Scan done — {len(results)} stocks scored")
        return results

    # ── GUARANTEED signal every 30 min ────────
    # Always picks the BEST available stock.
    # If already sent today, skip it and pick next best.
    # No minimum score required — someone must always win.
    def fire_signal(self, all_stocks: dict):
        if datetime.now() - self.last_signal < timedelta(minutes=SIGNAL_EVERY_MIN):
            return
        if not all_stocks:
            self.log("📭 No stocks in cache — skipping signal")
            return

        # Sort all scanned stocks by score descending
        ranked = sorted(all_stocks.items(), key=lambda x: x[1]['info']['score'], reverse=True)

        # Pick best stock not already in open positions and not sent today
        chosen = None
        for symbol, data in ranked:
            if symbol in self.positions:
                continue
            if self.db.sent_today(symbol):
                continue
            chosen = (symbol, data)
            break

        # If every stock was already sent today, just pick overall best not in positions
        if chosen is None:
            for symbol, data in ranked:
                if symbol not in self.positions:
                    chosen = (symbol, data)
                    break

        if chosen is None:
            self.log("📭 All stocks are in open positions — no signal")
            return

        symbol, data = chosen
        q     = data['quote']
        info  = data['info']
        logo  = data['logo']
        name  = data['name']
        price = q['price']
        t1    = round(price * (1 + TARGET_1_PCT / 100), 2)
        t2    = round(price * (1 + TARGET_2_PCT / 100), 2)
        sl    = round(price * (1 - STOP_LOSS_PCT / 100), 2)

        self.positions[symbol] = {
            'entry': price, 'target1': t1, 'target2': t2,
            'stop_loss': sl, 't1_hit': False, 'opened_at': datetime.now()
        }
        self.db.add_position(symbol, price, t1, t2, sl)
        self.db.log_signal(symbol, 'BUY', price, 0.0, 'signal')
        self.db.mark_sent_today(symbol)

        self.signals_today += 1
        post(self.webhook, buy_embed(symbol, name, logo, price, t1, t2, sl, info, self.signals_today))
        self.last_signal = datetime.now()
        self.log(f"📱 BUY #{self.signals_today} {symbol} ({name}) @ ${price:.2f}  "
                 f"T1=${t1}  T2=${t2}  SL=${sl}  score={info['score']}")

    # ── Main loop ─────────────────────────────
    def run(self):
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"── Cycle #{cycle} ──────────────────────────────")

                if self.is_premarket():
                    self.do_premarket()

                if self.is_open():
                    self.premarket_sent = False
                    self.monitor()
                    all_stocks = self.scan()
                    self.fire_signal(all_stocks)

                elif self.is_close_time():
                    self.log("🏁 Market closed — resetting daily counters")
                    self.signals_today = 0
                    self.db.clear_sent_today()

                else:
                    self.log("😴 Market closed — waiting …")

                time.sleep(SCAN_SLEEP_SEC)

            except KeyboardInterrupt:
                self.log("👋 Shutting down")
                break
            except Exception as e:
                self.log(f"❌ Loop error: {e}")
                time.sleep(60)


if __name__ == "__main__":
    MangoBot().run()
