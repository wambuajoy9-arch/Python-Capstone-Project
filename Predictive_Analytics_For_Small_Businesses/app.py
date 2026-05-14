import pandas as pd 
import streamlit as st
# Load the data
data = pd.read_csv("Predictive_Analytics_For_Small_Businesses/Cleaned_Data.csv")
data["date"] = pd.to_datetime(data["date"], errors="coerce")
data = data.dropna(subset=["date"])
# Extract Year
data["Year"] = data["date"].dt.year
st.title("Commodity Price Predictor")
st.markdown("Upload the cleaned dataset to predict future prices, demand and restocking needs")
st.sidebar.header("User Inputs")
# Calculate the average price per Year 
average_price_per_year = data.groupby(["Year","commodity"])["price"].mean().reset_index()

# Filter one commodity, predictictions are usually done per commodity
# Show the available commodities
commodity = average_price_per_year['commodity'].unique()
selected_commodity = st.sidebar.selectbox("Select Commodity", commodity)
#Filter the data of the selected commodity
filtered_data = average_price_per_year[average_price_per_year["commodity"] == selected_commodity]
# Calculating the Growth Rate
data["GrowthRate"] = data["price"].pct_change()
average_growth = data["GrowthRate"].mean()
# This calculates the average growth rate

# The user inputs the year they'd like to predict the price
Year = st.sidebar.number_input("Enter the year to predict",min_value=2027, max_value=2040, value=2027)
# Get the data of the last year before predicted year
Last_Year = filtered_data["Year"].iloc[-1]
# .iloc[-1] gets the data of the latest year in the year column
# Get the latest price in the price column
Latest_Price = filtered_data["price"].iloc[-1]
# Calculate years into the future(ahead)
Year_ahead = Year - Last_Year
# Get the future price
Future_Price = Latest_Price*(1+average_growth)**Year_ahead


print("Future_Price:",Future_Price)



## Predicting Demand
# first get the elasticity of the different categories 
def elasticity_by_category(category):
    category = category.lower() # puts your category in lowercase

    if category == "cereals and tubers":
        return -0.6
    elif category == "pulses and nuts":
        return -0.8
    elif category == "vegetables and fruits":
        return -0.9
    elif category == "oils and fats":
        return -0.5
    elif category == "meat,fish and eggs":
        return -1.3
    elif category == "dairy":
        return -0.9
    else:
        return -0.8 # this is a default value
    
# get the category data from the dataset

commodity_data = data[data["commodity"] == selected_commodity]
category= data[data["commodity"]== selected_commodity]["category"].iloc[0]
current_elasticity = elasticity_by_category(category)
    
# Getting the Demnad Index(this is a measure used to track how the demand of a product changes over time compared to a fixed starting point)
price_change_percentage = ((Future_Price-Latest_Price)/Latest_Price)*100
print("Price_Change_percentage:",price_change_percentage)
# Using 100 as my baseline to represent the current market equilibrium
Demand_Index = 100*(1+(current_elasticity*price_change_percentage))
print("Demand_Index:",Demand_Index)
if Demand_Index>= 100:
    print("The demand for the commodity is high,Increase the stock levels to make more sales")
elif 90<= Demand_Index< 100:
    print("The demand for the commodity is stable,Ensure the stock level is enough")
else:
    print("The demand is low,do not but more stock")
# Predicting Profit
# Predicting profit
Cost_price = st.sidebar.number_input(f"Enter buying price for {selected_commodity}", value=float(Latest_Price))
Predicted_Profit = Future_Price - Cost_price
print("Predicted_Profit:",Predicted_Profit)
Percentage_profit = (Predicted_Profit/Cost_price)*100
print("Percentage_profit:",Percentage_profit)
if Percentage_profit>= 30:
    print("the profit gain is high")
elif Percentage_profit>= 20:
    print("The profit gain is good")
else:
    print("low profit gain")

# Restock Alert System 
# The Restock alert system
# The user inputs the current stock and restock stock
Current_stock = st.sidebar.number_input("Current Stock Level", min_value=0, value=10)
Restock_threshold = st.sidebar.number_input("Restock Threshold", min_value=0, value=20)

# when to restock
# Restock Logic
st.divider()
if Current_stock < Restock_threshold:
    st.error(" Status: Time to Restock!")
    if Percentage_profit >= 20 and Demand_Index >= 90:
        st.success(" RESTOCK DECISION: APPROVED (Market conditions are favorable)")
    else:
        st.warning(" RESTOCK DECISION: DENIED (Low margins or demand)")
else:
    st.info("Status: Stock levels are sufficient")

