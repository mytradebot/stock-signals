#!/usr/bin/env python3
"""
MEGA BOT - FINAL SIMPLE VERSION
Just get prices and send best stocks every 30 min
NO complex filters. NO momentum. JUST SIGNALS!
"""

import os
import time
from datetime import datetime, timedelta

try:
    import requests
except:
    os.system("pip install requests --break-system-packages")
    import requests

class SimpleBot:
    def __init__(self):
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ DISCORD_WEBHOOK not set!")
            exit(1)
        
        self.finnhub_key = 'd8bja4hr01qppd8s0760d8bja4hr01qppd8s076g'
        
        # 100 BEST STOCKS
        self.stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BERKSH',
            'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW',
            'MCD', 'NFLX', 'CSCO', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE',
            'AVGO', 'ASML', 'QCOM', 'INTU', 'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT',
            'MU', 'KLAC', 'LRCX', 'AMAT', 'NKE', 'MRVL', 'MCHP', 'QRVO', 'SWKS',
            'EXC', 'PAYX', 'DDOG', 'CRWD', 'ZM', 'OKTA', 'TWLO', 'NET', 'GDDY', 'WDAY',
            'DOCN', 'SNOW', 'UPST', 'PTON', 'ROKU', 'NVAX', 'BIIB', 'REGN', 'VRTX', 'ALNY',
            'ILMN', 'HUBS', 'DXCM', 'VEEV', 'ULTA', 'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG',
            'EXPE', 'BABA', 'JD', 'PDD', 'BILI', 'SE', 'SPOT', 'UBER', 'LYFT', 'PINS',
            'SNAP', 'TTWO', 'EA', 'BLNK', 'PRPL', 'KKR', 'BX', 'APO', 'OKE', 'MPC',
        ]
        
        self.stocks_data = {}
        self.last_signal = datetime.now()
        
        self.log("=" * 60)
        self.log("🥭 MEGA BOT - SIMPLE VERSION")
        self.log("📊 100 BEST STOCKS")
        self.log("🚀 Every 5 min: Get prices")
        self.log("💬 Every 30 min: Send signals to Discord")
        self.log("=" * 60)
    
    def log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {msg}")
    
    def get_price(self, symbol):
        """Get current price from Finnhub"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if 'c' in data and data['c'] > 0:
                return float(data['c'])
        except:
            pass
        
        return None
    
    def scan(self):
        """Scan all stocks and get prices"""
        self.log(f"🔍 Scanning {len(self.stocks)} stocks...")
        
        found = 0
        for symbol in self.stocks:
            try:
                price = self.get_price(symbol)
                
                if price:
                    self.stocks_data[symbol] = price
                    found += 1
                
                time.sleep(0.05)
            except:
                pass
        
        self.log(f"   ✅ Got prices for {found} stocks")
    
    def send_signals(self):
        """Send best stocks to Discord"""
        if not self.stocks_data:
            self.log("⚪ No data yet")
            return
        
        # Get top 6 stocks by price
        sorted_stocks = sorted(self.stocks_data.items(), key=lambda x: x[1], reverse=True)[:6]
        
        message = "🥭 **MEGA BOT SIGNALS**\n"
        message += f"⏰ {datetime.now().strftime('%H:%M %Z')}\n\n"
        
        for i, (symbol, price) in enumerate(sorted_stocks):
            timeframe = [2, 3, 4, 5, 6, 7][i]
            target = price * 1.02  # 2% target
            stop = price * 0.98   # 2% stop
            
            message += f"🟢 **{symbol}** ({timeframe}-day)\n"
            message += f"Entry: ${price:.2f}\n"
            message += f"Target: ${target:.2f} | Stop: ${stop:.2f}\n\n"
        
        try:
            requests.post(self.webhook, json={'content': message}, timeout=10)
            self.log(f"📱 Sent {len(sorted_stocks)} signals to Discord!")
        except:
            self.log("❌ Discord error")
    
    def is_market_hours(self):
        """Check if market is open (EDT)"""
        from datetime import timezone
        edt = timezone(timedelta(hours=-4))
        now = datetime.now(edt)
        
        is_weekday = now.weekday() < 5
        is_open = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_open
    
    def run(self):
        """Main loop"""
        cycle = 0
        
        while True:
            cycle += 1
            self.log(f"\n🔄 CYCLE #{cycle}")
            
            if self.is_market_hours():
                self.scan()
                
                elapsed = datetime.now() - self.last_signal
                if elapsed >= timedelta(minutes=30):
                    self.log("⏰ 30 min - SENDING SIGNALS!")
                    self.send_signals()
                    self.last_signal = datetime.now()
                else:
                    remaining = 30 - int(elapsed.total_seconds() / 60)
                    self.log(f"⏳ Next signal in {remaining} min")
            
            else:
                self.log("⏳ Market closed")
            
            self.log("⏱️ Next check in 5 min...\n")
            time.sleep(300)


if __name__ == "__main__":
    bot = SimpleBot()
    bot.run()
