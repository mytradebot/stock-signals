#!/usr/bin/env python3
"""
STOCK SIGNAL BOT - Daily US Stock Analysis
Analyzes 50+ stocks, sends 1-6 signals/day via Discord
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

class StockSignalBot:
    def __init__(self):
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK')
        
        if not self.discord_webhook:
            print("❌ ERROR: DISCORD_WEBHOOK not set!")
            exit(1)
        
        self.top_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO',
            'ASML', 'NFLX', 'AMD', 'INTC', 'CSCO', 'QCOM', 'CRM', 'ADBE',
            'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT', 'MU', 'KLAC', 'LRCX'
        ]
        
        self.min_dip = 1.5
        self.min_volume = 1000000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        self.max_signals_per_day = 6
        self.signals_today = 0
        
        self.log("=" * 80)
        self.log("🤖 STOCK SIGNAL BOT STARTED")
        self.log("=" * 80)
    
    def log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"[{ts}] {msg}"
        print(text)
    
    def get_stock_data(self, symbol):
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            params = {'modules': 'price,summaryDetail'}
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'quoteSummary' in data and 'result' in data['quoteSummary']:
                    result = data['quoteSummary']['result'][0]
                    
                    price_data = result.get('price', {})
                    summary = result.get('summaryDetail', {})
                    
                    current_price = price_data.get('regularMarketPrice', {}).get('raw', 0)
                    fifty_two_week_high = summary.get('fiftyTwoWeekHigh', {}).get('raw', 0)
                    avg_volume = summary.get('averageVolume', {}).get('raw', 0)
                    
                    if current_price > 0 and fifty_two_week_high > 0:
                        dip = ((fifty_two_week_high - current_price) / fifty_two_week_high) * 100
                        
                        return {
                            'symbol': symbol,
                            'price': current_price,
                            'high_52w': fifty_two_week_high,
                            'volume': avg_volume,
                            'dip': dip
                        }
        except:
            pass
        
        return None
    
    def find_signals(self):
        signals = []
        
        self.log(f"📊 Analyzing {len(self.top_stocks)} stocks...")
        
        for symbol in self.top_stocks:
            try:
                data = self.get_stock_data(symbol)
                
                if not data:
                    continue
                
                price = data['price']
                dip = data['dip']
                volume = data['volume']
                
                if dip >= self.min_dip and volume >= self.min_volume:
                    signals.append({
                        'symbol': symbol,
                        'price': price,
                        'dip': dip,
                        'volume': volume,
                        'entry': price,
                        'target': price * (1 + self.profit_target / 100),
                        'stop': price * (1 - self.stop_loss / 100)
                    })
                    
                    self.log(f"   ✅ {symbol}: ${price:.2f} | Dip: {dip:.2f}%")
                
                time.sleep(0.1)
            
            except:
                continue
        
        signals.sort(key=lambda x: x['dip'], reverse=True)
        
        return signals[:self.max_signals_per_day]
    
    def send_discord_signal(self, signal):
        try:
            symbol = signal['symbol']
            price = signal['price']
            dip = signal['dip']
            target = signal['target']
            stop = signal['stop']
            
            message = f"""🟢 **BUY SIGNAL**

📈 **Stock:** `{symbol}`
💰 **Entry:** `${price:.2f}`
🎯 **Target:** `${target:.2f}` (+{self.profit_target:.1f}%)
🛑 **Stop Loss:** `${stop:.2f}` (-{self.stop_loss:.1f}%)
📉 **Dip:** `{dip:.2f}%` from 52-week high
⏱️ **Hold:** 7-10 days"""
            
            payload = {'content': message}
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                self.log(f"📱 Signal sent: {symbol}")
                return True
        
        except Exception as e:
            self.log(f"❌ Error: {e}")
        
        return False
    
    def is_market_hours(self):
        from datetime import datetime, timezone
        eastern = timezone(timedelta(hours=-5))
        now = datetime.now(eastern)
        
        is_weekday = now.weekday() < 5
        is_market_hours = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_market_hours
    
    def run_cycle(self):
        self.log("-" * 80)
        
        signals = self.find_signals()
        
        if not signals:
            self.log("⚪ No signals found")
        else:
            self.log(f"🟢 Found {len(signals)} signal(s)")
            
            for signal in signals:
                if self.signals_today < self.max_signals_per_day:
                    self.send_discord_signal(signal)
                    self.signals_today += 1
                    time.sleep(2)
    
    def start(self):
        self.log(f"🚀 CONFIG: {len(self.top_stocks)} stocks | Dip: {self.min_dip}% | Target: {self.profit_target}%")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                self.log(f"\n🔄 CYCLE #{cycle} [{now}]")
                
                if self.is_market_hours():
                    self.run_cycle()
                else:
                    self.log("⏳ Market closed")
                
                self.log(f"⏱️ Next check in 1 hour...")
                time.sleep(3600)
        
        except KeyboardInterrupt:
            self.log("\n⏹️ BOT STOPPED")

if __name__ == "__main__":
    bot = StockSignalBot()
    bot.start()
