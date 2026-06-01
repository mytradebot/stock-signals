#!/usr/bin/env python3
"""
MangoBotUltimate v3.0
- Buys dips, sells at +3% or +5% highs
- Holds positions 1-7 days in memory + SQLite
- Analyzes 3 weeks of historical data per stock
- Sends best signal to Discord every 30 minutes
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
# CONFIG  (override via environment variables)
# ─────────────────────────────────────────────
DISCORD_WEBHOOK     = os.environ.get('DISCORD_WEBHOOK', '')
FINNHUB_KEY         = os.environ.get('FINNHUB_KEY', 'd8bja4hr01qppd8s0760d8bja4hr01qppd8s076g')
DB_PATH             = os.environ.get('DB_PATH', './mangobot.db')

SIGNAL_EVERY_MIN    = 30       # send best signal every 30 minutes
TARGET_1_PCT        = 3.0      # first sell target  (+3%)
TARGET_2_PCT        = 5.0      # second sell target (+5%)
STOP_LOSS_PCT       = 2.0      # stop-loss          (-2%)
MAX_HOLD_DAYS       = 7        # force exit after 7 days
MIN_SCORE           = 60       # minimum score to qualify
SCAN_SLEEP_SEC      = 300      # how often to run the main loop
WEEKS_HISTORY       = 3        # weeks of candle history to analyze

# ─────────────────────────────────────────────
# STOCK LIST  (~130 liquid US tickers)
# ─────────────────────────────────────────────
STOCKS = [
    # Technology
    'AAPL','MSFT','GOOGL','AMZN','NVDA','TSLA','META','NFLX','ADBE','INTC',
    'AMD','CRM','ORCL','CSCO','IBM','INTU','PYPL','AVGO','QCOM','SNPS',
    'CDNS','AMAT','LRCX','KLAC','MU','MRVL','MCHP','FTNT','CRWD','OKTA',
    'NET','ZS','DDOG','SNOW','PLTR','SHOP','COIN',
    # Healthcare / Biotech
    'JNJ','UNH','PFE','MRK','ABBV','AMGN','BIIB','REGN','VRTX','GILD',
    'ISRG','DXCM','ILMN','VEEV','MRNA','BNTX',
    # Financials
    'JPM','BAC','WFC','GS','MS','BLK','SCHW','CME','V','MA',
    'AXP','COF','PNC','USB','TFC','IBKR',
    # Consumer
    'MCD','NKE','COST','DIS','UBER','ABNB','DASH','PINS','ULTA','LULU',
    'ROST','WMT','PG','KO','PEP','MNST','CELH','YUM','CCL','RCL','DAL','UAL',
    # Industrials / Defense
    'GE','BA','RTX','HON','LMT','NOC','GD','EMR','CAT','DE',
    # Energy
    'XOM','CVX','COP','MPC','PSX','VLO','EOG','SLB','HAL','OXY','DVN',
    # Utilities
    'NEE','DUK','SO','AEP','XEL','WEC','SRE',
    # REITs
    'CCI','EQIX','DLR','PLD','AMT','PSA','EXR',
    # Telecom / Media
    'CMCSA','TMUS','VZ','T','ROKU','SPOT',
    # Materials
    'NEM','GOLD','FCX',
]

# ─────────────────────────────────────────────
# SQLITE  (persistence across restarts)
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
        """)
        self.conn.commit()

    # ── positions ──────────────────────────────
    def add_position(self, symbol, entry, t1, t2, sl):
        self.conn.execute("""
            INSERT OR REPLACE INTO positions
            (symbol, entry_price, target1, target2, stop_loss, t1_hit, opened_at)
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

    # ── logo cache ─────────────────────────────
    def get_logo(self, symbol):
        row = self.conn.execute(
            "SELECT url, name FROM logo_cache WHERE symbol=?", (symbol,)).fetchone()
        return (row[0] or None, row[1]) if row else (None, None)

    def save_logo(self, symbol, url, name):
        self.conn.execute(
            "INSERT OR REPLACE INTO logo_cache (symbol,url,name) VALUES (?,?,?)",
            (symbol, url or '', name or symbol))
        self.conn.commit()

    # ── signal log ─────────────────────────────
    def log(self, symbol, action, price, pnl, reason):
        self.conn.execute("""
            INSERT INTO signal_log (symbol,action,price,pnl_pct,reason,ts)
            VALUES (?,?,?,?,?,?)
        """, (symbol, action, price, pnl, reason, datetime.now().isoformat()))
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
        """Fetch `weeks` weeks of daily OHLCV candles."""
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
        """Returns (logo_url, company_name)."""
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
    ml  = ema(closes, fast) - ema(closes, slow)
    sl  = ema(ml, sig)
    return float(ml[-1] - sl[-1]), float(ml[-1])   # histogram, macd_line

def bollinger(closes, period=20):
    if len(closes) < period:
        return closes[-1], closes[-1], closes[-1]
    w = closes[-period:]
    m = np.mean(w); s = np.std(w)
    return float(m + 2*s), float(m), float(m - 2*s)

def atr(high, low, close, period=14):
    """Average True Range — measures volatility."""
    if len(close) < period + 1:
        return 0.0
    tr = np.maximum(high[1:]-low[1:],
         np.maximum(abs(high[1:]-close[:-1]),
                    abs(low[1:]-close[:-1])))
    return float(np.mean(tr[-period:]))

def trend_slope(closes, lookback=10):
    """Linear regression slope of last `lookback` closes, normalised by price."""
    if len(closes) < lookback:
        return 0.0
    y = closes[-lookback:]
    x = np.arange(lookback)
    slope = np.polyfit(x, y, 1)[0]
    return float(slope / y[0] * 100)   # % per day

def support_distance(close_now, lows, lookback=15):
    """How far above the recent support level the price is (lower = dip)."""
    support = np.min(lows[-lookback:]) if len(lows) >= lookback else np.min(lows)
    return float((close_now - support) / support * 100)

def volume_spike(volumes, lookback=10):
    if len(volumes) < lookback + 1:
        return 1.0
    avg = np.mean(volumes[-(lookback+1):-1])
    return float(volumes[-1] / avg) if avg > 0 else 1.0


# ─────────────────────────────────────────────
# COMPOSITE SCORE  (0 – 100)
# ─────────────────────────────────────────────
# Uses 3 weeks of data to find stocks that:
#   • Are near a support level (dip)
#   • Have RSI in buy zone (35-55)
#   • MACD histogram turning positive (momentum shift)
#   • Below Bollinger mid-band (room to run)
#   • Gentle upward trend over 3 weeks
#   • Volume picking up
# ─────────────────────────────────────────────
def score(quote, candles):
    closes  = candles['close']
    highs   = candles['high']
    lows    = candles['low']
    volumes = candles['volume']
    price   = quote['price']
    prev    = quote['prev']

    pts = 0
    info = {}

    # 1. RSI  (25 pts) — want 32–55 for dip-buy zone
    r = rsi(closes)
    info['rsi'] = round(r, 1)
    if 32 <= r <= 50:   pts += 25   # sweet spot: oversold but recovering
    elif 50 < r <= 58:  pts += 18
    elif r < 32:        pts += 10   # very oversold, risky
    elif 58 < r <= 65:  pts += 8

    # 2. MACD histogram  (20 pts) — want histogram crossing above zero
    hist, ml = macd(closes)
    info['macd_hist'] = round(hist, 4)
    if hist > 0 and hist > abs(ml) * 0.05:   pts += 20  # strong bullish cross
    elif hist > 0:                            pts += 13
    elif -0.3 < hist <= 0:                   pts += 5   # about to cross

    # 3. Bollinger position  (20 pts) — below mid = dip
    bb_u, bb_m, bb_l = bollinger(closes)
    bb_pct = (price - bb_l) / (bb_u - bb_l + 1e-9)
    info['bb_pct'] = round(bb_pct, 2)
    if bb_pct <= 0.35:   pts += 20   # price near/below lower band = clear dip
    elif bb_pct <= 0.50: pts += 15   # below mid
    elif bb_pct <= 0.65: pts += 8

    # 4. Support distance  (15 pts) — close to 3-week support = dip
    sup_dist = support_distance(price, lows, lookback=min(15, len(lows)))
    info['sup_dist_pct'] = round(sup_dist, 2)
    if sup_dist <= 3.0:    pts += 15  # very close to support
    elif sup_dist <= 6.0:  pts += 10
    elif sup_dist <= 10.0: pts += 5

    # 5. Trend slope over 3 weeks  (10 pts) — gentle uptrend preferred
    slope = trend_slope(closes, lookback=min(15, len(closes)))
    info['trend_slope'] = round(slope, 3)
    if 0.1 <= slope <= 1.0:   pts += 10   # steady uptrend
    elif slope > 1.0:         pts += 5    # steep — may be overextended
    elif -0.2 <= slope < 0.1: pts += 7    # flat/mild dip = good dip-buy

    # 6. Volume spike  (10 pts) — unusual volume on a dip = accumulation
    vs = volume_spike(volumes)
    info['vol_spike'] = round(vs, 2)
    if vs >= 1.8:   pts += 10
    elif vs >= 1.3: pts += 6
    elif vs >= 1.0: pts += 3

    # Day change filter — avoid stocks in freefall (< -4%) or already surged (> +5%)
    chg = (price - prev) / prev * 100 if prev > 0 else 0
    info['chg_pct'] = round(chg, 2)
    if chg < -4.0 or chg > 5.0:
        pts = max(0, pts - 20)   # heavy penalty

    info['score'] = min(pts, 100)
    return info


# ─────────────────────────────────────────────
# DISCORD HELPERS
# ─────────────────────────────────────────────
def post(webhook, embed):
    try:
        requests.post(webhook, json={'embeds': [embed]}, timeout=10)
    except Exception:
        pass

def _thumb(url):
    return {"url": url} if url else None

def make_buy_embed(symbol, name, logo, price, t1, t2, sl, info, signals_today):
    chg = info.get('chg_pct', 0)
    embed = {
        "title": f"🟢 BUY SIGNAL  {name} ({symbol})",
        "description": (
            f"📉 **Dip detected** — price near support, RSI in buy zone.\n"
            f"Hold up to **{MAX_HOLD_DAYS} days**. Sell at **+{TARGET_1_PCT}%** or **+{TARGET_2_PCT}%**."
        ),
        "color": 3066993,
        "fields": [
            {"name": "📍 Entry Price",  "value": f"**${price:.2f}**",                 "inline": True},
            {"name": "🎯 Target 1",     "value": f"${t1:.2f}  (+{TARGET_1_PCT}%)",    "inline": True},
            {"name": "🚀 Target 2",     "value": f"${t2:.2f}  (+{TARGET_2_PCT}%)",    "inline": True},
            {"name": "🛑 Stop-Loss",    "value": f"${sl:.2f}  (-{STOP_LOSS_PCT}%)",   "inline": True},
            {"name": "📊 RSI",          "value": str(info.get('rsi','—')),             "inline": True},
            {"name": "📈 MACD Hist",    "value": str(info.get('macd_hist','—')),       "inline": True},
            {"name": "📉 BB Position",  "value": f"{info.get('bb_pct',0)*100:.0f}%",  "inline": True},
            {"name": "🏗️ Support Gap", "value": f"{info.get('sup_dist_pct',0):.1f}% above support", "inline": True},
            {"name": "📐 3W Trend",     "value": f"{info.get('trend_slope',0):+.2f}%/day",           "inline": True},
            {"name": "🔊 Volume Spike", "value": f"{info.get('vol_spike',1):.1f}x avg",              "inline": True},
            {"name": "📅 Day Change",   "value": f"{chg:+.2f}%",                      "inline": True},
            {"name": "⭐ Score",        "value": f"**{info.get('score',0)}/100**",     "inline": True},
            {"name": "📢 Signals Today","value": str(signals_today),                  "inline": True},
        ],
        "footer": {"text": f"🥭 Mango_Bot v3.0 | {datetime.now().strftime('%d %b %Y %H:%M')} | Not financial advice"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    t = _thumb(logo)
    if t:
        embed["thumbnail"] = t
    return embed

def make_sell_embed(symbol, name, logo, entry, price, pnl, reason, target_hit):
    color = 5763719 if pnl >= 0 else 15548997
    if target_hit == 1:
        icon = "🎯"
    elif target_hit == 2:
        icon = "🚀"
    elif "STOP" in reason:
        icon = "🛑"
    else:
        icon = "⏰"
    embed = {
        "title": f"{icon} SELL — {name} ({symbol})  |  {reason}",
        "color": color,
        "fields": [
            {"name": "📍 Entry",  "value": f"${entry:.2f}", "inline": True},
            {"name": "💰 Exit",   "value": f"${price:.2f}", "inline": True},
            {"name": "📊 P&L",    "value": f"**{pnl:+.2f}%**", "inline": True},
        ],
        "footer": {"text": f"🥭 Mango_Bot v3.0 | {datetime.now().strftime('%d %b %Y %H:%M')}"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    t = _thumb(logo)
    if t:
        embed["thumbnail"] = t
    return embed

def make_premarket_embed(spy_chg, qqq_chg, spy_logo=None):
    avg = (spy_chg + qqq_chg) / 2
    if avg > 0.5:
        sentiment, color = "🟢 BULLISH", 3066993
    elif avg < -0.5:
        sentiment, color = "🔴 BEARISH", 15548997
    else:
        sentiment, color = "🟡 NEUTRAL", 16776960
    embed = {
        "title": "🌅 MANGO_BOT — Pre-Market Outlook",
        "color": color,
        "fields": [
            {"name": "📊 Sentiment", "value": sentiment,          "inline": True},
            {"name": "📈 SPY",       "value": f"{spy_chg:+.2f}%", "inline": True},
            {"name": "💻 QQQ",       "value": f"{qqq_chg:+.2f}%", "inline": True},
            {"name": "⚙️ Strategy",  "value": f"Buy-the-dip mode. Signals fire every {SIGNAL_EVERY_MIN} min. Score ≥ {MIN_SCORE} required.", "inline": False},
            {"name": "🎯 Targets",   "value": f"+{TARGET_1_PCT}% (T1)  →  +{TARGET_2_PCT}% (T2)  |  Stop: -{STOP_LOSS_PCT}%", "inline": False},
        ],
        "footer": {"text": "🥭 Mango_Bot v3.0 | Happy Trading!"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    t = _thumb(spy_logo)
    if t:
        embed["thumbnail"] = t
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

        # In-memory positions (loaded from DB on startup)
        self.positions: dict = self.db.load_positions()

        self.last_signal   = datetime.now() - timedelta(minutes=SIGNAL_EVERY_MIN + 1)
        self.signals_today = 0
        self.premarket_sent = False

        self.log(f"🥭 Mango_Bot v3.0 started | {len(self.positions)} open positions loaded")

    # ── Logging ──────────────────────────────
    def log(self, msg):
        ts = datetime.now(self._ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")

    def now_ist(self):
        return datetime.now(self._ist)

    # ── Logo helper ───────────────────────────
    def get_logo(self, symbol):
        url, name = self.db.get_logo(symbol)
        if url is not None:
            return url or None, name
        url, name = self.mkt.profile(symbol)
        self.db.save_logo(symbol, url, name)
        return url, name

    # ── Market hours (IST) ────────────────────
    def is_premarket(self):
        n = self.now_ist()
        return n.weekday() < 5 and n.hour == 18 and n.minute < 5

    def is_open(self):
        n = self.now_ist()
        if n.weekday() >= 5:
            return False
        return n.hour >= 19 or n.hour == 0 or (n.hour == 1 and n.minute < 30)

    def is_close_time(self):
        n = self.now_ist()
        return n.hour == 1 and n.minute >= 30

    # ── Pre-market broadcast ──────────────────
    def do_premarket(self):
        if self.premarket_sent:
            return
        spy = self.mkt.quote('SPY')
        qqq = self.mkt.quote('QQQ')
        if not spy or not qqq:
            return
        spy_chg = (spy['price'] - spy['prev']) / spy['prev'] * 100
        qqq_chg = (qqq['price'] - qqq['prev']) / qqq['prev'] * 100
        spy_logo, _ = self.get_logo('SPY')
        post(self.webhook, make_premarket_embed(spy_chg, qqq_chg, spy_logo))
        self.premarket_sent = True
        self.log(f"🌅 Pre-market | SPY {spy_chg:+.2f}%  QQQ {qqq_chg:+.2f}%")

    # ── Monitor open positions ────────────────
    def monitor(self):
        for symbol, pos in list(self.positions.items()):
            try:
                q = self.mkt.quote(symbol)
                if not q:
                    continue

                price = q['price']
                entry = pos['entry']
                pnl   = (price - entry) / entry * 100
                age   = (datetime.now() - pos['opened_at']).days
                logo, name = self.get_logo(symbol)

                # ── Sell conditions ──────────────────────
                target_hit = 0
                reason     = None

                if not pos['t1_hit'] and price >= pos['target1']:
                    # First target hit — mark it but keep holding for T2
                    self.positions[symbol]['t1_hit'] = True
                    self.db.mark_t1_hit(symbol)
                    target_hit = 1
                    reason     = f"TARGET 1 HIT +{TARGET_1_PCT}%"
                    post(self.webhook, make_sell_embed(symbol, name, logo, entry, price, pnl, reason, 1))
                    self.db.log(symbol, 'SELL_T1', price, pnl, reason)
                    self.log(f"🎯 T1 {symbol} @ ${price:.2f}  P&L {pnl:+.2f}%")
                    continue   # stay in position, waiting for T2

                if price >= pos['target2']:
                    reason     = f"TARGET 2 HIT +{TARGET_2_PCT}%"
                    target_hit = 2
                elif price <= pos['stop_loss']:
                    reason     = "STOP-LOSS HIT"
                elif age >= MAX_HOLD_DAYS:
                    reason     = f"{MAX_HOLD_DAYS}-DAY EXIT"

                if reason:
                    post(self.webhook,
                         make_sell_embed(symbol, name, logo, entry, price, pnl, reason, target_hit))
                    self.db.log(symbol, 'SELL', price, pnl, reason)
                    self.db.remove_position(symbol)
                    del self.positions[symbol]
                    self.log(f"📤 SELL {symbol} ({name}) | {reason} | P&L {pnl:+.2f}%")

            except Exception as e:
                self.log(f"⚠️  Monitor {symbol}: {e}")

    # ── Scan all stocks, return scored candidates ──
    def scan(self):
        self.log(f"🔍 Scanning {len(STOCKS)} stocks ({WEEKS_HISTORY}w history) …")
        results = {}

        for symbol in STOCKS:
            if symbol in self.positions:
                continue   # already holding
            try:
                q = self.mkt.quote(symbol)
                if not q or q['price'] <= 0:
                    time.sleep(0.12)
                    continue

                c = self.mkt.candles(symbol, weeks=WEEKS_HISTORY)
                if c is None:
                    time.sleep(0.12)
                    continue

                info = score(q, c)
                if info['score'] >= MIN_SCORE:
                    logo, name = self.get_logo(symbol)
                    results[symbol] = {
                        'quote': q, 'info': info,
                        'logo': logo, 'name': name,
                    }
                    self.log(f"  ✅ {symbol:6s} {info['score']:3d}/100  "
                             f"RSI={info['rsi']}  MACD_h={info['macd_hist']:.4f}  "
                             f"BB={info['bb_pct']:.2f}  sup={info['sup_dist_pct']:.1f}%  "
                             f"slope={info['trend_slope']:+.3f}")

                time.sleep(0.12)
            except Exception as e:
                self.log(f"  ⚠️  {symbol}: {e}")

        self.log(f"✅ Scan done — {len(results)} qualifying stocks")
        return results

    # ── Fire the single best signal every 30 min ──
    def fire_signal(self, candidates: dict):
        if datetime.now() - self.last_signal < timedelta(minutes=SIGNAL_EVERY_MIN):
            return
        if not candidates:
            return

        # Pick highest score
        symbol, data = max(candidates.items(), key=lambda x: x[1]['info']['score'])

        q     = data['quote']
        info  = data['info']
        logo  = data['logo']
        name  = data['name']
        price = q['price']
        t1    = round(price * (1 + TARGET_1_PCT / 100), 2)
        t2    = round(price * (1 + TARGET_2_PCT / 100), 2)
        sl    = round(price * (1 - STOP_LOSS_PCT / 100), 2)

        # Store in memory + DB
        pos = {'entry': price, 'target1': t1, 'target2': t2,
               'stop_loss': sl, 't1_hit': False, 'opened_at': datetime.now()}
        self.positions[symbol] = pos
        self.db.add_position(symbol, price, t1, t2, sl)
        self.db.log(symbol, 'BUY', price, 0.0, 'signal')

        self.signals_today += 1
        post(self.webhook,
             make_buy_embed(symbol, name, logo, price, t1, t2, sl, info, self.signals_today))
        self.last_signal = datetime.now()
        self.log(f"📱 BUY {symbol} ({name}) @ ${price:.2f}  T1=${t1}  T2=${t2}  SL=${sl}  score={info['score']}")

    # ── Main loop ─────────────────────────────
    def run(self):
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"── Cycle #{cycle} ──────────────────────────")

                if self.is_premarket():
                    self.do_premarket()

                if self.is_open():
                    self.premarket_sent = False
                    self.monitor()                      # check exits first
                    candidates = self.scan()            # find dips
                    self.fire_signal(candidates)        # best signal every 30 min

                elif self.is_close_time():
                    self.log("🏁 Market closed — resetting daily counter")
                    self.signals_today = 0

                else:
                    self.log("😴 Market closed")

                time.sleep(SCAN_SLEEP_SEC)

            except KeyboardInterrupt:
                self.log("👋 Shutting down")
                break
            except Exception as e:
                self.log(f"❌ Loop error: {e}")
                time.sleep(60)


# ─────────────────────────────────────────────
if __name__ == "__main__":
    MangoBot().run()
