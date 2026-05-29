#!/usr/bin/env python3
import os, time, json
from datetime import datetime, timedelta, timezone
import requests

try:
    import numpy as np
except:
    os.system("pip install numpy --break-system-packages")
    import numpy as np

class MangoBotUltimate:
    def __init__(self):
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            exit(1)
        
        self.finnhub_key = 'd8bja4hr01qppd8s0760d8bja4hr01qppd8s076g'
        
        self.stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'ADOBE', 'INTC',
            'AMD', 'CRM', 'ORCL', 'CSCO', 'IBM', 'INTU', 'PYPL', 'AVGO', 'QCOM', 'SNPS',
            'CDNS', 'ASML', 'AMAT', 'LRCX', 'KLAC', 'MU', 'MRVL', 'MCHP', 'QRVO', 'FTNT',
            'CRWD', 'OKTA', 'TWLO', 'NET', 'ZS', 'COIN', 'DDOG', 'SNOW', 'DOCN', 'PATH',
            'HOOD', 'UPST', 'RBLX', 'DBX', 'SHOP', 'SPLK', 'PALO', 'CRSR', 'PLTR', 'SOFI',
            'JNJ', 'UNH', 'PFE', 'MRK', 'ABBV', 'AMGN', 'CELG', 'BIIB', 'REGN', 'VRTX',
            'ALNY', 'ILMN', 'VEEV', 'DXCM', 'ISRG', 'ALGN', 'EXAS', 'INCY', 'GILD', 'BPMC',
            'NVAX', 'MRNA', 'BNTX', 'ARWR', 'SRPT', 'BBIO', 'BMRN', 'CBPO', 'EXEL', 'PCVX',
            'SAGE', 'RGEN', 'VYGR', 'ADVM', 'AERI', 'APLT', 'AVRX', 'AXSM', 'AXTA', 'AZTA',
            'BCRX', 'BGNE', 'BGLX', 'BIAH', 'BIEE', 'BKKT', 'BLSP', 'BLFS', 'BMCH', 'BMTX',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'BDX', 'SCHW', 'CME', 'ICE',
            'V', 'MA', 'AXP', 'DFS', 'COF', 'RF', 'PNC', 'USB', 'TFC', 'KEY',
            'CFG', 'MTB', 'FITB', 'HBAN', 'OZK', 'EWBC', 'UMBF', 'WAFD', 'BANR', 'CBSH',
            'FCNCA', 'FFIN', 'FRME', 'GBCI', 'HOFT', 'HWBK', 'IBKR', 'ILHC', 'INDB', 'ISBC',
            'KBSF', 'KFSB', 'LGBO', 'LHCG', 'MBNB', 'MOFB', 'NBHC', 'NWBI', 'NVRO', 'OFG',
            'MCD', 'NKE', 'COST', 'LOW', 'HOME', 'DIS', 'BOOKING', 'EXPEDIA', 'UBER', 'LYFT',
            'DASH', 'ABNB', 'TRIP', 'BKNG', 'EXPE', 'PINS', 'ULTA', 'LULU', 'DLTR', 'FIVE',
            'ROST', 'RH', 'BBBY', 'JWN', 'M', 'KSS', 'GPS', 'GCG', 'DECK', 'YUM',
            'LVS', 'WYNN', 'PENN', 'CAR', 'KMX', 'AZO', 'ORLY', 'AAP', 'CCL', 'RCL',
            'DAL', 'UAL', 'ALK', 'JBLU', 'SAVE', 'SKX', 'WMT', 'PG', 'KO', 'PEP',
            'CL', 'KMB', 'CRK', 'MO', 'PM', 'UVV', 'GIS', 'K', 'CAG', 'MNST',
            'TAP', 'STZ', 'BF.B', 'HSY', 'CPB', 'ADM', 'CELH', 'EL', 'CLX', 'FMX',
            'FIZZ', 'GNRC', 'HRL', 'JJSF', 'LECO', 'LW', 'MDLZ', 'OCHF', 'SMPL', 'SNYD',
            'SJM', 'TSN', 'UNFI', 'WDC', 'WSFS', 'WBA',
            'GE', 'BA', 'RTX', 'HON', 'LMT', 'NOC', 'GD', 'TDG', 'ITT', 'SPR',
            'APH', 'HUBB', 'ALLE', 'EMR', 'IR', 'ZTS', 'SWK', 'TMDX', 'XEL', 'NEE',
            'DUK', 'SO', 'EXC', 'D', 'PEG', 'SRE', 'WEC', 'PPL', 'AEP', 'AES',
            'CMS', 'DTE', 'EIX', 'EQT', 'FE', 'NI', 'OKE', 'AVA', 'PNW', 'CNP',
            'EVRG', 'LNT', 'MAS', 'XOM', 'CVX', 'COP', 'MPC', 'PSX', 'VLO', 'FANG',
            'EOG', 'SLB', 'HAL', 'OXY', 'NOV', 'APA', 'CIVI', 'DINO', 'DVN', 'EQNR',
            'GPRK', 'KMI', 'LPI', 'MRO', 'CTRA', 'PBA', 'PEN', 'PXD', 'RRC', 'SD',
            'SM', 'SNAP', 'TC', 'TSP', 'WMB', 'WPZ', 'NEM', 'GOLD', 'GFI', 'PAAS',
            'ALTG', 'AU', 'AUY', 'BAR', 'HL', 'IAG', 'KL', 'MAG', 'SA', 'SSR',
            'CCI', 'EQIX', 'DLR', 'CSGP', 'PLD', 'AMT', 'SBAC', 'SBA', 'AVB', 'PSA',
            'EXR', 'WELL', 'KRC', 'UMH', 'MPW', 'STAG', 'WCC', 'NHI', 'NHS', 'OHI',
            'PAGP', 'EPR', 'STORE', 'WRT', 'IRT', 'KIM', 'REG', 'SKT', 'BRG', 'CDR',
            'CHCT', 'CTO', 'DEI', 'DRH', 'EDR', 'ELME', 'ELS', 'EME', 'EPRT', 'ESRT',
            'FAM', 'FBP', 'FPI', 'FRT', 'GDRX', 'CMCSA', 'CHTR', 'TMUS', 'VZ', 'T',
            'DISH', 'FOX', 'FOXA', 'VIACA', 'LBRDK', 'LBRDA', 'MSGS', 'MSGM', 'ROKU', 'SPOT',
            'TWTR', 'MTCH', 'ZG', 'ZASH', 'ZETA', 'VIAC', 'FUBO', 'VUZI', 'TRNX', 'TXRH', 'TWOU',
        ]
        
        self.stocks_analysis = {}
        self.open_positions = {}
        self.closed_positions = {}
        self.last_signal = datetime.now() - timedelta(minutes=31)
        self.blocked_stocks = {}
        self.premarket_sent = False
        
        self.load_blocked()
        self.log("🥭 MANGO_BOT ULTIMATE STARTED")
    
    def log(self, msg):
        ist = timezone(timedelta(hours=5, minutes=30))
        ts = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")
        print(f"[{ts}] {msg}")
    
    def load_blocked(self):
        try:
            for path in ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        for symbol, ts in data.items():
                            self.blocked_stocks[symbol] = datetime.fromisoformat(ts)
                    return
        except:
            pass
    
    def save_blocked(self):
        try:
            data = {s: ts.isoformat() for s, ts in self.blocked_stocks.items()}
            for path in ['/home/claude/blocked.json', '/tmp/blocked.json', './blocked.json']:
                try:
                    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
                    with open(path, 'w') as f:
                        json.dump(data, f)
                except:
                    pass
        except:
            pass
    
    def get_stock(self, symbol):
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=5)
            d = r.json()
            if 'c' in d and d['c'] > 0:
                return {
                    'price': float(d['c']), 
                    'volume': int(d.get('v', 100000)), 
                    'high': float(d.get('h', d['c'])), 
                    'low': float(d.get('l', d['c'])), 
                    'prev': float(d.get('pc', d['c']))
                }
        except:
            pass
        
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=demo"
            r = requests.get(url, timeout=5)
            d = r.json()
            if 'Global Quote' in d and d['Global Quote'].get('05. price'):
                quote = d['Global Quote']
                price = float(quote['05. price'])
                if price > 0:
                    return {
                        'price': price,
                        'volume': int(quote.get('06. volume', 100000)),
                        'high': float(quote.get('03. high', price)),
                        'low': float(quote.get('04. low', price)),
                        'prev': float(quote.get('08. previous close', price))
                    }
        except:
            pass
        
        return None
    
    def score_stock(self, symbol, data):
        if not data or data['price'] <= 0:
            return 0
        
        score = 0
        
        if data['volume'] > 5000000:
            score += 30
        elif data['volume'] > 1000000:
            score += 20
        else:
            score += 10
        
        if 50 < data['price'] < 500:
            score += 30
        elif data['price'] > 0:
            score += 15
        
        if data['prev'] > 0:
            change = ((data['price'] - data['prev']) / data['prev']) * 100
            if -1 <= change <= 5:
                score += 40
        
        return min(max(score, 0), 100)
    
    def premarket_check(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        if not (now.hour == 18 and now.minute < 5) or self.premarket_sent:
            return
        
        spy = self.get_stock('SPY')
        qqq = self.get_stock('QQQ')
        
        if spy and qqq:
            spy_change = ((spy['price'] - spy['prev']) / spy['prev']) * 100 if spy['prev'] > 0 else 0
            qqq_change = ((qqq['price'] - qqq['prev']) / qqq['prev']) * 100 if qqq['prev'] > 0 else 0
            
            sentiment = "🟢 BULLISH" if (spy_change + qqq_change) / 2 > 0.5 else ("🔴 BEARISH" if (spy_change + qqq_change) / 2 < -0.5 else "🟡 NEUTRAL")
            
            fields = [
                {"name": "📊 Market Sentiment", "value": sentiment, "inline": True},
                {"name": "📈 S&P 500 (SPY)", "value": f"{spy_change:+.2f}%", "inline": True},
                {"name": "💻 Nasdaq (QQQ)", "value": f"{qqq_change:+.2f}%", "inline": True},
                {"name": "💡 Today's Action", "value": "Markets are ready! Quality signals incoming.", "inline": False},
                {"name": "⚠️ Strategy", "value": "Cautious - Only take high-quality signals (70+).", "inline": False}
            ]
            
            embed = {
                "title": "🌅 MANGO_BOT - MARKET MOMENTUM",
                "color": 16776960,
                "fields": fields,
                "footer": {"text": "🥭 Mango_Bot - Market Outlook | Happy Trading!"}
            }
            try:
                requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
                self.log(f"🌅 PRE-MARKET: {sentiment}")
                self.premarket_sent = True
            except:
                pass
    
    def scan(self):
        self.log(f"🔍 Scanning {len(self.stocks)} stocks...")
        found = 0
        
        for symbol in self.stocks:
            try:
                data = self.get_stock(symbol)
                if data and data['price'] > 0:
                    score = self.score_stock(symbol, data)
                    if score >= 50:
                        self.stocks_analysis[symbol] = {
                            'score': score, 
                            'price': data['price'], 
                            'volume': data['volume'], 
                            'prev': data['prev'],
                            'high': data['high'], 
                            'low': data['low']
                        }
                        found += 1
                time.sleep(0.2)
            except:
                pass
        
        self.log(f"✅ Analyzed {found} stocks")
    
    def monitor(self):
        now = datetime.now()
        to_close = []
        for symbol, pos in list(self.open_positions.items()):
            try:
                data = self.get_stock(symbol)
                if not data:
                    continue
                price = data['price']
                entry = pos['entry']
                target = pos['target']
                
                if price >= target or (now - pos['time']).days >= 7:
                    profit = ((price - entry) / entry) * 100
                    reason = "🎉 TARGET HIT" if price >= target else "⏰ 7-DAY EXIT"
                    
                    embed = {
                        "title": f"{reason} {symbol}",
                        "color": 3066993 if profit > 0 else 15158332,
                        "fields": [
                            {"name": "Entry", "value": f"${entry:.2f}", "inline": True},
                            {"name": "Exit", "value": f"${price:.2f}", "inline": True},
                            {"name": "P&L", "value": f"{profit:+.2f}%", "inline": True}
                        ],
                        "footer": {"text": "🥭 Mango_Bot"}
                    }
                    try:
                        requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
                        self.closed_positions[symbol] = {'symbol': symbol, 'profit': profit}
                        self.log(f"📤 SELL: {symbol} ({profit:+.2f}%)")
                    except:
                        pass
                    to_close.append(symbol)
            except:
                pass
        for s in to_close:
            if s in self.open_positions:
                del self.open_positions[s]
    
    def buy(self, symbol, data, score):
        price = data['price']
        target = price * 1.025
        
        self.open_positions[symbol] = {'entry': price, 'target': target, 'time': datetime.now()}
        self.blocked_stocks[symbol] = datetime.now()
        self.save_blocked()
        
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        mins_left = ((24 - now.hour) * 60 - now.minute + 90) if now.hour >= 19 else ((1 - now.hour) * 60 - now.minute + 30)
        signals_left = max(1, (mins_left // 30) + 1)
        
        embed = {
            "title": f"🟢 MANGO_BOT BUY: {symbol}",
            "color": 3066993,
            "fields": [
                {"name": "📍 Entry", "value": f"${price:.2f}", "inline": True},
                {"name": "🎯 Target", "value": f"${target:.2f} (+2.5%)", "inline": True},
                {"name": "⭐ Score", "value": f"{score}/100", "inline": True},
                {"name": "📢 Signals Left", "value": f"{signals_left} more today!", "inline": True},
                {"name": "🔒 Locked", "value": "7 days", "inline": True},
            ],
            "footer": {"text": "🥭 Mango_Bot Pro"}
        }
        
        try:
            requests.post(self.webhook, json={'embeds': [embed]}, timeout=10)
            self.log(f"📱 BUY: {symbol} @ ${price:.2f}")
        except:
            pass
    
    def is_blocked(self, symbol):
        if symbol not in self.blocked_stocks:
            return False
        days = (datetime.now() - self.blocked_stocks[symbol]).days
        if days >= 7:
            del self.blocked_stocks[symbol]
            self.save_blocked()
            return False
        return True
    
    def is_premarket_time(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        return now.hour == 18 and now.minute < 5
    
    def is_open(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        return ((now.hour >= 19) or (now.hour < 1) or (now.hour == 1 and now.minute < 30)) and now.weekday() < 5
    
    def is_market_close(self):
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        return now.hour == 1 and now.minute >= 30
    
    def run(self):
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log(f"🔄 CYCLE #{cycle}")
                
                if self.is_premarket_time():
                    self.premarket_check()
                
                if self.is_open():
                    self.premarket_sent = False
                    self.scan()
                    self.monitor()
                    
                    elapsed = datetime.now() - self.last_signal
                    if elapsed >= timedelta(minutes=30) and len(self.stocks_analysis) > 0:
                        available = {s: d for s, d in self.stocks_analysis.items() if not self.is_blocked(s)}
                        if available:
                            best = max(available.items(), key=lambda x: x[1]['score'])
                            self.buy(best[0], best[1], best[1]['score'])
                            self.last_signal = datetime.now()
                
                elif self.is_market_close():
                    self.log("🏁 MARKET CLOSED")
                    self.closed_positions = {}
                else:
                    self.log("😴 Market closed")
                
                time.sleep(300)
            except Exception as e:
                self.log(f"❌ ERROR: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = MangoBotUltimate()
    bot.run()
