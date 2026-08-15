import streamlit as st
import google.generativeai as genai
from shared_lib import load_css, FinancialTools, MarketResearcher, FinancialAnalyst, BusinessAnalyst

st.set_page_config(page_title="FinAgents: Analysis", page_icon="🕵️", layout="wide")
load_css()

st.title("🕵️ Agent Workflow: Analysis")

# Check for Profile
if 'user_profile' not in st.session_state:
    st.warning("⚠️ User Profile not found. Please go back to **Home** to set up your profile.")
    st.stop()

user_prefs = st.session_state['user_profile']

# Setup Agents
api_key = user_prefs.get('api_key')
model = None
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

chanakya = MarketResearcher("Chanakya", "Market Researcher", model)
aryabhatta = FinancialAnalyst("Aryabhatta", "Quantitative Analyst", model)
vydur = BusinessAnalyst("Vydur", "Business Analyst", model)

# Execution
col1, col2 = st.columns([1, 2])

with col1:
    st.info(f"**Target:** {user_prefs['risk']} Portfolio\n\n**Focus:** {', '.join(user_prefs['instruments'])}")
    start_btn = st.button("🚀 Start Agent Workflow", type="primary")

if start_btn:
    with col2:
        # Phase 1: Research
        research_output = chanakya.execute(user_prefs, FinancialTools)
        
        # Phase 2: Analysis
        if research_output['assets']:
            analyst_output = aryabhatta.execute(research_output, FinancialTools, user_prefs['risk'])
            
            # Phase 3: Thesis (Drafting)
            # We will generate the thesis here but save it for the Results page
            final_thesis = vydur.execute(analyst_output, user_prefs)
            
            # Save Results
            st.session_state['analysis_results'] = {
                'metrics': analyst_output,
                'thesis': final_thesis,
                'raw_data': research_output['raw_data']
            }
            
            st.success("✅ Analysis Complete! Please navigate to **'Results'** in the sidebar to view the report.")
        else:
            st.error("No assets found for the selected criteria.")
