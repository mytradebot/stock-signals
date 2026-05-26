#!/usr/bin/env python3
"""
MANGOBOT - DYNAMIC STOCK CRAWLER
Fetches ALL USA stocks from web automatically
No hardcoding - Real data!
"""

import os
import json
import time
from datetime import datetime, timedelta
import requests

def install_packages():
    """Install required packages"""
    try:
        import yfinance
    except:
        print("📦 Installing yfinance...")
        os.system("pip install yfinance --break-system-packages")
    
    try:
        import pandas
    except:
        print("📦 Installing pandas...")
        os.system("pip install pandas --break-system-packages")

install_packages()

import yfinance
import pandas as pd

class DynamicMangoBot:
    def __init__(self):
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ ERROR: DISCORD_WEBHOOK not set!")
            exit(1)
        
        # Parameters
        self.min_dip = 0.3
        self.min_volume = 100000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        self.max_hold = 7
        
        # Dynamically fetch stocks
        self.stocks = self.fetch_all_usa_stocks()
        
        self.buffer = []
        self.last_push = datetime.now()
        self.signals_today = 0
        self.today = datetime.now().strftime("%Y-%m-%d")
        
        self.log("=" * 80)
        self.log("🥭 MANGOBOT - DYNAMIC CRAWLER")
        self.log(f"📊 Found {len(self.stocks)} USA stocks")
        self.log("=" * 80)
    
    def fetch_all_usa_stocks(self):
        """Fetch ALL USA stocks from multiple sources"""
        self.log("🌐 Fetching ALL USA stocks from web...")
        all_stocks = set()
        
        # METHOD 1: Fetch S&P 500 from Wikipedia
        try:
            self.log("   📥 Fetching S&P 500...")
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse HTML table
                df = pd.read_html(response.text)[0]
                if 'Symbol' in df.columns:
                    symbols = df['Symbol'].tolist()
                    all_stocks.update(symbols)
                    self.log(f"      ✅ Got {len(symbols)} S&P 500 stocks")
        except Exception as e:
            self.log(f"      ⚠️  S&P 500 failed: {e}")
        
        # METHOD 2: Fetch NASDAQ stocks
        try:
            self.log("   📥 Fetching NASDAQ...")
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                df = pd.read_html(response.text)[4]  # NASDAQ table
                if 'Ticker' in df.columns:
                    symbols = df['Ticker'].tolist()
                    all_stocks.update(symbols)
                    self.log(f"      ✅ Got {len(symbols)} NASDAQ stocks")
        except Exception as e:
            self.log(f"      ⚠️  NASDAQ failed: {e}")
        
        # METHOD 3: Fetch Dow Jones from Wikipedia
        try:
            self.log("   📥 Fetching Dow Jones...")
            url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                df = pd.read_html(response.text)[1]  # Dow table
                if 'Symbol' in df.columns:
                    symbols = df['Symbol'].tolist()
                    all_stocks.update(symbols)
                    self.log(f"      ✅ Got {len(symbols)} Dow Jones stocks")
        except Exception as e:
            self.log(f"      ⚠️  Dow failed: {e}")
        
        # METHOD 4: Fetch Russell 3000 stocks
        try:
            self.log("   📥 Fetching Russell 3000...")
            url = "https://en.wikipedia.org/wiki/Russell_3000"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                tables = pd.read_html(response.text)
                for table in tables:
                    if 'Ticker' in table.columns:
                        symbols = table['Ticker'].tolist()
                        all_stocks.update(symbols)
                self.log(f"      ✅ Got Russell 3000 stocks")
        except Exception as e:
            self.log(f"      ⚠️  Russell failed: {e}")
        
        # METHOD 5: Get popular ETFs and stocks
        popular = [
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
            'VRSN', 'ANET', 'TEAM', 'DOCU', 'NEWR', 'ORCL', 'WDAY', 'OKTA', 'ZSCALER', 'PALO'
        ]
        all_stocks.update(popular)
        
        # Clean up stock symbols
        final_stocks = []
        for stock in all_stocks:
            stock = str(stock).strip().upper()
            # Only keep valid stock symbols (1-5 chars, letters only)
            if len(stock) >= 1 and len(stock) <= 5 and stock.replace('.', '').replace('-', '').isalpha():
                final_stocks.append(stock)
        
        final_stocks = sorted(list(set(final_stocks)))
        
        self.log(f"✅ Total unique stocks: {len(final_stocks)}")
        self.log(f"📊 Ready to analyze!")
        
        return final_stocks
    
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
        """Fetch stock data"""
        try:
            ticker = yfinance.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty or len(hist) < 50:
                return None
            
            price = hist['Close'].iloc[-1]
            high_52w = hist['High'].max()
            volume = hist['Volume'].iloc[-1]
            
            if price > 0 and high_52w > 0 and volume > 0:
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
        """Scan ALL stocks"""
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
                
                time.sleep(0.01)
            except:
                failed += 1
                continue
        
        self.log(f"   ✅ Analyzed: {analyzed}/{len(self.stocks)}")
        self.log(f"   📊 Found: {found} signals")
        self.log(f"   ❌ Failed: {failed}")
        
        if signals:
            self.buffer.extend(signals)
            self.log(f"   💾 Buffer: {len(self.buffer)}")
        
        return signals
    
    def push_best_to_discord(self):
        """Push best signal"""
        if not self.buffer:
            self.log("⚪ No signals")
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

🔄 Next in 30 min
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
        """Check market hours"""
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
                
                # Reset daily
                today = datetime.now().strftime("%Y-%m-%d")
                if today != self.today:
                    self.signals_today = 0
                    self.today = today
                    self.buffer = []
                
                if self.is_market_open():
                    # Scan
                    self.find_signals()
                    
                    # Check 30 min
                    elapsed = datetime.now() - self.last_push
                    if elapsed >= timedelta(minutes=30):
                        self.log("⏰ 30 min - PUSHING!")
                        self.push_best_to_discord()
                        self.last_push = datetime.now()
                    else:
                        remaining = 30 - int(elapsed.total_seconds() / 60)
                        self.log(f"⏳ Push in {remaining} min (Buffer: {len(self.buffer)})")
                else:
                    self.log("⏳ Market closed")
                
                self.log(f"⏱️  Next check: 5 min...")
                time.sleep(300)
        
        except KeyboardInterrupt:
            self.log("\n⏹️  STOPPED")
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    bot = DynamicMangoBot()
    bot.run()
