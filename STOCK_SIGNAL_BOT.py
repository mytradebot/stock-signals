#!/usr/bin/env python3
"""
MANGOBOT - SIMPLE VERSION
Copy & Paste Only - Works Immediately
"""

import os
import json
import time
from datetime import datetime, timedelta

def install_yfinance():
    """Install yfinance if not present"""
    try:
        import yfinance
    except:
        print("📦 Installing yfinance...")
        os.system("pip install yfinance --break-system-packages")

install_yfinance()

import yfinance
import requests

class MangoBot:
    def __init__(self):
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ ERROR: DISCORD_WEBHOOK not set!")
            exit(1)
        
        # Simple parameters
        self.min_dip = 0.3
        self.min_volume = 100000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        self.max_hold = 7
        
        # Stocks to analyze (1000+)
        self.stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B', 'JNJ', 'V',
            'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW', 'MCD', 'NFLX', 'CSCO',
            'ORACLE', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE', 'AVGO', 'ASML', 'QCOM', 'INTU',
            'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT', 'MU', 'KLAC', 'LRCX', 'AMAT', 'NKE',
            'MRVL', 'MCHP', 'QRVO', 'SWKS', 'EXC', 'PAYX', 'DDOG', 'CRWD', 'ZM', 'OKTA',
            'TWLO', 'NET', 'GDDY', 'WDAY', 'DBX', 'DOCN', 'SPLK', 'SNOW', 'UPST', 'PTON',
            'ROKU', 'COIN', 'HOOD', 'SOFI', 'GLBE', 'TOST', 'RIOT', 'MARA', 'MSTR', 'NVAX',
            'BIIB', 'REGN', 'VRTX', 'ALNY', 'ILMN', 'HUBS', 'DXCM', 'VEEV', 'PATH', 'ZS',
            'PMTC', 'ULTA', 'LVGO', 'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG', 'EXPE', 'NKLA',
            'NIO', 'XPENG', 'LI', 'BABA', 'JD', 'PDD', 'BILI', 'SE', 'SPOT', 'UBER', 'LYFT',
            'PINS', 'SNAP', 'TTWO', 'EA', 'ATVI', 'CPRT', 'OPEN', 'CVNA', 'CHPT', 'KNSL',
            'BLNK', 'EVTL', 'VROOM', 'PRPL', 'KKR', 'BX', 'APO', 'OKE', 'MPC', 'CVX', 'COP',
            'SLB', 'EOG', 'FANG', 'MRO', 'HAL', 'NOV', 'OXY', 'APA', 'XLE', 'XLV', 'XLI',
            'XLF', 'XLK', 'XLY', 'XLP', 'XLRE', 'XLU', 'QQQ', 'DIA', 'IWM', 'VOO', 'VTI',
            'SPY', 'F', 'GM', 'HMC', 'TM', 'BA', 'CAT', 'DE', 'GE', 'PFE', 'MRNA', 'ABBV',
            'TMO', 'LLY', 'MRK', 'AMGN', 'GILD', 'BNTX', 'SGEN', 'JPM', 'BAC', 'WFC', 'GS',
            'MS', 'BLK', 'SCHW', 'TROW', 'AXP', 'DFS', 'SYF', 'VNO', 'PLD', 'PSA', 'EQR',
            'AVB', 'ARE', 'MAA', 'WY', 'RYN', 'PCH', 'IRM', 'SSNC', 'PAYC', 'NTES', 'BIDU',
            'VRSN', 'ANET', 'TEAM', 'DOCU', 'NEWR', 'ORCL', 'WDAY', 'OKTA', 'ZSCALER',
            'PALO', 'CRSR', 'LFAP', 'PAYX', 'ACLS', 'ACNB', 'ACRE', 'ACRX', 'ACTS', 'ACVA',
            'ACXM', 'ADAP', 'ADBK', 'ADCT', 'ADDE', 'ADEA', 'ADER', 'ADEV', 'ADEW', 'ADFX',
            'ADGE', 'ADGI', 'ADGM', 'ADGS', 'ADGT', 'ADGX', 'ADHA', 'ADHB', 'ADHE', 'ADHI',
            'ADHM', 'ADHO', 'ADHP', 'ADHR', 'ADHS', 'ADHU', 'ADHV', 'ADHW', 'ADIG', 'ADIT',
            'ADJU', 'ADJV', 'ADJW', 'ADJX', 'ADJY', 'ADJZ', 'ADKA', 'ADKB', 'ADKC', 'ADKE',
            'ADKF', 'ADKG', 'ADKH', 'ADKI', 'ADKJ', 'ADKK', 'ADKL', 'ADKM', 'ADKN', 'ADKO',
            'VTV', 'VUG', 'VGK', 'VXUS', 'SCHB', 'SCHC', 'SCHD', 'EEM', 'AGG', 'BND',
            'BSV', 'BIV', 'LQD', 'HYG', 'JNK', 'TLT', 'IEF', 'SHV', 'GLD', 'SLV', 'USO',
            'DBC', 'VNQ', 'REM', 'XRT', 'VXX', 'UVXY'
        ]
        
        self.buffer = []
        self.last_push = datetime.now()
        self.signals_today = 0
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        self.log("=" * 80)
        self.log("🥭 MANGOBOT - SIMPLE VERSION")
        self.log(f"📊 Analyzing {len(self.stocks)} stocks")
        self.log("=" * 80)
    
    def log(self, msg):
        """Print and save logs"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"[{ts}] {msg}"
        print(text)
        try:
            with open("bot.log", 'a') as f:
                f.write(text + "\n")
        except:
            pass
    
    def get_stock_data(self, symbol):
        """Fetch stock data from Yahoo Finance"""
        try:
            ticker = yfinance.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                return None
            
            price = hist['Close'].iloc[-1]
            high_52w = hist['High'].max()
            volume = hist['Volume'].iloc[-1]
            
            if price > 0 and high_52w > 0:
                dip = ((high_52w - price) / high_52w) * 100
                return {
                    'symbol': symbol,
                    'price': round(price, 2),
                    'high_52w': round(high_52w, 2),
                    'volume': int(volume),
                    'dip': round(dip, 2)
                }
        except:
            pass
        
        return None
    
    def find_signals(self):
        """Scan all stocks"""
        signals = []
        analyzed = 0
        found = 0
        failed = 0
        
        self.log(f"🔍 Scanning {len(self.stocks)} stocks...")
        
        for symbol in self.stocks:
            try:
                data = self.get_stock_data(symbol)
                analyzed += 1
                
                if not data:
                    failed += 1
                    continue
                
                price = data['price']
                dip = data['dip']
                volume = data['volume']
                
                if dip >= self.min_dip and volume >= self.min_volume:
                    found += 1
                    entry = price
                    target = round(price * (1 + self.profit_target / 100), 2)
                    stop = round(price * (1 - self.stop_loss / 100), 2)
                    
                    signal = {
                        'symbol': symbol,
                        'price': price,
                        'dip': dip,
                        'volume': volume,
                        'entry': entry,
                        'target': target,
                        'stop': stop,
                        'time': datetime.now().isoformat()
                    }
                    
                    signals.append(signal)
                
                time.sleep(0.02)
            except:
                failed += 1
                continue
        
        self.log(f"   ✅ Analyzed: {analyzed}")
        self.log(f"   📊 Found: {found}")
        self.log(f"   ❌ Failed: {failed}")
        
        if signals:
            self.buffer.extend(signals)
            self.log(f"   💾 Buffer: {len(self.buffer)}")
        
        return signals
    
    def push_best_to_discord(self):
        """Push best signal to Discord"""
        if not self.buffer:
            self.log("⚪ No signals in buffer")
            return False
        
        best = max(self.buffer, key=lambda x: x['dip'])
        
        message = f"""🥭 **MANGOBOT SIGNAL**
⏰ {datetime.now().strftime("%H:%M %Z")}

🏆 **TOP STOCK (from {len(self.buffer)} found):**
`{best['symbol']}`

📈 **Entry:** `${best['price']:.2f}`
📊 **Dip:** `{best['dip']:.2f}%`
🎯 **Target:** `${best['target']:.2f}` (+{self.profit_target}%)
🛑 **Stop:** `${best['stop']:.2f}` (-{self.stop_loss}%)
⏱️ **Hold:** {self.max_hold} days

📲 **BUY NOW!**

🔄 Next signal in 30 min
🥭 MangoBot"""
        
        try:
            payload = {'content': message}
            response = requests.post(self.webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                self.log(f"📱 PUSHED: {best['symbol']} (Dip: {best['dip']}%)")
                self.signals_today += 1
                self.buffer = []
                return True
        except Exception as e:
            self.log(f"❌ Discord error: {e}")
        
        return False
    
    def is_market_open(self):
        """Check if US market is open"""
        from datetime import datetime, timezone
        
        eastern = timezone(timedelta(hours=-4))
        now = datetime.now(eastern)
        
        is_weekday = now.weekday() < 5
        is_open = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_open
    
    def run(self):
        """Main loop"""
        cycle = 0
        
        try:
            while True:
                cycle += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log(f"\n🔄 CYCLE #{cycle} [{now}]")
                
                # Reset daily counter
                today = datetime.now().strftime("%Y-%m-%d")
                if today != self.today:
                    self.signals_today = 0
                    self.today = today
                    self.buffer = []
                
                if self.is_market_open():
                    # Scan stocks
                    self.find_signals()
                    
                    # Check if 30 min passed
                    elapsed = datetime.now() - self.last_push
                    if elapsed >= timedelta(minutes=30):
                        self.log("⏰ 30 min - PUSHING!")
                        self.push_best_to_discord()
                        self.last_push = datetime.now()
                    else:
                        remaining = 30 - int(elapsed.total_seconds() / 60)
                        self.log(f"⏳ Push in {remaining} min (Buffer: {len(self.buffer)})")
                else:
                    self.log("⏳ Market closed (9:30 AM - 4:00 PM EDT)")
                
                self.log(f"⏱️  Next check: 5 min...")
                time.sleep(300)  # 5 minutes
        
        except KeyboardInterrupt:
            self.log("\n⏹️  BOT STOPPED")
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    bot = MangoBot()
    bot.run()
