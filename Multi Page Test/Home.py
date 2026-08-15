import streamlit as st
from shared_lib import load_css

# Page Configuration
st.set_page_config(
    page_title="FinAgents India: User Profile",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
load_css()

# Main Content: Title and Config
st.title("🇮🇳 FinAgents India: User Profile")
st.markdown("### Setup your Investment Persona")

# Configuration (Moved from Sidebar)
with st.expander("⚙️ System Configuration", expanded=False):
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.success("✅ Database Connected (Supabase)" if st.secrets.get("SUPABASE_URL") else "❌ Database NOT Connected")

# Main Content: User Inputs
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🎯 Investment Goals")
    investment_goal = st.selectbox(
        "Primary Goal",
        ["Wealth Creation", "Retirement Planning", "Tax Saving (ELSS)", "Short Term Gains", "Passive Income"]
    )
    investment_horizon = st.select_slider(
        "Investment Horizon",
        options=["Short Term (<1 Yr)", "Medium Term (1-3 Yrs)", "Long Term (3-5 Yrs)", "Wealth Creation (5+ Yrs)"]
    )
    capital = st.number_input("Capital to Deploy (₹)", min_value=1000, value=100000, step=5000)

with col2:
    st.markdown("#### ⚖️ Risk & Preferences")
    risk_profile = st.select_slider(
        "Risk Appetite",
        options=["Ultra Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive", "Speculative / High Alpha"],
        value="Moderate"
    )
    instruments = st.multiselect(
        "Investment Preference",
        ["Stocks", "Mutual Funds/ETFs", "Gold/Commodities"],
        default=["Stocks", "Mutual Funds/ETFs"]
    )
    expected_return = st.slider("Expected Annual Return (%)", 5, 50, 15)

# Save to Session State
if st.button("Save Profile & Proceed ➡️"):
    st.session_state['user_profile'] = {
        'goal': investment_goal,
        'horizon': investment_horizon,
        'capital': capital,
        'risk': risk_profile,
        'instruments': instruments,
        'return': f"{expected_return}%",
        'api_key': api_key
    }
    st.success("Profile Saved! Please navigate to **'Analysis'** in the sidebar.")
    # Optional: st.switch_page("pages/2_Analysis.py") if using Streamlit >= 1.30

# Debug Info
if 'user_profile' in st.session_state:
    with st.expander("Current Profile (Debug)"):
        st.json(st.session_state['user_profile'])
