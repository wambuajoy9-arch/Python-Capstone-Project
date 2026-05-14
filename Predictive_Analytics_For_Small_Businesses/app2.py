import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Commodity Price Predictor", page_icon="📦", layout="wide")

st.title("Commodity Price Predictor")
st.markdown("Upload your cleaned dataset to predict future prices, demand, and restocking needs.")
# Helper functions
def elasticity_by_category(category: str) -> float:
    mapping = {
        "cereals and tubers": -0.6,
        "pulses and nuts": -0.8,
        "vegetables and fruits": -0.9,
        "oils and fats": -0.5,
        "meat,fish and eggs": -1.3,
        "dairy": -0.9,
    }
    return mapping.get(category.lower(), -0.8)


# Uploading the file
uploaded_file = st.file_uploader("Upload Cleaned_Data.csv", type=["csv"])

if uploaded_file is None:
    st.info("Please upload your CSV file to get started.")
    st.stop()

data_raw = pd.read_csv(uploaded_file)
data_raw["date"] = pd.to_datetime(data_raw["date"], errors="coerce")
data_raw = data_raw.dropna(subset=["date"])
data_raw["Year"] = data_raw["date"].dt.year

avg_price = (
    data_raw.groupby(["Year", "commodity"])["price"]
    .mean()
    .reset_index()
)

# Sidebar inputs 
st.sidebar.header("Settings")

commodities = sorted(avg_price["commodity"].unique())
commodity = st.sidebar.selectbox("Select commodity", commodities)

last_year = int(avg_price[avg_price["commodity"] == commodity]["Year"].max())
predict_year = st.sidebar.number_input(
    "Year to predict",
    min_value=last_year + 1,
    max_value=last_year + 20,
    value=last_year + 3,
    step=1,
)

cost_price = st.sidebar.number_input("Your cost price (buying price)", min_value=0.01, value=10.0, step=0.01)
current_stock = st.sidebar.number_input("Current stock level", min_value=0, value=100, step=1)
restock_threshold = st.sidebar.number_input("Restock alert threshold", min_value=0, value=30, step=1)

# Calculations 
commodity_data = avg_price[avg_price["commodity"] == commodity].copy().sort_values("Year")
commodity_data["GrowthRate"] = commodity_data["price"].pct_change() 
avg_growth = commodity_data["GrowthRate"].mean()

latest_price = commodity_data["price"].iloc[-1]
years_ahead = predict_year - last_year
future_price = latest_price * (1 + avg_growth / 100) ** years_ahead

# Demand
commodity_raw = data_raw[data_raw["commodity"] == commodity]
category = commodity_raw["category"].iloc[0] if "category" in commodity_raw.columns else "unknown"
elasticity = elasticity_by_category(category)
price_change_pct = ((future_price - latest_price) / latest_price) * 100
demand_index = 100 * (1 + (elasticity * price_change_pct / 100))

# Profit
predicted_profit = future_price - cost_price
pct_profit = (predicted_profit / cost_price) * 100

# Layout 
col1, col2, col3, col4 = st.columns(4)

col1.metric("Latest price", f"{latest_price:.2f}", help=f"Average price in {last_year}")
col2.metric(
    f"Predicted price ({predict_year})",
    f"{future_price:.2f}",
    delta=f"{price_change_pct:+.1f}%",
)
col3.metric("Demand index", f"{demand_index:.1f}", help="100 = current equilibrium")
col4.metric("Projected profit", f"{predicted_profit:.2f}", delta=f"{pct_profit:+.1f}%")

st.divider()

#Price history chat
st.subheader("Price history & forecast")

history_fig = go.Figure()
history_fig.add_trace(go.Scatter(
    x=commodity_data["Year"],
    y=commodity_data["price"],
    mode="lines+markers",
    name="Historical price",
    line=dict(width=2),
))
history_fig.add_trace(go.Scatter(
    x=[last_year, predict_year],
    y=[latest_price, future_price],
    mode="lines+markers",
    name="Forecast",
    line=dict(dash="dash", width=2),
    marker=dict(symbol="star", size=10),
))
history_fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Average price",
    legend=dict(orientation="h"),
    margin=dict(t=20),
)
st.plotly_chart(history_fig, use_container_width=True)

# Analysis cards
col_demand, col_profit, col_restock = st.columns(3)

with col_demand:
    st.subheader("Demand outlook")
    if demand_index >= 100:
        st.success("High demand — consider increasing stock to capture more sales.")
    elif demand_index >= 90:
        st.info("Stable demand — maintain current stock levels.")
    else:
        st.warning("Low demand — avoid purchasing additional stock.")
    st.caption(f"Elasticity used: {elasticity} (category: *{category}*)")
    st.caption(f"Avg annual growth rate: {avg_growth:.2f}%")

with col_profit:
    st.subheader("Profit outlook")
    if pct_profit >= 30:
        st.success(f"High profit gain ({pct_profit:.1f}%)")
    elif pct_profit >= 20:
        st.info(f"🔵 Good profit gain ({pct_profit:.1f}%)")
    elif pct_profit > 0:
        st.warning(f"Low profit gain ({pct_profit:.1f}%)")
    else:
        st.error(f"Selling below cost ({pct_profit:.1f}%)")
    st.caption(f"Cost price: {cost_price:.2f} → Predicted sell price: {future_price:.2f}")

with col_restock:
    st.subheader("Restock alert")
    needs_restock = current_stock < restock_threshold
    should_buy = pct_profit >= 20 and demand_index >= 90

    if needs_restock:
        if should_buy:
            st.error("Restock now — stock is low and conditions are favourable.")
        else:
            st.warning("Stock is low, but demand/profit conditions are unfavourable. Hold off.")
    else:
        st.success("Stock levels are sufficient.")
    st.caption(f"Current stock: {current_stock} | Threshold: {restock_threshold}")
# Raw data preview
with st.expander("View price history data"):
    st.dataframe(commodity_data.rename(columns={"price": "avg_price"}).reset_index(drop=True), use_container_width=True)
