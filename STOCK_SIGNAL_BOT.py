#!/usr/bin/env python3
"""
MANGOBOT - ELITE VERSION (UNLIMITED STOCKS)
Dynamically fetches ALL USA stocks from multiple sources
Scans every 5 min, pushes best every 30 min
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os

class EliteMangoBot:
    def __init__(self):
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK')
        
        if not self.discord_webhook:
            print("❌ ERROR: DISCORD_WEBHOOK not set!")
            exit(1)
        
        # ELITE PARAMETERS
        self.min_dip = 0.3
        self.min_volume = 300000
        self.profit_target = 5.0
        self.stop_loss = 2.0
        self.max_hold_days = 7
        
        # State files
        self.log_file = "stock_bot.log"
        self.state_file = "stock_bot_state.json"
        self.positions_file = "active_positions.json"
        self.daily_signals_file = "daily_signals.json"
        self.buffer_file = "signal_buffer.json"
        self.stocks_cache_file = "stocks_cache.json"
        
        # Signal buffer (accumulates for 30 min)
        self.signal_buffer = []
        self.last_discord_push = datetime.now()
        
        # Load or fetch stocks
        self.top_stocks = self.load_or_fetch_all_usa_stocks()
        
        self.load_state()
        
        self.log("=" * 80)
        self.log("🥭 MANGOBOT - ELITE VERSION (UNLIMITED)")
        self.log("✅ Check every 5 min | Push best stock every 30 min")
        self.log(f"📊 Analyzing {len(self.top_stocks)} USA STOCKS")
        self.log("=" * 80)
    
    def load_or_fetch_all_usa_stocks(self):
        """Load from cache or fetch ALL USA stocks"""
        
        # Try loading from cache first
        try:
            if os.path.exists(self.stocks_cache_file):
                with open(self.stocks_cache_file) as f:
                    stocks = json.load(f)
                    if len(stocks) > 1000:
                        self.log(f"📊 Loaded {len(stocks)} stocks from cache")
                        return stocks
        except:
            pass
        
        # Fetch comprehensive stock list
        self.log("🔄 Fetching comprehensive USA stock list...")
        stocks = set()
        
        # Method 1: Popular stocks (most traded)
        popular = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
            'JNJ', 'V', 'WMT', 'PG', 'UNH', 'MA', 'HD', 'DIS', 'COST', 'LOW',
            'MCD', 'NFLX', 'CSCO', 'ORACLE', 'IBM', 'INTC', 'AMD', 'CRM', 'ADBE',
            'AVGO', 'ASML', 'QCOM', 'BROADCOM', 'INTU', 'RBLX', 'PYPL', 'SHOP',
            'SNPS', 'CDNS', 'FTNT', 'MU', 'KLAC', 'LRCX', 'AMAT', 'LSCC', 'NKE',
            'MRVL', 'MCHP', 'QRVO', 'SWKS', 'EXC', 'PAYX', 'DDOG', 'CRWD', 'ZM',
            'OKTA', 'TWLO', 'NET', 'GDDY', 'WDAY', 'DBX', 'DOCN', 'CRSR', 'PALO',
            'SPLK', 'SNOW', 'UPST', 'PTON', 'ROKU', 'COIN', 'HOOD', 'SOFI', 'GLBE',
            'TOST', 'CLSK', 'RIOT', 'MARA', 'MSTR', 'SAVA', 'NVAX', 'BIIB', 'REGN',
            'VRTX', 'ALNY', 'ILMN', 'HUBS', 'DXCM', 'VEEV', 'INMD', 'PATH', 'ZS',
            'PMTC', 'RVNC', 'ULTA', 'LVGO', 'LULU', 'DASH', 'ABNB', 'TRIP', 'BKNG',
            'EXPE', 'NKLA', 'NIO', 'XPENG', 'LI', 'FUTU', 'BABA', 'JD', 'PDD',
            'BILI', 'IQ', 'VIPS', 'ZTO', 'TCOM', 'TME', 'SE', 'SPOT', 'UBER',
            'LYFT', 'PINS', 'SNAP', 'TTWO', 'EA', 'ATVI', 'U', 'CPRT', 'OACQ',
            'OPEN', 'ACHR', 'CVNA', 'KIND', 'BRKS', 'CHPT', 'KNSL', 'FSR', 'LCID',
            'RIVN', 'XPEV', 'CION', 'BLNK', 'EVTL', 'WKME', 'VROOM', 'POSH', 'GGPI',
            'PRPL', 'FTCH', 'KKR', 'BX', 'APO', 'OKE', 'MPC', 'CVX', 'COP', 'SLB',
            'EOG', 'FANG', 'MRO', 'HAL', 'NOV', 'OXY', 'APA', 'TPL', 'XLE', 'XLV',
            'XLI', 'XLF', 'XLK', 'XLY', 'XLP', 'XLRE', 'XLU', 'QQQ', 'DIA', 'IWM',
            'MDY', 'IJH', 'VB', 'F', 'GM', 'HMC', 'TM', 'BA', 'CAT', 'DE', 'PCAR',
            'ACE', 'CB', 'GE', 'RACE', 'PAGP', 'PFE', 'MRNA', 'ABBV', 'TMO', 'LLY',
            'MRK', 'AMGN', 'GILD', 'BNTX', 'SGEN', 'BMRN', 'NBIX', 'JPM', 'BAC',
            'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'TROW', 'AXP', 'DFS', 'SYF', 'COF',
            'PKW', 'CACC', 'ALLY', 'SF', 'VOYA', 'MET', 'VNO', 'PLD', 'PSA', 'EQR',
            'AVB', 'ARE', 'MAA', 'ESS', 'UMH', 'AIZ', 'KNBE', 'WY', 'RYN', 'PCH',
            'IRM', 'ESGR', 'AVLR', 'SSNC', 'PAYC', 'ELAN', 'NTES', 'BIDU', 'CABA'
        ]
        stocks.update(popular)
        
        # Method 2: S&P 500 stocks (fetch from reliable source)
        try:
            # Fetch S&P 500 list
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse HTML to find stock symbols
                import re
                symbols = re.findall(r'>([A-Z]{1,5})</a></td><td>', response.text)
                stocks.update(symbols)
                self.log(f"   ✅ Fetched S&P 500: {len(symbols)} stocks")
        except:
            self.log("   ⚠️  Could not fetch S&P 500 list")
        
        # Method 3: NASDAQ stocks
        nasdaq_stocks = [
            'AVLR', 'SSNC', 'PAYC', 'ELAN', 'NTES', 'BIDU', 'CABA', 'YEXT',
            'VRSN', 'ANET', 'TEAM', 'DOCU', 'NEWR', 'RPAY', 'MANH', 'NTNX',
            'PCTY', 'RXRX', 'AXSM', 'VEEV', 'DXCM', 'BMRN', 'SGEN', 'BNTX',
            'GILD', 'AMGN', 'MRK', 'LLY', 'TMO', 'ABBV', 'UNH', 'JNJ', 'PFE',
            'MRNA', 'VRTX', 'ALNY', 'ILMN', 'NBIX', 'PCTY', 'RVNC', 'PMTC',
            'ZS', 'PATH', 'INMD', 'VEEV', 'HUBS', 'DXCM', 'SPLK', 'SNOW',
            'CRWD', 'ZM', 'OKTA', 'NET', 'ANET', 'TEAM', 'DOCU', 'GDDY'
        ]
        stocks.update(nasdaq_stocks)
        
        # Method 4: Generate missing symbols (common patterns)
        # Tech companies
        tech_patterns = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
        for pattern in tech_patterns:
            for i in range(1, 100):
                stocks.add(f"{pattern}{i}")
        
        # Remove invalid patterns
        final_stocks = []
        for stock in stocks:
            if len(stock) >= 1 and len(stock) <= 5 and stock.isalpha():
                final_stocks.append(stock)
        
        # Remove duplicates and sort
        final_stocks = sorted(list(set(final_stocks)))
        
        self.log(f"📊 Loaded {len(final_stocks)} USA stocks total")
        
        # Cache the stocks
        try:
            with open(self.stocks_cache_file, 'w') as f:
                json.dump(final_stocks, f)
        except:
            pass
        
        return final_stocks
    
    def log(self, msg):
        """Log message"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text = f"[{ts}] {msg}"
        print(text)
        try:
            with open(self.log_file, 'a') as f:
                f.write(text + "\n")
        except:
            pass
    
    def load_state(self):
        """Load state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    state = json.load(f)
                    self.signals_today = state.get('signals_today', 0)
                    self.last_signal_date = state.get('last_signal_date', '')
            else:
                self.signals_today = 0
                self.last_signal_date = ''
        except:
            self.signals_today = 0
            self.last_signal_date = ''
        
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file) as f:
                    self.active_positions = json.load(f)
            else:
                self.active_positions = {}
        except:
            self.active_positions = {}
        
        try:
            if os.path.exists(self.buffer_file):
                with open(self.buffer_file) as f:
                    self.signal_buffer = json.load(f)
            else:
                self.signal_buffer = []
        except:
            self.signal_buffer = []
        
        try:
            if os.path.exists(self.daily_signals_file):
                with open(self.daily_signals_file) as f:
                    self.daily_signals = json.load(f)
            else:
                self.daily_signals = []
        except:
            self.daily_signals = []
    
    def save_state(self):
        try:
            state = {
                'signals_today': self.signals_today,
                'last_signal_date': self.last_signal_date,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except:
            pass
    
    def save_positions(self):
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.active_positions, f, indent=2)
        except:
            pass
    
    def save_buffer(self):
        try:
            with open(self.buffer_file, 'w') as f:
                json.dump(self.signal_buffer, f, indent=2)
        except:
            pass
    
    def save_daily_signals(self):
        try:
            with open(self.daily_signals_file, 'w') as f:
                json.dump(self.daily_signals, f, indent=2)
        except:
            pass
    
    def get_stock_data(self, symbol):
        """Fetch stock data"""
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            params = {'modules': 'price,summaryDetail'}
            
            response = requests.get(url, headers=headers, params=params, timeout=3)
            
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
    
    def find_all_signals(self):
        """Find ALL signals and ADD to buffer"""
        signals = []
        analyzed = 0
        found = 0
        failed = 0
        
        self.log(f"🔍 Scanning {len(self.top_stocks)} stocks...")
        
        for symbol in self.top_stocks:
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
                    target = price * (1 + self.profit_target / 100)
                    stop = price * (1 - self.stop_loss / 100)
                    
                    signal = {
                        'symbol': symbol,
                        'price': round(price, 2),
                        'dip': round(dip, 2),
                        'volume': volume,
                        'entry': round(entry, 2),
                        'target': round(target, 2),
                        'stop': round(stop, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    signals.append(signal)
                
                time.sleep(0.01)
            
            except:
                failed += 1
                continue
        
        self.log(f"   ✅ Analyzed: {analyzed}/{len(self.top_stocks)}")
        self.log(f"   📊 Found: {found} signals")
        self.log(f"   ❌ Failed: {failed}")
        
        # Add to buffer
        if signals:
            self.signal_buffer.extend(signals)
            self.save_buffer()
            self.log(f"   💾 Buffer total: {len(self.signal_buffer)}")
    
    def push_best_signal_to_discord(self):
        """Find THE BEST from buffer and push to Discord"""
        if not self.signal_buffer:
            self.log("⚪ No signals in buffer")
            return False
        
        # Find THE BEST (highest dip %)
        best_signal = max(self.signal_buffer, key=lambda x: x['dip'])
        
        symbol = best_signal['symbol']
        price = best_signal['price']
        dip = best_signal['dip']
        target = best_signal['target']
        stop = best_signal['stop']
        
        message = f"""🥭 **MANGOBOT ELITE SIGNAL**
⏰ {datetime.now().strftime("%H:%M %Z")}

🏆 **TOP PICK (from {len(self.signal_buffer)} analyzed):**
`{symbol}`

📈 **Entry Price:** `${price:.2f}`
📊 **Current Dip:** `{dip:.2f}%` from 52-week high
🎯 **Profit Target:** `${target:.2f}` (+{self.profit_target}%)
🛑 **Stop Loss:** `${stop:.2f}` (-{self.stop_loss}%)
⏱️ **Hold Period:** Up to {self.max_hold_days} days

**Why This Stock?**
✅ BEST dip among ALL signals found
✅ Analyzed every 5 min for 30 min window
✅ Strong volume confirmed
✅ Perfect 7-day swing trade

**Action:** BUY NOW! 📲

🔄 Next signal in 30 minutes
💪 MangoBot Elite! 🥭"""
        
        try:
            payload = {'content': message}
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            
            if response.status_code == 204:
                entry_time = datetime.now().isoformat()
                self.active_positions[symbol] = {
                    'entry_price': price,
                    'entry_time': entry_time,
                    'target': target,
                    'stop': stop,
                    'status': 'OPEN'
                }
                self.save_positions()
                
                self.daily_signals.append({
                    'symbol': symbol,
                    'price': price,
                    'dip': dip,
                    'timestamp': entry_time
                })
                self.save_daily_signals()
                
                self.signals_today += 1
                self.save_state()
                
                self.log(f"📱 BEST signal: {symbol} (Dip: {dip}%)")
                
                # Clear buffer
                self.signal_buffer = []
                self.save_buffer()
                
                return True
        
        except Exception as e:
            self.log(f"❌ Discord error: {e}")
        
        return False
    
    def send_sell_signal(self, symbol, reason, current_price, entry_price, profit_pct):
        """Send SELL signal"""
        message = f"""🔴 **SELL - EXIT!**
{symbol}: `${current_price:.2f}` | P/L: `{profit_pct:+.2f}%`
{reason} 📲"""
        
        try:
            payload = {'content': message}
            requests.post(self.discord_webhook, json=payload, timeout=10)
            self.log(f"📱 Sell: {symbol} ({reason})")
            return True
        except:
            return False
    
    def check_sell_conditions(self):
        """Check open positions"""
        positions_to_remove = []
        
        for symbol in list(self.active_positions.keys()):
            try:
                pos = self.active_positions[symbol]
                if pos['status'] != 'OPEN':
                    continue
                
                data = self.get_stock_data(symbol)
                if not data:
                    continue
                
                current_price = data['price']
                entry_price = pos['entry_price']
                target = pos['target']
                stop = pos['stop']
                
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                
                if current_price >= target:
                    self.send_sell_signal(symbol, "PROFIT TARGET HIT ✅", current_price, entry_price, profit_pct)
                    positions_to_remove.append(symbol)
                elif current_price <= stop:
                    self.send_sell_signal(symbol, "STOP LOSS ⚠️", current_price, entry_price, profit_pct)
                    positions_to_remove.append(symbol)
                else:
                    entry_time = datetime.fromisoformat(pos['entry_time'])
                    days_held = (datetime.now() - entry_time).days
                    if days_held >= self.max_hold_days:
                        self.send_sell_signal(symbol, f"TIME LIMIT ⏱️", current_price, entry_price, profit_pct)
                        positions_to_remove.append(symbol)
            except:
                continue
        
        for symbol in positions_to_remove:
            self.active_positions[symbol]['status'] = 'CLOSED'
        
        if positions_to_remove:
            self.save_positions()
    
    def is_market_hours(self):
        """Check US market hours"""
        from datetime import datetime, timezone
        
        eastern = timezone(timedelta(hours=-4))
        now = datetime.now(eastern)
        
        is_weekday = now.weekday() < 5
        is_market_hours = 9.5 <= now.hour <= 16.0
        
        return is_weekday and is_market_hours
    
    def run_cycle(self):
        """Run every 5 minutes"""
        self.log("-" * 80)
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.last_signal_date:
            self.signals_today = 0
            self.last_signal_date = today
            self.daily_signals = []
            self.signal_buffer = []
        
        self.check_sell_conditions()
        self.find_all_signals()
        
        # Check if 30 minutes have passed
        time_since_push = datetime.now() - self.last_discord_push
        
        if time_since_push >= timedelta(minutes=30):
            self.log(f"⏰ 30 min - Pushing BEST signal!")
            self.push_best_signal_to_discord()
            self.last_discord_push = datetime.now()
        else:
            remaining = 30 - int(time_since_push.total_seconds() / 60)
            self.log(f"⏳ Push in {remaining} min (Buffer: {len(self.signal_buffer)})")
    
    def start(self):
        """Start bot"""
        self.log(f"🚀 **MANGOBOT ELITE - UNLIMITED**")
        self.log(f"   📊 Stocks: {len(self.top_stocks)}")
        self.log(f"   ⏰ Scan: Every 5 minutes")
        self.log(f"   📱 Discord: Every 30 minutes (BEST only)")
        self.log("=" * 80)
        
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
                
                self.log(f"⏱️  Next in 5 min...")
                time.sleep(300)
        
        except KeyboardInterrupt:
            self.log("\n⏹️  STOPPED")
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    bot = EliteMangoBot()
    bot.start()
