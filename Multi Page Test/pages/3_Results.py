import streamlit as st
import pandas as pd
import plotly.express as px
from shared_lib import load_css

st.set_page_config(page_title="FinAgents: Results", page_icon="📈", layout="wide")
load_css()

st.title("📈 Final Investment Report")

# Check for Results
if 'analysis_results' not in st.session_state:
    st.info("ℹ️ No analysis results found. Please go to **Home** to setup profile and **Analysis** to run the workflow.")
    st.stop()

results = st.session_state['analysis_results']
final_thesis = results['thesis']
metrics_df = results['metrics']

# Display Thesis
st.markdown("### 📝 Investment Thesis")
st.markdown(final_thesis)

st.divider()

# Display Metrics
st.markdown("### 📊 Performance Metrics (Top Picks)")

if not metrics_df.empty:
    # Stylized Dataframe
    st.dataframe(
        metrics_df.style.background_gradient(subset=['Sharpe_Ratio', 'Return_1Y_Pct'], cmap="RdYlGn")
        .format({
            "Last_Price_INR": "₹{:.2f}", 
            "Return_1Y_Pct": "{:.2f}%", 
            "Volatility_Pct": "{:.2f}%",
            "Sharpe_Ratio": "{:.2f}"
        }),
        use_container_width=True
    )
    
    # Comparison Chart
    st.markdown("#### 🆚 Assets Comparison")
    
    # Sanitize data for plotting (Size cannot be negative)
    metrics_df['Size_Ref'] = metrics_df['Sharpe_Ratio'].apply(lambda x: max(0.1, float(x)))

    # Scatter Plot: Risk vs Return
    fig = px.scatter(
        metrics_df, 
        x="Volatility_Pct", 
        y="Return_1Y_Pct", 
        color="Trend", 
        size="Size_Ref",
        hover_data=["Name", "Ticker", "Sharpe_Ratio"],
        title="Risk (Volatility) vs Return (1Y)",
        labels={"Volatility_Pct": "Risk (Volatility %)", "Return_1Y_Pct": "Return (1Y %)"}
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No quantitative metrics available to display.")

# Raw Data Inspection
with st.expander("🔍 Inspect Raw Data (Debug)"):
    st.write(results['raw_data'])
