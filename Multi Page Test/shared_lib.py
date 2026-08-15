import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
from datetime import datetime, timedelta
import nselib
from nselib import capital_market
from mftool import Mftool
from supabase import create_client, Client

# ==========================================
# CUSTOM CSS
# ==========================================
def load_css():
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
# TOOL DEFINITIONS & CLASSES
# ==========================================

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
        
        if as_json:
            import json
            return json.dumps(scheme_info)
        return scheme_info

class DatabaseHandler:
    def __init__(self):
        self.url = st.secrets.get("SUPABASE_URL")
        self.key = st.secrets.get("SUPABASE_KEY")
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
        if not self.connected: return {}
        try:
            response = self.client.table("mf_schemes").select("scheme_code, scheme_name").execute()
            return {doc['scheme_code']: doc['scheme_name'] for doc in response.data}
        except:
            return {}

    def get_nav_history(self, scheme_code):
        if not self.connected: return None
        try:
            response = self.client.table("mf_nav_history").select("history").eq("scheme_code", scheme_code).execute()
            return response.data[0]['history'] if response.data else None
        except:
            return None

class FinancialTools:
    """A collection of tools for Indian Market Analysis."""
    mf = RobustMftool()
    db = DatabaseHandler()

    @staticmethod
    @st.cache_data
    def get_all_nse_stocks():
        try:
            df = capital_market.equity_list()
            if 'SYMBOL' in df.columns:
                mapping = {}
                for _, row in df.iterrows():
                    ticker = f"{row['SYMBOL']}.NS"
                    name = row.get('NAME OF COMPANY', row['SYMBOL']).title()
                    mapping[ticker] = name
                return mapping
            return {}
        except Exception as e:
            return {}

    @staticmethod
    @st.cache_data
    def get_all_etfs():
        try:
            equity_df = capital_market.equity_list()
            equity_symbols = set(equity_df['SYMBOL']) if 'SYMBOL' in equity_df.columns else set()
            bhav_df = pd.DataFrame()
            for i in range(5):
                date_check = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%Y')
                try:
                    bhav_df = capital_market.bhav_copy_with_delivery(date_check)
                    if not bhav_df.empty: break
                except: continue
            if bhav_df.empty: return {}

            traded_symbols = set(bhav_df[bhav_df['SERIES'] == 'EQ']['SYMBOL'])
            etf_symbols = traded_symbols - equity_symbols
            etf_map = {}
            for sym in etf_symbols:
                ticker = f"{sym}.NS"
                etf_map[ticker] = f"{sym} (ETF)"
            return etf_map
        except Exception as e:
            return {}

    @staticmethod
    @st.cache_data
    def get_all_mutual_funds():
        try:
            if FinancialTools.db.connected:
                db_schemes = FinancialTools.db.get_all_schemes()
                if db_schemes: return db_schemes
            
            all_schemes = FinancialTools.mf.get_scheme_codes()
            filtered_schemes = {}
            for code, name in all_schemes.items():
                if "Direct" in name and "Growth" in name:
                    filtered_schemes[code] = name
            return filtered_schemes
        except Exception as e:
            return {}

    @staticmethod
    def get_indian_ticker_suggestions(categories):
        selected_assets = []
        if "Stocks" in categories:
            stock_map = FinancialTools.get_all_nse_stocks()
            all_tickers = list(stock_map.keys())
            try:
                nifty_500 = capital_market.nifty500_equity_list()
                target_col = 'Symbol' if 'Symbol' in nifty_500.columns else 'SYMBOL'
                targets = [f"{sym}.NS" for sym in nifty_500[target_col].tolist()]
                for t in targets:
                    if t in stock_map:
                        selected_assets.append({'ticker': t, 'name': stock_map[t]})
                    else:
                        selected_assets.append({'ticker': t, 'name': t.replace('.NS', '')})
            except:
                for t in all_tickers[:500]:
                    selected_assets.append({'ticker': t, 'name': stock_map.get(t, t)})

        if "Mutual Funds/ETFs" in categories:
            dynamic_etfs = FinancialTools.get_all_etfs()
            for t, n in dynamic_etfs.items():
                selected_assets.append({'ticker': t, 'name': n})
            mfs = FinancialTools.get_all_mutual_funds()
            for code, name in mfs.items():
                selected_assets.append({'ticker': code, 'name': name})

        unique_assets = {v['ticker']: v for v in selected_assets}.values()
        return list(unique_assets)

    @staticmethod
    def fetch_market_data(tickers, period="1y"):
        if not tickers: return {}, {}
        yf_tickers = [t for t in tickers if isinstance(t, str) and ".NS" in t]
        mf_codes = [t for t in tickers if isinstance(t, str) and t.isdigit()]
        
        yf_data = pd.DataFrame()
        mf_data = {}
        
        if yf_tickers:
            try:
                yf_data = yf.download(yf_tickers, period=period, group_by='ticker', progress=False)
            except Exception as e:
                print(f"Error fetching YF data: {e}")
        
        if mf_codes:
            progress_text = "Fetching Mutual Fund History..."
            my_bar = st.progress(0, text=progress_text)
            total = len(mf_codes)
            for i, code in enumerate(mf_codes):
                try:
                    hist_data = None
                    if FinancialTools.db.connected:
                        hist_data = FinancialTools.db.get_nav_history(code)
                    if not hist_data:
                        hist = FinancialTools.mf.get_scheme_historical_nav(code)
                        if hist and 'data' in hist:
                            hist_data = hist['data']
                    
                    if hist_data:
                        df = pd.DataFrame(hist_data)
                        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
                        df = df.set_index('date').sort_index()
                        df['nav'] = pd.to_numeric(df['nav'])
                        df = df.rename(columns={'nav': 'Close'})
                        
                        if period == "1y":
                            start_date = datetime.now() - timedelta(days=365)
                            df = df[df.index >= start_date]
                        elif period == "5y":
                            start_date = datetime.now() - timedelta(days=365*5)
                            df = df[df.index >= start_date]
                        
                        mf_data[code] = df
                except: pass
                my_bar.progress((i + 1) / total, text=f"Fetching MF {code}...")
            my_bar.empty()
        return yf_data, mf_data

    @staticmethod
    def calculate_technical_metrics(hist_data_tuple, ticker, name):
        yf_data, mf_data = hist_data_tuple
        try:
            df = pd.DataFrame()
            if ticker in mf_data:
                df = mf_data[ticker]
            elif not yf_data.empty:
                if isinstance(yf_data.columns, pd.MultiIndex):
                    try: df = yf_data[ticker].copy()
                    except KeyError: return None
                else:
                    if 'Close' in yf_data.columns: df = yf_data.copy()
                    else: return None
            
            if df.empty: return None
            df = df.dropna()
            df['Daily_Return'] = df['Close'].pct_change()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            volatility = df['Daily_Return'].std() * np.sqrt(252)
            current_price = df['Close'].iloc[-1]
            start_price = df['Close'].iloc[0]
            total_return = (current_price - start_price) / start_price
            risk_free_rate = 0.06
            sharpe_ratio = (total_return - risk_free_rate) / volatility if volatility != 0 else 0
            trend = "Bullish" if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1] else "Bearish"
            return {
                "Ticker": ticker, "Name": name, "Last_Price_INR": round(current_price, 2),
                "Return_1Y_Pct": round(total_return * 100, 2), "Volatility_Pct": round(volatility * 100, 2),
                "Sharpe_Ratio": round(sharpe_ratio, 2), "Trend": trend, "History": df['Close']
            }
        except: return None

    @staticmethod
    def fetch_fundamentals(ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            def get_val(key, fmt="{:.2f}"):
                val = info.get(key)
                if val is None: return "N/A"
                if isinstance(val, (int, float)): return fmt.format(val)
                return val
            def get_pct(key):
                val = info.get(key)
                if val is None: return "0.0%"
                return f"{val * 100:.2f}%"
            return {
                "Market_Cap_Cr": get_val('marketCap', "{:,.0f}"), "PE_Ratio": get_val('trailingPE'),
                "PB_Ratio": get_val('priceToBook'), "Industry_PE": get_val('industryTrailingPE') if 'industryTrailingPE' in info else "N/A",
                "Debt_to_Equity": get_val('debtToEquity'), "ROE": get_pct('returnOnEquity'),
                "EPS_TTM": get_val('trailingEps'), "Dividend_Yield": get_pct('dividendYield'),
                "Expense_Ratio": get_pct('annualReportExpenseRatio') if 'annualReportExpenseRatio' in info else "N/A"
            }
        except:
             return {"Market_Cap_Cr": "N/A", "PE_Ratio": "N/A", "PB_Ratio": "N/A", "Debt_to_Equity": "N/A", "ROE": "N/A", "EPS_TTM": "N/A", "Dividend_Yield": "N/A", "Expense_Ratio": "N/A"}

# ==========================================
# AGENTS
# ==========================================

class Agent:
    def __init__(self, name, role, model):
        self.name = name
        self.role = role
        self.model = model
    
    def think(self, prompt):
        try:
            if not self.model: return "LLM Analysis unavailable (No API Key provided)."
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error in cognitive processing: {e}"

class MarketResearcher(Agent):
    def execute(self, user_prefs, tools):
        with st.spinner(f"{self.name} is scanning the NSE/BSE markets..."):
            st.markdown(f"""<div class="agent-box researcher">
                        <div class="agent-title">🕵️ {self.name} (Market Researcher)</div>
                        <b>Action:</b> Querying Indian Market Indices...<br>
                        <b>Focus:</b> {', '.join(user_prefs['instruments'])}<br>
                        <b>Context:</b> Risk Profile: {user_prefs['risk']} | Horizon: {user_prefs['horizon']}
                        </div>""", unsafe_allow_html=True)
            asset_list = tools.get_indian_ticker_suggestions(user_prefs['instruments'])
            tickers = [a['ticker'] for a in asset_list]
            raw_data = tools.fetch_market_data(tickers)
            if 'shared_memory' in st.session_state:
                st.session_state.shared_memory['raw_market_data'] = raw_data
            return {"assets": asset_list, "raw_data": raw_data}

class FinancialAnalyst(Agent):
    def execute(self, researcher_output, tools, user_risk_profile):
        with st.spinner(f"{self.name} is running quantitative models in Sandbox..."):
            st.markdown(f"""<div class="agent-box analyst">
                        <div class="agent-title">👩‍💻 {self.name} (Financial Analyst)</div>
                        <b>Action:</b> Performing Volatility Analysis & Backtesting.<br>
                        <b>Target:</b> Top performing assets matching user constraints.
                        </div>""", unsafe_allow_html=True)
            risk_slabs = {
                "Ultra Conservative": (0, 5), "Conservative": (5, 10), "Moderate": (10, 20),
                "Aggressive": (20, 30), "Very Aggressive": (30, 40), "Speculative / High Alpha": (40, 1000)
            }
            if isinstance(user_risk_profile, tuple):
                min_vol = risk_slabs[user_risk_profile[0]][0]
                max_vol = risk_slabs[user_risk_profile[1]][1]
            else:
                min_vol, max_vol = risk_slabs.get(user_risk_profile, (0, 100))
            
            analyzed_assets = []
            assets = researcher_output['assets']
            data = researcher_output['raw_data']
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, asset in enumerate(assets):
                ticker = asset['ticker']
                name = asset['name']
                status_text.text(f"Scanning {name}...")
                metrics = tools.calculate_technical_metrics(data, ticker, name)
                if metrics:
                    vol = metrics['Volatility_Pct']
                    if min_vol <= vol <= max_vol:
                        analyzed_assets.append(metrics)
                progress_bar.progress((idx + 1) / len(assets))
            status_text.empty()
            
            df_analysis = pd.DataFrame(analyzed_assets)
            if df_analysis.empty: return pd.DataFrame()
            
            top_picks = df_analysis.sort_values(by="Sharpe_Ratio", ascending=False).head(20)
            st.info(f"Fetching fundamental data for top {len(top_picks)} candidates...")
            fundamental_data = []
            for index, row in top_picks.iterrows():
                funds = tools.fetch_fundamentals(row['Ticker'])
                fundamental_data.append(funds)
            final_df = pd.concat([top_picks, pd.DataFrame(fundamental_data, index=top_picks.index)], axis=1)
            
            if 'shared_memory' in st.session_state:
                st.session_state.shared_memory['analyzed_metrics'] = final_df
            return final_df

class BusinessAnalyst(Agent):
    def execute(self, analyst_output, user_prefs):
        with st.spinner(f"{self.name} is drafting the Investment Thesis..."):
            st.markdown(f"""<div class="agent-box reporter">
                        <div class="agent-title">🧑‍💼 {self.name} (Business Analyst)</div>
                        <b>Action:</b> Synthesizing Quantitative Data with Economic Context.
                        </div>""", unsafe_allow_html=True)
            if analyst_output.empty: return "No suitable assets found."

            cols_to_show = [c for c in ['Name', 'Last_Price_INR', 'Return_1Y_Pct', 'Volatility_Pct', 'Sharpe_Ratio', 'PE_Ratio'] if c in analyst_output.columns]
            top_5_context = analyst_output.head(5)[cols_to_show].to_json(orient='records')
            top_3_picks = analyst_output.head(3)['Name'].tolist()
            top_3_str = ", ".join(top_3_picks)
            current_date = datetime.now().strftime("%B %d, %Y")
            
            prompt = f"""
            You are a Senior Investment Strategist for the Indian Market.
            Data: {top_5_context}
            Top 3 Picks: {top_3_str}
            Date: {current_date}
            Profile: {user_prefs['risk']} | Target: {user_prefs['return']} | {user_prefs['horizon']} | Goal: {user_prefs['goal']}
            
            Generate a structured investment report. 
            Executive Summary (100 words).
            Top 3 Recommendations (Ranked) with rationale.
            Portfolio Strategy.
            Indian Market Context.
            Risk Factors.
            Disclaimer.
            """
            
            if self.model:
                return self.think(prompt)
            else:
                best_asset = analyst_output.iloc[0]
                return f"### Top Pick: {best_asset['Name']}\nRationale: {best_asset['Return_1Y_Pct']}% Annual Return. Volatility: {best_asset['Volatility_Pct']}%. (Connect API Key for full thesis)."
