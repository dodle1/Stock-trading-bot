from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime
from alpaca_trade_api import REST 
from timedelta import Timedelta
from finbert_utils import estimate_sentiment

API_KEY = ""
API_SECRET = ""
BASE_URL = ""

ALPACA_CREDS = {
    "API_KEY":API_KEY, 
    "API_SECRET": API_SECRET,
    "PAPER": True
    
}

class MLTrader(Strategy):
    def initialize(self, symbol:str="SPY", cash_at_risk:float=0.5):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET) 
          
        
    def postion_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quanity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quanity
    
    def get_dates(self):
        today = self.get_datetime()
        three_days_ago = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_ago.strftime('%Y-%m-%d')
        
    
    def get_sentiment(self):
        today, three_days_ago = self.get_dates()
        news = self.api.get_news(symbol=self.symbol,
                                 start=three_days_ago,
                                 end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment
        
        
    def on_trading_iteration(self):
       
        cash, last_price, quanity = self.postion_sizing()
        probability, sentiment = self.get_sentiment()
        print(f"Sentiment: {sentiment}, Probability: {probability}")  
        
        
        if cash > last_price:
            if sentiment == "positive" and probability > .9:
                
                order = self.create_order(
                    self.symbol,
                    quanity,
                    "buy",
                    type="bracket",
                    take_profit_price = last_price * 1.2,
                    stop_loss_price = last_price *.95
                )
                
                self.submit_order(order)
                self.last_trade = "buy"
                
                
            elif sentiment == "negative" and probability > .9:
                
                order = self.create_order(
                    self.symbol,
                    quanity,
                    "sell",
                    type="bracket",
                    take_profit_price = last_price * .8,
                    stop_loss_price = last_price * 1.05
                )
                self.submit_order(order)
                self.last_trade = "sell"
            
                
#Change dates for different data
start_date = datetime(2023,1,1)
end_date = datetime(2023,12,31)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(name='mlstrat', broker=broker,
                    parameters={"symbol":"SPY", 
                                "cash_at_risk":.5})
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol":"SPY",
                "cash_at_risk":.5}
 )

