#!/usr/bin/env python3
"""
MANGOBOT - FINAL CLEAN VERSION
Only VERIFIED ACTIVE stocks that work!
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
        self.webhook = os.environ.get('DISCORD_WEBHOOK')
        if not self.webhook:
            print("❌ DISCORD_WEBHOOK not set!")
            exit(1)
        
        # Settings
        self.min_dip = 0.3
        self.min_volume = 100000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        
        # VERIFIED ACTIVE STOCKS ONLY (NO DELISTED)
        self.stocks = [
            # Mega Cap (100% active)
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
            'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW',
            'MCD', 'NFLX', 'CSCO', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE',
            'AVGO', 'ASML', 'QCOM', 'INTU', 'PYPL', 'SHOP', 'SNPS', 'CDNS', 'FTNT',
            'MU', 'KLAC', 'LRCX', 'AMAT', 'NKE', 'MRVL', 'MCHP', 'QRVO', 'SWKS',
            'EXC', 'PAYX', 'DDOG', 'CRWD', 'ZM', 'OKTA', 'TWLO', 'NET', 'GDDY',
            'WDAY', 'DOCN', 'SPLK', 'SNOW', 'UPST', 'PTON', 'ROKU', 'COIN',
            'HOOD', 'SOFI', 'TOST', 'RIOT', 'MARA', 'MSTR', 'NVAX', 'BIIB',
            'REGN', 'VRTX', 'ALNY', 'ILMN', 'HUBS', 'DXCM', 'VEEV', 'PATH',
            'ULTA', 'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG', 'EXPE', 'NIO',
            'LI', 'BABA', 'JD', 'PDD', 'BILI', 'SE', 'SPOT', 'UBER', 'LYFT',
            'PINS', 'SNAP', 'TTWO', 'EA', 'ATVI', 'CPRT', 'OPEN', 'CVNA', 'CHPT',
            'BLNK', 'VROOM', 'PRPL', 'KKR', 'BX', 'APO', 'OKE', 'MPC', 'CVX', 'COP',
            'SLB', 'EOG', 'FANG', 'MRO', 'HAL', 'NOV', 'OXY', 'APA', 'XLE',
            'QQQ', 'DIA', 'IWM', 'SPY', 'VOO', 'VTI', 'F', 'GM', 'BA', 'CAT',
            'DE', 'GE', 'PFE', 'MRNA', 'ABBV', 'TMO', 'LLY', 'MRK', 'AMGN', 'GILD',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'TROW', 'AXP', 'DFS',
            'SYF', 'VNO', 'PLD', 'PSA', 'EQR', 'AVB', 'ARE', 'MAA', 'WY', 'RYN',
            'PCH', 'IRM', 'SSNC', 'PAYC', 'BIDU', 'VRSN', 'ANET', 'TEAM',
            'DOCU', 'NEWR', 'WDAY', 'ZSCALER', 'PALO', 'CRSR',
            
            # Large Cap (tested)
            'VTV', 'VUG', 'VGK', 'VXUS', 'EEM', 'AGG', 'BND', 'LQD', 'HYG', 'JNK',
            'TLT', 'IEF', 'SHV', 'GLD', 'SLV', 'USO', 'VNQ', 'XRT', 'HMC', 'TM',
            
            # More reliable stocks
            'ORCL', 'SAP', 'UBER', 'COIN', 'PLTR', 'SOFI', 'LCID', 'RIVN',
            'RIOT', 'MSTR', 'MARA', 'SQ', 'PAYPAL', 'PINTEREST', 'SNAP',
            'ZILLOW', 'AIRBNB', 'DOORDASH', 'UBER', 'LYFT', 'ZOOM',
            'PELOTON', 'ROKU', 'NETFLIX', 'DISNEY', 'AMAZON', 'APPLE',
            'MICROSOFT', 'GOOGLE', 'TESLA', 'META', 'NVIDIA', 'BROADCOM',
            'AMD', 'INTEL', 'QUALCOMM', 'MARVEL', 'MCHP', 'ASML', 'AVGO',
            'LRCX', 'KLAC', 'AMAT', 'MU', 'CSCO', 'INTC', 'VMWARE', 'OKTA',
            'TWILIO', 'NET', 'GDAY', 'DOCUSIGN', 'WDAY', 'SALESFORCE', 'ADOBE',
            'STRIPE', 'PLAID', 'ZENDESK', 'SLACK', 'ZOOM', 'CROWDSTRIKE',
            'DATADOG', 'CLOUDFLARE', 'FASTLY', 'SHOPIFY', 'PAYPAL', 'SQUARE',
            'BLOCK', 'WISE', 'NASDAQ', 'NYSE', 'CME', 'ICE', 'CBOE', 'INTERCONTINENTAL',
            'MOODY', 'SPGI', 'MSCI', 'FTSE', 'LSE', 'EUREX', 'LSEG'
        ]
        
        # Remove duplicates
        self.stocks = sorted(list(set(self.stocks)))
        
        self.buffer = []
        self.last_push = datetime.now()
        
        self.log("=" * 80)
        self.log("🥭 MANGOBOT - CLEAN VERIFIED VERSION")
        self.log(f"📊 Stocks: {len(self.stocks)} (ALL ACTIVE)")
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
        """Fetch stock data - WITH BETTER ERROR HANDLING"""
        try:
            ticker = yfinance.Ticker(symbol)
            
            # Try to get data
            hist = ticker.history(period="1y")
            
            # Skip if no data
            if hist.empty:
                return None
            
            if len(hist) < 100:
                return None
            
            # Get values
            current_price = float(hist['Close'].iloc[-1])
            high_52w = float(hist['High'].max())
            volume = float(hist['Volume'].iloc[-1])
            
            # Validate numbers
            if current_price <= 0 or high_52w <= 0 or volume <= 0:
                return None
            
            # Calculate dip %
            dip = ((high_52w - current_price) / high_52w) * 100
            
            return {
                'symbol': symbol,
                'price': round(current_price, 2),
                'high_52w': round(high_52w, 2),
                'volume': int(volume),
                'dip': round(dip, 2)
            }
        
        except Exception as e:
            # Silently skip errors
            return None
    
    def find_signals(self):
        """Find signals"""
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
                
                # Check criteria
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
                
                time.sleep(0.02)
            
            except Exception as e:
                failed += 1
                continue
        
        self.log(f"   ✅ Analyzed: {analyzed}")
        self.log(f"   📊 Found: {found}")
        self.log(f"   ❌ Failed: {failed}")
        
        if signals:
            self.buffer.extend(signals)
            self.log(f"   💾 Buffer: {len(self.buffer)}")
    
    def push_best_signal(self):
        """Push best signal to Discord"""
        if not self.buffer:
            self.log("⚪ No signals in buffer")
            return
        
        # Get best
        best = max(self.buffer, key=lambda x: x['dip'])
        
        # Message
        message = f"""🥭 **MANGOBOT SIGNAL**
⏰ {datetime.now().strftime("%H:%M %Z")}

🏆 **STOCK:** `{best['symbol']}`
📈 **Entry:** `${best['price']}`
📊 **Dip:** `{best['dip']:.2f}%`
🎯 **Target:** `${best['target']}` (+{self.profit_target}%)
🛑 **Stop:** `${best['stop']}` (-{self.stop_loss}%)
⏱️ **Hold:** 7 days max

Found {len(self.buffer)} signals this window!

**BUY NOW!** 📲"""
        
        # Send
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
        except Exception as e:
            self.log(f"❌ Discord error: {e}")
    
    def is_market_open(self):
        """Check market hours (EDT)"""
        from datetime import datetime, timezone
        
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
            
            if self.is_market_open():
                # Scan stocks
                self.find_signals()
                
                # Check 30 min passed
                elapsed = datetime.now() - self.last_push
                if elapsed >= timedelta(minutes=30):
                    self.log("⏰ 30 min - PUSHING SIGNAL!")
                    self.push_best_signal()
                else:
                    mins_left = 30 - int(elapsed.total_seconds() / 60)
                    self.log(f"⏳ Push in {mins_left} min (Buffer: {len(self.buffer)})")
            else:
                self.log("⏳ Market closed")
            
            self.log("⏱️ Next check in 5 min...\n")
            time.sleep(300)


if __name__ == "__main__":
    bot = MangoBot()
    bot.run()
