"""SuperKart sales forecasting - Streamlit frontend."""
import os

import pandas as pd
import requests
import streamlit as st

# Backend URL: the backend container name on the shared Docker network (overridable for local runs)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:7860")
REFERENCE_YEAR = 2025
PERISHABLES = ["Dairy", "Meat", "Fruits and Vegetables", "Breakfast", "Breads", "Seafood"]
PRODUCT_TYPES = ["Fruits and Vegetables", "Snack Foods", "Frozen Foods", "Dairy", "Household",
                 "Baking Goods", "Canned", "Health and Hygiene", "Meat", "Soft Drinks", "Breads",
                 "Hard Drinks", "Others", "Starchy Foods", "Breakfast", "Seafood"]
REQUIRED_COLUMNS = ["Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
                    "Store_Size", "Store_Location_City_Type", "Store_Type", "Product_Id_char",
                    "Store_Age_Years", "Product_Type_Category"]

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="centered")
st.title("🛒 SuperKart Sales Forecast")
st.write("Predict the total sales revenue of a product in a store, for one product or for a whole CSV file.")

# ---------------- Online (single) prediction ----------------
st.subheader("Single prediction")
with st.form("single_prediction"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Product**")
        product_family = st.selectbox("Product family (ID prefix)", ["FD - Food", "DR - Drinks", "NC - Non-consumable"])
        product_type = st.selectbox("Product type", PRODUCT_TYPES)
        sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
        weight = st.number_input("Product weight", min_value=0.0, max_value=50.0, value=12.66, step=0.1)
        mrp = st.number_input("Product MRP", min_value=0.0, max_value=1000.0, value=147.0, step=1.0)
        area = st.number_input("Allocated display area (ratio)", min_value=0.0, max_value=1.0,
                               value=0.068, step=0.001, format="%.3f")
    with col2:
        st.markdown("**Store**")
        store_type = st.selectbox("Store type", ["Supermarket Type2", "Supermarket Type1", "Departmental Store", "Food Mart"])
        store_size = st.selectbox("Store size", ["Medium", "High", "Small"])
        city_type = st.selectbox("City tier", ["Tier 2", "Tier 1", "Tier 3"])
        est_year = st.number_input("Store establishment year", min_value=1950, max_value=REFERENCE_YEAR,
                                   value=2009, step=1)
    submitted = st.form_submit_button("Predict sales", type="primary")

if submitted:
    payload = {
        "Product_Weight": weight,
        "Product_Sugar_Content": sugar,
        "Product_Allocated_Area": area,
        "Product_MRP": mrp,
        "Store_Size": store_size,
        "Store_Location_City_Type": city_type,
        "Store_Type": store_type,
        "Product_Id_char": product_family[:2],
        "Store_Age_Years": int(REFERENCE_YEAR - est_year),
        "Product_Type_Category": "Perishables" if product_type in PERISHABLES else "Non Perishables",
    }
    try:
        response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
        if response.ok:
            prediction = response.json()["Predicted_Sales"]
            st.success(f"Predicted sales revenue: **{prediction:,.2f}**")
            with st.expander("Request sent to the API"):
                st.json(payload)
        else:
            st.error(f"API error ({response.status_code}): {response.json().get('error', response.text)}")
    except requests.exceptions.RequestException as err:
        st.error(f"Could not reach the prediction API at {BACKEND_URL}: {err}")

# ---------------- Batch prediction ----------------
st.subheader("Batch prediction")
st.caption("CSV columns required: " + ", ".join(f"`{c}`" for c in REQUIRED_COLUMNS))
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    batch_df = pd.read_csv(uploaded_file)
    st.write(f"{len(batch_df)} rows loaded")
    st.dataframe(batch_df.head(), use_container_width=True)

    missing = [c for c in REQUIRED_COLUMNS if c not in batch_df.columns]
    if missing:
        st.error(f"The file is missing required column(s): {missing}")
    elif st.button("Predict for batch", type="primary"):
        try:
            uploaded_file.seek(0)
            response = requests.post(f"{BACKEND_URL}/v1/predictbatch",
                                     files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                                     timeout=60)
            if response.ok:
                predictions = response.json()
                batch_df["Predicted_Sales"] = [predictions[str(i)] for i in batch_df.index]
                st.success("Batch predictions completed!")
                st.dataframe(batch_df, use_container_width=True)
                st.metric("Total predicted sales", f"{batch_df['Predicted_Sales'].sum():,.2f}")
                st.download_button("Download predictions as CSV", batch_df.to_csv(index=False).encode("utf-8"),
                                   file_name="superkart_batch_predictions.csv", mime="text/csv")
            else:
                st.error(f"API error ({response.status_code}): {response.json().get('error', response.text)}")
        except requests.exceptions.RequestException as err:
            st.error(f"Could not reach the prediction API at {BACKEND_URL}: {err}")
