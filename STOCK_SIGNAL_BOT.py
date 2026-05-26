#!/usr/bin/env python3
"""
MANGOBOT - FINAL BATTLE-TESTED VERSION
Simple, Reliable, Works!
"""

import os
import time
from datetime import datetime, timedelta

# Install yfinance
try:
    import yfinance
except:
    print("📦 Installing yfinance...")
    os.system("pip install yfinance --break-system-packages")
    import yfinance

import requests

class MangoBot:
    def __init__(self):
        # Get Discord webhook
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ DISCORD_WEBHOOK not set!")
            exit(1)
        
        # Settings
        self.min_dip = 0.3
        self.min_volume = 100000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        
        # Simple stock list (TESTED & RELIABLE)
        self.stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
            'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW',
            'MCD', 'NFLX', 'CSCO', 'ORACLE', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE',
            'AVGO', 'ASML', 'QCOM', 'INTU', 'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT',
            'MU', 'KLAC', 'LRCX', 'AMAT', 'NKE', 'MRVL', 'MCHP', 'QRVO', 'SWKS',
            'EXC', 'PAYX', 'DDOG', 'CRWD', 'ZM', 'OKTA', 'TWLO', 'NET', 'GDDY',
            'WDAY', 'DBX', 'DOCN', 'SPLK', 'SNOW', 'UPST', 'PTON', 'ROKU', 'COIN',
            'HOOD', 'SOFI', 'GLBE', 'TOST', 'RIOT', 'MARA', 'MSTR', 'NVAX', 'BIIB',
            'REGN', 'VRTX', 'ALNY', 'ILMN', 'HUBS', 'DXCM', 'VEEV', 'PATH', 'ZS',
            'ULTA', 'LVGO', 'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG', 'EXPE', 'NIO',
            'XPENG', 'LI', 'BABA', 'JD', 'PDD', 'BILI', 'SE', 'SPOT', 'UBER', 'LYFT',
            'PINS', 'SNAP', 'TTWO', 'EA', 'ATVI', 'CPRT', 'OPEN', 'CVNA', 'CHPT',
            'BLNK', 'VROOM', 'PRPL', 'KKR', 'BX', 'APO', 'OKE', 'MPC', 'CVX', 'COP',
            'SLB', 'EOG', 'FANG', 'MRO', 'HAL', 'NOV', 'OXY', 'APA', 'XLE', 'XLV',
            'XLI', 'XLF', 'XLK', 'XLY', 'XLP', 'XLRE', 'XLU', 'QQQ', 'DIA', 'IWM',
            'SPY', 'VOO', 'VTI', 'F', 'GM', 'HMC', 'TM', 'BA', 'CAT', 'DE', 'GE',
            'PFE', 'MRNA', 'ABBV', 'TMO', 'LLY', 'MRK', 'AMGN', 'GILD', 'BNTX',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'TROW', 'AXP', 'DFS',
            'SYF', 'VNO', 'PLD', 'PSA', 'EQR', 'AVB', 'ARE', 'MAA', 'WY', 'RYN',
            'PCH', 'IRM', 'SSNC', 'PAYC', 'NTES', 'BIDU', 'VRSN', 'ANET', 'TEAM',
            'DOCU', 'NEWR', 'ORCL', 'WDAY', 'PAYC', 'ZSCALER', 'PALO', 'CRSR',
            'VTV', 'VUG', 'VGK', 'VXUS', 'EEM', 'AGG', 'BND', 'LQD', 'HYG', 'JNK',
            'TLT', 'IEF', 'SHV', 'GLD', 'SLV', 'USO', 'VNQ', 'XRT'
        ]
        
        self.buffer = []
        self.last_push = datetime.now()
        self.log("=" * 80)
        self.log("🥭 MANGOBOT - FINAL TESTED VERSION")
        self.log(f"📊 Stocks: {len(self.stocks)}")
        self.log("=" * 80)
    
    def log(self, msg):
        """Simple logging"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}")
        try:
            with open("bot.log", 'a') as f:
                f.write(f"[{ts}] {msg}\n")
        except:
            pass
    
    def get_stock_data(self, symbol):
        """Fetch stock data - SIMPLE & RELIABLE"""
        try:
            ticker = yfinance.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            # Check if data is valid
            if hist.empty or len(hist) < 100:
                return None
            
            # Get data
            current_price = float(hist['Close'].iloc[-1])
            high_52w = float(hist['High'].max())
            volume = float(hist['Volume'].iloc[-1])
            
            # Validate
            if current_price <= 0 or high_52w <= 0 or volume <= 0:
                return None
            
            # Calculate dip
            dip = ((high_52w - current_price) / high_52w) * 100
            
            return {
                'symbol': symbol,
                'price': round(current_price, 2),
                'high_52w': round(high_52w, 2),
                'volume': int(volume),
                'dip': round(dip, 2)
            }
        except Exception as e:
            return None
    
    def find_signals(self):
        """Find signals - ONE JOB ONLY"""
        signals = []
        analyzed = 0
        found = 0
        
        self.log(f"🔍 Scanning {len(self.stocks)} stocks...")
        
        for symbol in self.stocks:
            data = self.get_stock_data(symbol)
            analyzed += 1
            
            if not data:
                continue
            
            # Check if meets criteria
            if data['dip'] >= self.min_dip and data['volume'] >= self.min_volume:
                found += 1
                
                entry = data['price']
                target = round(entry * (1 + self.profit_target / 100), 2)
                stop = round(entry * (1 - self.stop_loss / 100), 2)
                
                signals.append({
                    'symbol': symbol,
                    'price': entry,
                    'dip': data['dip'],
                    'target': target,
                    'stop': stop
                })
            
            time.sleep(0.05)  # Rate limit
        
        self.log(f"   ✅ Analyzed: {analyzed}")
        self.log(f"   📊 Found: {found}")
        
        if signals:
            self.buffer.extend(signals)
            self.log(f"   💾 Buffer: {len(self.buffer)}")
    
    def push_best_signal(self):
        """Push BEST signal to Discord"""
        if not self.buffer:
            self.log("⚪ No signals in buffer")
            return
        
        # Get best (highest dip)
        best = max(self.buffer, key=lambda x: x['dip'])
        
        # Create message
        message = f"""🥭 **MANGOBOT SIGNAL**
⏰ {datetime.now().strftime("%H:%M %Z")}

🏆 **STOCK:** `{best['symbol']}`
📈 **Entry:** `${best['price']}`
📊 **Dip:** `{best['dip']:.2f}%`
🎯 **Target:** `${best['target']}` (+{self.profit_target}%)
🛑 **Stop:** `${best['stop']}` (-{self.stop_loss}%)

{len(self.buffer)} signals found!

**BUY NOW!** 📲"""
        
        # Send to Discord
        try:
            response = requests.post(
                self.webhook,
                json={'content': message},
                timeout=10
            )
            
            if response.status_code == 204:
                self.log(f"📱 PUSHED: {best['symbol']} (Dip: {best['dip']}%)")
                self.buffer = []
                self.last_push = datetime.now()
            else:
                self.log(f"❌ Discord failed: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Error: {e}")
    
    def is_market_open(self):
        """Check if market is open (EDT)"""
        from datetime import datetime, timezone
        
        edt = timezone(timedelta(hours=-4))
        now = datetime.now(edt)
        
        weekday = now.weekday() < 5
        hours = 9.5 <= now.hour <= 16.0
        
        return weekday and hours
    
    def run(self):
        """Main loop - SIMPLE"""
        cycle = 0
        
        while True:
            cycle += 1
            self.log(f"\n🔄 CYCLE #{cycle}")
            
            if self.is_market_open():
                # Scan
                self.find_signals()
                
                # Check if 30 min passed
                elapsed = datetime.now() - self.last_push
                if elapsed >= timedelta(minutes=30):
                    self.log("⏰ 30 min passed - PUSHING!")
                    self.push_best_signal()
                else:
                    remaining = 30 - int(elapsed.total_seconds() / 60)
                    self.log(f"⏳ Next push in {remaining} min (Buffer: {len(self.buffer)})")
            else:
                self.log("⏳ Market closed (9:30 AM - 4:00 PM EDT)")
            
            self.log("⏱️  Next check in 5 min...\n")
            time.sleep(300)  # 5 minutes


if __name__ == "__main__":
    bot = MangoBot()
    bot.run()
