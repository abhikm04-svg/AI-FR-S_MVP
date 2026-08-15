import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os

import nselib
from nselib import capital_market
from mftool import Mftool
from supabase import create_client, Client

class RobustMftool(Mftool):
    def get_scheme_codes(self, as_json=False):
        """
        Overridden to handle malformed lines in AMFI data robustly.
        """
        scheme_info = {}
        url = self._get_quote_url
        try:
            response = self._session.get(url)
            data = response.text.split("\n")
            for scheme_data in data:
                if ";" in scheme_data:
                    scheme = scheme_data.split(";")
                    # FIX: Check length to prevent IndexError
                    if len(scheme) >= 4:
                        scheme_info[scheme[0]] = scheme[3]
        except Exception as e:
            print(f"Error fetching scheme codes in RobustMftool: {e}")
            
        # Basic implementation of render_response for as_json=False (default)
        if as_json:
            import json
            return json.dumps(scheme_info)
        return scheme_info

# ==========================================
# CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="FinAgents India: AI Financial Council",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Agent styling
st.markdown("""
<style>
    :root {
      --background: oklch(0.9777 0.0041 301.4256);
      --foreground: oklch(0.3651 0.0325 287.0807);
      --card: oklch(1.0000 0 0);
      --card-foreground: oklch(0.3651 0.0325 287.0807);
      --popover: oklch(1.0000 0 0);
      --popover-foreground: oklch(0.3651 0.0325 287.0807);
      --primary: oklch(0.6104 0.0767 299.7335);
      --primary-foreground: oklch(0.9777 0.0041 301.4256);
      --secondary: oklch(0.8957 0.0265 300.2416);
      --secondary-foreground: oklch(0.3651 0.0325 287.0807);
      --muted: oklch(0.8906 0.0139 299.7754);
      --muted-foreground: oklch(0.5288 0.0375 290.7895);
      --accent: oklch(0.7889 0.0802 359.9375);
      --accent-foreground: oklch(0.3394 0.0441 1.7583);
      --destructive: oklch(0.6332 0.1578 22.6734);
      --destructive-foreground: oklch(0.9777 0.0041 301.4256);
      --border: oklch(0.8447 0.0226 300.1421);
      --input: oklch(0.9329 0.0124 301.2783);
      --ring: oklch(0.6104 0.0767 299.7335);
      --chart-1: oklch(0.6104 0.0767 299.7335);
      --chart-2: oklch(0.7889 0.0802 359.9375);
      --chart-3: oklch(0.7321 0.0749 169.8670);
      --chart-4: oklch(0.8540 0.0882 76.8292);
      --chart-5: oklch(0.7857 0.0645 258.0839);
      --sidebar: oklch(0.9554 0.0082 301.3541);
      --sidebar-foreground: oklch(0.3651 0.0325 287.0807);
      --sidebar-primary: oklch(0.6104 0.0767 299.7335);
      --sidebar-primary-foreground: oklch(0.9777 0.0041 301.4256);
      --sidebar-accent: oklch(0.7889 0.0802 359.9375);
      --sidebar-accent-foreground: oklch(0.3394 0.0441 1.7583);
      --sidebar-border: oklch(0.8719 0.0198 302.1690);
      --sidebar-ring: oklch(0.6104 0.0767 299.7335);
      --font-sans: Geist, sans-serif;
      --font-serif: "Lora", Georgia, serif;
      --font-mono: "Fira Code", "Courier New", monospace;
      --radius: 0.5rem;
      --shadow-x: 1px;
      --shadow-y: 2px;
      --shadow-blur: 5px;
      --shadow-spread: 1px;
      --shadow-opacity: 0.06;
      --shadow-color: hsl(0 0% 0%);
      --shadow-2xs: 1px 2px 5px 1px hsl(0 0% 0% / 0.03);
      --shadow-xs: 1px 2px 5px 1px hsl(0 0% 0% / 0.03);
      --shadow-sm: 1px 2px 5px 1px hsl(0 0% 0% / 0.06), 1px 1px 2px 0px hsl(0 0% 0% / 0.06);
      --shadow: 1px 2px 5px 1px hsl(0 0% 0% / 0.06), 1px 1px 2px 0px hsl(0 0% 0% / 0.06);
      --shadow-md: 1px 2px 5px 1px hsl(0 0% 0% / 0.06), 1px 2px 4px 0px hsl(0 0% 0% / 0.06);
      --shadow-lg: 1px 2px 5px 1px hsl(0 0% 0% / 0.06), 1px 4px 6px 0px hsl(0 0% 0% / 0.06);
      --shadow-xl: 1px 2px 5px 1px hsl(0 0% 0% / 0.06), 1px 8px 10px 0px hsl(0 0% 0% / 0.06);
      --shadow-2xl: 1px 2px 5px 1px hsl(0 0% 0% / 0.15);
      --tracking-normal: 0em;
      --spacing: 0.25rem;
    }

    @media (prefers-color-scheme: dark) {
      :root {
        --background: oklch(0.1300 0.0280 261.6920);
        --foreground: oklch(0.9053 0.0245 293.5570);
        --card: oklch(0.2544 0.0301 292.7315);
        --card-foreground: oklch(0.9053 0.0245 293.5570);
        --popover: oklch(0.6060 0.2500 292.7170);
        --popover-foreground: oklch(0.9053 0.0245 293.5570);
        --primary: oklch(0.5410 0.2810 293.0090);
        --primary-foreground: oklch(0.7230 0.2190 149.5790);
        --secondary: oklch(0.1300 0.0280 261.6920);
        --secondary-foreground: oklch(0.9710 0.0130 17.3800);
        --muted: oklch(0.2560 0.0320 294.8380);
        --muted-foreground: oklch(0.6974 0.0282 300.0614);
        --accent: oklch(0.3181 0.0321 308.6149);
        --accent-foreground: oklch(0.8391 0.0692 2.6681);
        --destructive: oklch(0.6875 0.1420 21.4566);
        --destructive-foreground: oklch(0.2166 0.0215 292.8474);
        --border: oklch(0.3063 0.0359 293.3367);
        --input: oklch(0.2847 0.0346 291.2726);
        --ring: oklch(0.7058 0.0777 302.0489);
        --chart-1: oklch(0.7058 0.0777 302.0489);
        --chart-2: oklch(0.8391 0.0692 2.6681);
        --chart-3: oklch(0.7321 0.0749 169.8670);
        --chart-4: oklch(0.8540 0.0882 76.8292);
        --chart-5: oklch(0.7857 0.0645 258.0839);
        --sidebar: oklch(0.1985 0.0200 293.6639);
        --sidebar-foreground: oklch(0.9053 0.0245 293.5570);
        --sidebar-primary: oklch(0.7058 0.0777 302.0489);
        --sidebar-primary-foreground: oklch(0.2166 0.0215 292.8474);
        --sidebar-accent: oklch(0.3181 0.0321 308.6149);
        --sidebar-accent-foreground: oklch(0.8391 0.0692 2.6681);
        --sidebar-border: oklch(0.2847 0.0346 291.2726);
        --sidebar-ring: oklch(0.7058 0.0777 302.0489);
    }

    .agent-box {
        padding: 20px;
        border-radius: var(--radius);
        margin-bottom: 20px;
        border: 1px solid var(--border);
        background-color: var(--card);
        color: var(--card-foreground);
        box-shadow: var(--shadow-sm);
    }
    .agent-title {
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .researcher { border-left: 5px solid var(--chart-1); }
    .analyst { border-left: 5px solid var(--chart-2); }
    .reporter { border-left: 5px solid var(--chart-3); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SHARED MEMORY (The "Brain")
# ==========================================
if 'shared_memory' not in st.session_state:
    st.session_state.shared_memory = {
        'user_profile': {},
        'raw_market_data': None,
        'analyzed_metrics': None,
        'final_thesis': ""
    }

# ==========================================
# DATABASE HANDLER
# ==========================================
class DatabaseHandler:
    def __init__(self):
        # Try Streamlit secrets first, then fallback to environment variables for local runs
        self.url = None
        self.key = None

        try:
            self.url = st.secrets.get("SUPABASE_URL")
            self.key = st.secrets.get("SUPABASE_KEY")
        except Exception:
            # st.secrets can throw when no secrets.toml is configured
            pass

        if not self.url:
            self.url = os.getenv("SUPABASE_URL")
        if not self.key:
            self.key = os.getenv("SUPABASE_KEY")

        try:
            if self.url and self.key:
                self.client: Client = create_client(self.url, self.key)
                self.connected = True
            else:
                self.connected = False
        except Exception as e:
            self.connected = False
            print(f"Supabase Connection Failed: {e}")

    def get_all_schemes(self):
        """Retrieves all schemes from DB."""
        if not self.connected: return {}
        try:
            response = self.client.table("mf_schemes").select("scheme_code, scheme_name").execute()
            return {doc['scheme_code']: doc['scheme_name'] for doc in response.data}
        except:
            return {}

    def get_nav_history(self, scheme_code):
        """Retrieves NAV history for a scheme."""
        if not self.connected: return None
        try:
            response = self.client.table("mf_nav_history").select("history").eq("scheme_code", scheme_code).execute()
            return response.data[0]['history'] if response.data else None
        except:
            return None

# ==========================================
# TOOLKIT (The "Hands" of the Agents)
# ==========================================

class FinancialTools:
    """
    A collection of tools for Indian Market Analysis.
    """
    mf = RobustMftool()
    db = DatabaseHandler() # Initialize DB Handler

    @staticmethod
    @st.cache_data
    def get_all_nse_stocks():
        """
        Fetches the list of all active equity stocks from NSE using nselib.
        Returns a dict {Ticker: Name}.
        """
        try:
            # Fetch equity list
            df = capital_market.equity_list()
            # The column name usually is 'SYMBOL' and 'NAME OF COMPANY'
            if 'SYMBOL' in df.columns:
                # Create a dict mapping Ticker -> Name
                # Clean names: Title case
                mapping = {}
                for _, row in df.iterrows():
                    ticker = f"{row['SYMBOL']}.NS"
                    name = row.get('NAME OF COMPANY', row['SYMBOL']).title()
                    mapping[ticker] = name
                return mapping
            return {}
        except Exception as e:
            st.error(f"Error fetching NSE stock list: {e}")
            return {}

    @staticmethod
    @st.cache_data
    def get_all_etfs():
        """
        Dynamically fetches all listed ETFs by comparing Bhavcopy (All Traded) 
        vs Equity List (Companies).
        Returns a dict {Ticker: Name}.
        """
        try:
            # 1. Fetch Equity List (Companies)
            equity_df = capital_market.equity_list()
            equity_symbols = set(equity_df['SYMBOL']) if 'SYMBOL' in equity_df.columns else set()
            
            # 2. Fetch Bhavcopy for the last few days to find active ETFs
            # Try last 5 days to find a trading day
            bhav_df = pd.DataFrame()
            for i in range(5):
                date_check = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%Y')
                try:
                    bhav_df = capital_market.bhav_copy_with_delivery(date_check)
                    if not bhav_df.empty:
                        break
                except:
                    continue
            
            if bhav_df.empty:
                return {}

            # 3. Filter for EQ series and find difference
            # ETFs are usually in EQ series but NOT in the equity list of companies
            if 'SERIES' not in bhav_df.columns or 'SYMBOL' not in bhav_df.columns:
                return {}

            traded_symbols = set(bhav_df[bhav_df['SERIES'] == 'EQ']['SYMBOL'])
            etf_symbols = traded_symbols - equity_symbols
            
            # 4. Create Mapping
            # Since we don't have names in Bhavcopy, we'll use Ticker as Name 
            # or try to format it.
            etf_map = {}
            for sym in etf_symbols:
                ticker = f"{sym}.NS"
                # Heuristic: Most ETFs have 'ETF' or 'BEES' in symbol, but not all.
                # We will just list them all.
                etf_map[ticker] = f"{sym} (ETF)"
            
            return etf_map
        except Exception as e:
            st.error(f"Error fetching ETF list: {e}")
            return {}

    @staticmethod
    @st.cache_data
    def get_all_mutual_funds():
        """
        Fetches all Open Ended Mutual Funds.
        Prioritizes MongoDB (populated by ingest_data.py).
        Fallbacks to mftool API if DB is empty.
        """
        try:
            # 1. Try fetching from DB first (Preferred)
            if FinancialTools.db.connected:
                db_schemes = FinancialTools.db.get_all_schemes()
                if db_schemes:
                    return db_schemes

            # 2. Fallback to API (Slow, but safe)
            all_schemes = FinancialTools.mf.get_scheme_codes()
            # Filter for Direct & Growth
            filtered_schemes = {}
            for code, name in all_schemes.items():
                if "Direct" in name and "Growth" in name:
                    filtered_schemes[code] = name
            
            return filtered_schemes
        except Exception as e:
            st.error(f"Error fetching Mutual Fund list: {e}")
            return {}

    @staticmethod
    def get_indian_ticker_suggestions(categories):
        """
        Maps user interest categories to specific NSE tickers.
        Returns a list of dicts: [{'ticker': '...', 'name': '...'}]
        """
        selected_assets = [] # List of dicts
        
        # --- STOCKS ---
        if "Stocks" in categories:
            # Fetch all NSE stocks mapping
            stock_map = FinancialTools.get_all_nse_stocks()
            all_tickers = list(stock_map.keys())
            
            # Prioritize NIFTY 500
            try:
                nifty_500 = capital_market.nifty500_equity_list()
                if 'Symbol' in nifty_500.columns:
                     targets = [f"{sym}.NS" for sym in nifty_500['Symbol'].tolist()]
                elif 'SYMBOL' in nifty_500.columns:
                     targets = [f"{sym}.NS" for sym in nifty_500['SYMBOL'].tolist()]
                else:
                    targets = all_tickers[:500]
                
                # Add to selected assets with names
                for t in targets:
                    if t in stock_map:
                        selected_assets.append({'ticker': t, 'name': stock_map[t]})
                    else:
                        selected_assets.append({'ticker': t, 'name': t.replace('.NS', '')})
            except:
                 # Fallback
                 for t in all_tickers[:500]:
                     selected_assets.append({'ticker': t, 'name': stock_map.get(t, t)})

        # --- MUTUAL FUNDS (Expanded List) ---
        if "Mutual Funds/ETFs" in categories:
            # 1. Get Dynamic ETF List (Listed)
            dynamic_etfs = FinancialTools.get_all_etfs()
            for t, n in dynamic_etfs.items():
                selected_assets.append({'ticker': t, 'name': n})
            
            # 2. Get All Mutual Funds (Unlisted/Open Ended)
            mfs = FinancialTools.get_all_mutual_funds()
            for code, name in mfs.items():
                selected_assets.append({'ticker': code, 'name': name})

        # --- GOLD/COMMODITIES ---
        if "Gold/Commodities" in categories:
             # Use ETFs for Gold
             dynamic_etfs = FinancialTools.get_all_etfs()
             for t, n in dynamic_etfs.items():
                 if 'GOLD' in t or 'SILVER' in t:
                     selected_assets.append({'ticker': t, 'name': n})
            
        # Remove duplicates (by ticker)
        unique_assets = {v['ticker']: v for v in selected_assets}.values()
        return list(unique_assets)

    @staticmethod
    def fetch_market_data(tickers, period="1y"):
        """
        Fetches historical data.
        - Uses yfinance for Stocks/ETFs (strings ending in .NS)
        - Uses mftool for Mutual Funds (numeric codes)
        """
        if not tickers:
            return {}, {} # Return separate dicts for YF and MF data
        
        yf_tickers = [t for t in tickers if isinstance(t, str) and ".NS" in t]
        mf_codes = [t for t in tickers if isinstance(t, str) and t.isdigit()] # MF codes are strings of digits
        
        yf_data = pd.DataFrame()
        mf_data = {}
        
        # 1. Fetch YFinance Data
        if yf_tickers:
            try:
                yf_data = yf.download(yf_tickers, period=period, group_by='ticker', progress=False)
            except Exception as e:
                st.error(f"Error fetching YF data: {e}")
        
        # 2. Fetch MF Data (mftool / DB)
        if mf_codes:
            progress_text = "Fetching Mutual Fund History..."
            my_bar = st.progress(0, text=progress_text)
            total = len(mf_codes)
            
            for i, code in enumerate(mf_codes):
                try:
                    hist_data = None
                    
                    # Try DB First (Fast)
                    if FinancialTools.db.connected:
                        hist_data = FinancialTools.db.get_nav_history(code)
                    
                    # If not in DB, fetch from API (Fallback)
                    if not hist_data:
                        hist = FinancialTools.mf.get_scheme_historical_nav(code)
                        if hist and 'data' in hist:
                            hist_data = hist['data']
                            # Note: We do NOT write back to DB here to avoid conflict with Ingestion Script
                    
                    if hist_data:
                        df = pd.DataFrame(hist_data)
                        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
                        df = df.dropna(subset=['date'])
                        df = df.set_index('date').sort_index()
                        df['nav'] = pd.to_numeric(df['nav'])
                        # Rename 'nav' to 'Close' to match yfinance structure
                        df = df.rename(columns={'nav': 'Close'})
                        
                        # Filter based on period
                        if period == "1y":
                            start_date = datetime.now() - timedelta(days=365)
                            df = df[df.index >= start_date]
                        elif period == "5y": # Approximate for "Long Term"
                             start_date = datetime.now() - timedelta(days=365*5)
                             df = df[df.index >= start_date]
                        elif period == "max":
                             pass # Keep all
                        else:
                             # Default to 1y if unknown
                             start_date = datetime.now() - timedelta(days=365)
                             df = df[df.index >= start_date]

                        mf_data[code] = df
                except:
                    pass
                my_bar.progress((i + 1) / total, text=f"Fetching MF {code}...")
            my_bar.empty()

        return yf_data, mf_data

    @staticmethod
    def calculate_technical_metrics(hist_data_tuple, ticker, name):
        """
        Fast calculation of technical metrics.
        hist_data_tuple: (yf_data, mf_data)
        """
        yf_data, mf_data = hist_data_tuple
        
        try:
            df = pd.DataFrame()
            
            # Determine source
            if ticker in mf_data:
                df = mf_data[ticker]
            elif not yf_data.empty:
                # Handle yfinance multi-index or single index
                if isinstance(yf_data.columns, pd.MultiIndex):
                    try:
                        df = yf_data[ticker].copy()
                    except KeyError:
                        return None
                else:
                    # If single ticker requested, yf returns single level cols
                    # But we usually request multiple.
                    # If single ticker in list, it might be just columns
                    if ticker in yf_data.columns: # This check is tricky for MultiIndex
                         pass 
                    # Fallback: check if columns have 'Close'
                    if 'Close' in yf_data.columns:
                         df = yf_data.copy()
                    else:
                         return None
            
            if df.empty:
                return None

            # Drop NaNs
            df = df.dropna()
            
            # --- Technical Indicators ---
            df['Daily_Return'] = df['Close'].pct_change()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Volatility (Annualized)
            volatility = df['Daily_Return'].std() * np.sqrt(252)
            
            # Returns (Absolute)
            current_price = df['Close'].iloc[-1]
            start_price = df['Close'].iloc[0]
            if start_price == 0:
                return None
            total_return = (current_price - start_price) / start_price
            
            # Sharpe Ratio (Risk Free Rate ~6%)
            risk_free_rate = 0.06
            sharpe_ratio = (total_return - risk_free_rate) / volatility if volatility != 0 else 0
            
            trend = "Bullish" if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1] else "Bearish"
            
            return {
                "Ticker": ticker,
                "Name": name,
                "Last_Price_INR": round(current_price, 2),
                "Return_1Y_Pct": round(total_return * 100, 2),
                "Volatility_Pct": round(volatility * 100, 2),
                "Sharpe_Ratio": round(sharpe_ratio, 2),
                "Trend": trend,
                "History": df['Close']
            }
        except Exception as e:
            return None

    @staticmethod
    def fetch_fundamentals(ticker):
        """
        Fetches fundamental data for a single ticker. Slow operation.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Helper to safely get value or "N/A"
            def get_val(key, fmt="{:.2f}"):
                val = info.get(key)
                if val is None: return "N/A"
                if isinstance(val, (int, float)): return fmt.format(val)
                return val

            # Helper for percentages
            def get_pct(key):
                val = info.get(key)
                if val is None:
                    return "N/A"
                return f"{val * 100:.2f}%"

            return {
                "Market_Cap_Cr": get_val('marketCap', "{:,.0f}"), # Raw value, will format later if needed
                "PE_Ratio": get_val('trailingPE'),
                "PB_Ratio": get_val('priceToBook'),
                "Industry_PE": get_val('industryTrailingPE') if 'industryTrailingPE' in info else "N/A", # Often not available directly, using sector/industry avg if possible or skip
                "Debt_to_Equity": get_val('debtToEquity'),
                "ROE": get_pct('returnOnEquity'),
                "EPS_TTM": get_val('trailingEps'),
                "Dividend_Yield": get_pct('dividendYield'),
                "Expense_Ratio": get_pct('annualReportExpenseRatio') if 'annualReportExpenseRatio' in info else "N/A" # For MFs
            }
        except Exception as e:
            return {
                "Market_Cap_Cr": "N/A", "PE_Ratio": "N/A", "PB_Ratio": "N/A", 
                "Debt_to_Equity": "N/A", "ROE": "N/A", "EPS_TTM": "N/A", 
                "Dividend_Yield": "N/A", "Expense_Ratio": "N/A"
            }

# ==========================================
# AGENT DEFINITIONS
# ==========================================

class Agent:
    def __init__(self, name, role, model):
        self.name = name
        self.role = role
        self.model = model
    
    def think(self, prompt):
        """Simulates the thinking process using Gemini LLM"""
        try:
            if not self.model:
                return "LLM Analysis unavailable (No API Key provided)."
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error in cognitive processing: {e}"

class MarketResearcher(Agent):
    def execute(self, user_prefs, tools):
        """
        Role: Identify the right instruments and fetch raw data.
        """
        with st.spinner(f"{self.name} is scanning the NSE/BSE markets..."):
            st.markdown(f"""<div class="agent-box researcher">
                        <div class="agent-title">🕵️ {self.name} (Market Researcher)</div>
                        <b>Action:</b> Querying Indian Market Indices...<br>
                        <b>Focus:</b> {', '.join(user_prefs['instruments'])}<br>
                        <b>Context:</b> Risk Profile: {user_prefs['risk']} | Horizon: {user_prefs['horizon']}
                        </div>""", unsafe_allow_html=True)
            
            # Returns list of dicts {'ticker': ..., 'name': ...}
            asset_list = tools.get_indian_ticker_suggestions(user_prefs['instruments'])
            tickers = [a['ticker'] for a in asset_list]
            
            # Returns tuple (yf_data, mf_data)
            raw_data = tools.fetch_market_data(tickers)
            
            st.session_state.shared_memory['raw_market_data'] = raw_data
            
            return {"assets": asset_list, "raw_data": raw_data}

class FinancialAnalyst(Agent):
    def execute(self, researcher_output, tools, user_risk_profile):
        """
        Role: Number crunching, modelling, filtering top candidates.
        """
        with st.spinner(f"{self.name} is running quantitative models in Sandbox..."):
            st.markdown(f"""<div class="agent-box analyst">
                        <div class="agent-title">👩‍💻 {self.name} (Financial Analyst)</div>
                        <b>Action:</b> Performing Volatility Analysis & Backtesting.<br>
                        <b>Models:</b> Sharpe Ratio, Risk Slabs, Fundamental Analysis.<br>
                        <b>Target:</b> Top performing assets matching user constraints.
                        </div>""", unsafe_allow_html=True)
            
            # --- RISK SLAB LOGIC ---
            # Volatility Slabs (Annualized SD)
            # Adjusted for Indian Equity Markets (Nifty Volatility ~12-15%, Stocks ~20-40%)
            risk_slabs = {
                "Ultra Conservative": (0, 5),    # Liquid / Arbitrage
                "Conservative": (5, 10),         # Debt / Conservative Hybrid
                "Moderate": (10, 20),            # Large Cap / Index
                "Aggressive": (20, 30),          # Mid Cap / Flexi Cap
                "Very Aggressive": (30, 40),     # Small Cap
                "Speculative / High Alpha": (40, 1000) # Micro Cap / High Beta
            }
            
            # Handle Range or Single Selection
            if isinstance(user_risk_profile, tuple):
                start_profile, end_profile = user_risk_profile
                # Find min of start and max of end
                min_vol = risk_slabs[start_profile][0]
                max_vol = risk_slabs[end_profile][1]
            else:
                min_vol, max_vol = risk_slabs.get(user_risk_profile, (0, 100))
            
            analyzed_assets = []
            assets = researcher_output['assets']
            data = researcher_output['raw_data'] # This is now a tuple (yf_data, mf_data)
            
            # 1. Technical Scan (Fast)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Debug counters
            total_scanned = 0
            passed_filter = 0
            
            for idx, asset in enumerate(assets):
                ticker = asset['ticker']
                name = asset['name']
                status_text.text(f"Scanning {name}...")
                # Pass the tuple 'data' directly
                metrics = tools.calculate_technical_metrics(data, ticker, name)
                if metrics:
                    total_scanned += 1
                    # Filter by Risk Slab immediately
                    vol = metrics['Volatility_Pct']
                    if min_vol <= vol <= max_vol:
                        analyzed_assets.append(metrics)
                        passed_filter += 1
                progress_bar.progress((idx + 1) / len(assets))
            
            status_text.empty()
            
            # Show Scan Results
            with st.expander("🕵️ Analysis Diagnostics", expanded=False):
                st.write(f"**Total Assets Identified:** {len(assets)}")
                st.write(f"**Data Available:** {total_scanned}")
                st.write(f"**Passed Risk Filter ({min_vol}% - {max_vol}% Volatility):** {passed_filter}")
                if passed_filter == 0:
                    st.warning("No assets matched your risk profile. Try widening the Risk Range or selecting a different profile.")
            
            df_analysis = pd.DataFrame(analyzed_assets)
            
            if df_analysis.empty:
                return pd.DataFrame()
            
            # 2. Select Top Candidates for Fundamental Analysis
            # Sort by Sharpe Ratio
            top_picks = df_analysis.sort_values(by="Sharpe_Ratio", ascending=False).head(20)
            
            # 3. Fetch Fundamentals (Slow) for Top Picks only
            st.info(f"Fetching fundamental data for top {len(top_picks)} candidates...")
            
            fundamental_data = []
            for index, row in top_picks.iterrows():
                ticker = row['Ticker']
                funds = tools.fetch_fundamentals(ticker)
                fundamental_data.append(funds)
            
            df_fundamentals = pd.DataFrame(fundamental_data, index=top_picks.index)
            
            # Merge Technical + Fundamental
            final_df = pd.concat([top_picks, df_fundamentals], axis=1)
            
            st.session_state.shared_memory['analyzed_metrics'] = final_df
            
            return final_df

class BusinessAnalyst(Agent):
    def execute(self, analyst_output, user_prefs):
        """
        Role: Qualitative synthesis, Thesis generation, Risk warnings.
        """
        with st.spinner(f"{self.name} is drafting the Investment Thesis..."):
            st.markdown(f"""<div class="agent-box reporter">
                        <div class="agent-title">🧑‍💼 {self.name} (Business Analyst)</div>
                        <b>Action:</b> Synthesizing Quantitative Data with Economic Context.<br>
                        <b>Objective:</b> Generate actionable recommendation report.
                        </div>""", unsafe_allow_html=True)
            
            if analyst_output.empty:
                return "No suitable assets found based on the analysis."

            # Prepare data context for LLM
            # Include new metrics in context
            cols_to_show = ['Name', 'Last_Price_INR', 'Return_1Y_Pct', 'Volatility_Pct', 'Sharpe_Ratio', 'PE_Ratio', 'Market_Cap_Cr', 'ROE']
            # Filter cols that exist
            cols_to_show = [c for c in cols_to_show if c in analyst_output.columns]
            
            # Use JSON format for unambiguous data parsing
            top_5_context = analyst_output.head(5)[cols_to_show].to_json(orient='records')
            
            # Identify the top 3 quantitative picks to ensure consistency with UI
            top_3_picks = analyst_output.head(3)['Name'].tolist()
            top_3_str = ", ".join(top_3_picks)
            
            current_date = datetime.now().strftime("%B %d, %Y")
            
            prompt = f"""
            You are a Senior Investment Strategist for the Indian Market.
            
            **Quantitative Analysis (Top Screened Assets - JSON Format):**
            {top_5_context}
            
            **Top 3 Quantitative Picks:** {top_3_str}
            
            **Task:**
            Generate a structured investment report following the EXACT format below. Do not deviate.
            
            **Required Output Format:**
            
            **Date:** {current_date}
            **Client Profile:** {user_prefs['risk']} Investor | Target: {user_prefs['return']} | {user_prefs['horizon']} | Goal: {user_prefs['goal']}
            
            ---
            
            # **Executive Summary**
            (Max 100 words: Synthesize the strategy tailored to the user's goal.)
            
            # **Top 3 Recommendations (Ranked)**
            1. **{top_3_picks[0] if len(top_3_picks) > 0 else 'Asset 1'}**: (Max 100 words: Focus on selection justification and fundamentals like P/E, ROE.)
            2. **{top_3_picks[1] if len(top_3_picks) > 1 else 'Asset 2'}**: (Max 100 words: Focus on selection justification and fundamentals.)
            3. **{top_3_picks[2] if len(top_3_picks) > 2 else 'Asset 3'}**: (Max 100 words: Focus on selection justification and fundamentals.)
            
            # **Portfolio Strategy**
            (Max 100 words: How these 3 assets fit together.)
            
            # **Indian Market Context**
            (Max 50 words: Relevant factors like Inflation, RBI policies, Sector growth.)
            
            # **Risk Factors**
            (Max 50 words: Warning about volatility or market conditions.)
            ---
            # **Disclaimer**
            "This report is generated by AI for informational purposes only and does not constitute financial advice. Past performance is not indicative of future results. Please consult a SEBI-registered investment advisor before making any investment decisions."
            
            **Constraints:**
            - **Tone:** Formal, professional, encouraging.
            - **Currency:** Use ₹ symbol.
            - **Consistency:** You MUST recommend the Top 3 Quantitative Picks listed above in that exact order.
            - **Data:** Use the provided JSON data accurately.
            """
            
            # If API key is present, use LLM
            if self.model:
                report = self.think(prompt)
            else:
                # Fallback heuristic rule-based response
                best_asset = analyst_output.iloc[0]
                report = f"### **Top Pick: {best_asset['Name']} ({best_asset['Ticker']})**\n\n" \
                         f"**Rationale:** Based on your {user_prefs['risk']} profile, this asset stands out with a **{best_asset['Return_1Y_Pct']}%** annual return.\n\n" \
                         f"**Fundamentals:** P/E: {best_asset.get('PE_Ratio', 'N/A')} | ROE: {best_asset.get('ROE', 'N/A')}\n\n" \
                         f"**Risk Note:** Volatility is {best_asset['Volatility_Pct']}%. Ensure this aligns with your {user_prefs['horizon']} timeline.\n\n" \
                         f"*(Note: Connect Gemini API Key for detailed thesis)*"

            st.session_state.shared_memory['final_thesis'] = report
            return report

# ==========================================
# MAIN APP LOGIC
# ==========================================

def main():
    # Sidebar: User Inputs
    with st.sidebar:
        st.header("⚙️ Indian Market Config")
        
        # API Key Logic: Check Secrets first, then Input
        default_api_key = ""
        use_manual_key = False
        
        if "GEMINI_API_KEY" in st.secrets:
            default_api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ API Key Loaded from Secrets")
            
            # Manual Override Option
            use_manual_key = st.checkbox("Manual Override API Key")
            
            if use_manual_key:
                api_key = st.text_input("Enter Manual API Key", type="password")
            else:
                api_key = default_api_key
        else:
            api_key_input = st.text_input("Gemini API Key", type="password", help="Required for the 'Business Analyst' to generate text reports.")
            api_key = api_key_input
        
        # Model Selection
        model_options = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-pro"]
        selected_model = st.selectbox("Select AI Model", model_options, index=0)
        
        st.divider()
        st.subheader("💾 Data Management")
        
        # MongoDB Connection Status
        if FinancialTools.db.connected:
            st.success("✅ MongoDB Connected")
            st.caption("Using remote data from Atlas.")
        else:
            st.error("❌ MongoDB Not Connected")
            st.caption("Check MONGO_URI in .streamlit/secrets.toml")

        st.divider()
        st.subheader("👤 Investor Profile")
        instruments = st.multiselect(
            "Investment Preference", 
            ["Stocks", "Mutual Funds/ETFs", "Gold/Commodities"],
            default=["Stocks", "Mutual Funds/ETFs"]
        )
        
        # Range Selection Toggle
        allow_range = st.checkbox("Allow Range Selection")
        
        risk_options = ["Ultra Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive", "Speculative / High Alpha"]
        return_options = [str(i) for i in range(6, 31)] + ["30+"]
        
        if allow_range:
            risk_appetite = st.select_slider("Risk Appetite Range", options=risk_options, value=("Conservative", "Moderate"))
            expected_return = st.select_slider("Target Return Range (CAGR %)", options=return_options, value=("10", "15"))
        else:
            risk_appetite = st.select_slider("Risk Appetite", options=risk_options, value="Moderate")
            expected_return = st.select_slider("Target Return (CAGR %)", options=return_options, value="12")
            
        horizon = st.selectbox("Time Horizon", ["Short Term (<1 yr)", "Medium Term (3-5 yrs)", "Long Term (5+ yrs)"])
        goal = st.text_input("Financial Goal", "Wealth Creation")
        
        start_btn = st.button("🚀 Analyze Market", type="primary")
        
        # Removed Supported Libraries section as requested

    st.title("🇮🇳 FinAgents: Indian Market Council")

    if start_btn:
        if not instruments:
            st.error("Please select at least one investment type.")
            return

        # Initialize LLM
        llm_model = None
        if api_key:
            genai.configure(api_key=api_key)
            llm_model = genai.GenerativeModel(selected_model)

        # Instantiate Agents
        researcher = MarketResearcher("Chanakya", "Market Researcher", llm_model)
        analyst = FinancialAnalyst("Aryabhata", "Financial Analyst", llm_model)
        reporter = BusinessAnalyst("Tagore", "Business Analyst", llm_model)
        tools = FinancialTools()

        user_prefs = {
            "instruments": instruments,
            "risk": risk_appetite,
            "return": expected_return,
            "horizon": horizon,
            "goal": goal
        }

        # --- ORCHESTRATION ---
        
        # 1. Researcher Agent
        research_results = researcher.execute(user_prefs, tools)
        
        # 2. Financial Analyst Agent
        # Pass user risk profile for slab filtering
        analysis_results = analyst.execute(research_results, tools, user_prefs['risk'])
        
        if analysis_results.empty:
            st.error("Analysis yielded no results. Try broadening your criteria or changing your Risk Appetite.")
            return

        # 3. Business Analyst Agent
        final_report = reporter.execute(analysis_results, user_prefs)

        # ==========================================
        # VISUALIZATION DASHBOARD
        # ==========================================
        st.divider()
        st.subheader("📊 The Council's Verdict")
        
        tab1, tab2, tab3 = st.tabs(["📑 Investment Thesis", "📈 Performance Lab", "📋 Raw Data"])
        
        with tab1:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(final_report)
            with col2:
                st.markdown("### Top Recommendation Metrics")
                best = analysis_results.iloc[0]
                st.metric("Asset", best['Name'])
                st.metric("Current Price", f"₹{best['Last_Price_INR']}")
                st.metric("1Y Return", f"{best['Return_1Y_Pct']}%", delta_color="normal")
                st.metric("Risk (Volatility)", f"{best['Volatility_Pct']}%", delta_color="inverse")
                st.divider()
                st.markdown("**Fundamentals**")
                st.metric("P/E Ratio", best.get('PE_Ratio', 'N/A'))
                st.metric("ROE", best.get('ROE', 'N/A'))

        with tab2:
            st.markdown("### Comparative Performance (Normalized)")
            st.caption("Comparing the growth of ₹100 invested 1 year ago across top picks.")
            
            fig = go.Figure()
            # Plot top 5 assets
            for index, row in analysis_results.head(5).iterrows():
                history = row['History']
                # Normalize: (Price / Start_Price) * 100
                normalized = (history / history.iloc[0]) * 100
                fig.add_trace(go.Scatter(x=normalized.index, y=normalized, mode='lines', name=row['Name']))
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Value of Investment (Indexed to 100)",
                template="plotly_white",
                height=450,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Bubble Chart for Risk vs Return
            st.markdown("### Risk vs Reward Landscape")
            
            # Ensure bubble size is positive (handle negative Sharpe Ratios)
            analysis_results['Bubble_Size'] = analysis_results['Sharpe_Ratio'].apply(lambda x: max(x, 0.01))
            
            fig_bubble = px.scatter(
                analysis_results,
                x="Volatility_Pct",
                y="Return_1Y_Pct",
                size="Bubble_Size",
                color="Trend",
                hover_name="Name",
                hover_data=["Ticker", "Sharpe_Ratio", "PE_Ratio", "ROE"],
                labels={"Volatility_Pct": "Risk (Volatility %)", "Return_1Y_Pct": "Return (%)"},
                title="Larger Bubble = Better Risk-Adjusted Return (Sharpe Ratio)"
            )
            st.plotly_chart(fig_bubble, use_container_width=True)

        with tab3:
            st.dataframe(analysis_results.drop(columns=['History', 'Bubble_Size'], errors='ignore'), use_container_width=True)

    else:
        # Welcome Screen
        st.info("👈 Enter your preferences in the sidebar to convene the council.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### 🕵️ Chanakya")
            st.markdown("*Market Researcher*")
            st.caption("Scans NSE/BSE for stocks, ETFs, and Gold.")
        with col2:
            st.markdown("### 👩‍💻 Aryabhata")
            st.markdown("*Financial Analyst*")
            st.caption("Runs mathematical models & backtests.")
        with col3:
            st.markdown("### 🧑‍💼 Tagore")
            st.markdown("*Business Analyst*")
            st.caption("Writes the final investment strategy.")

if __name__ == "__main__":
    main()
