import streamlit as st
import pandas as pd
import mysql.connector

# Database config
DB_CONFIG = {
    "host": "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    "user": "WuDkZhoePpAwKyn.root",
    "password": "5uya6Epti3kkwENe",
    "database": "vasan",
    "port": 4000
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Load data
def load_data():
    conn = get_connection()
    query = "SELECT * FROM bus_routes"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Streamlit App
st.title("🚌 RedBus Data Dashboard")

df = load_data()

if df.empty:
    st.warning("⚠️ No bus data found in database.")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("Filters")

    # Route filter
    routes = df["route_name"].dropna().unique().tolist()
    selected_routes = st.sidebar.multiselect("Select Routes", routes, default=routes)

    # Bus Type filter
    bus_types = df["bustype"].dropna().unique().tolist()
    selected_bustypes = st.sidebar.multiselect("Select Bus Types", bus_types, default=bus_types)

    # Price filter
    if df["price"].notna().any():
        min_price = float(df["price"].min())
        max_price = float(df["price"].max())
        if min_price < max_price:
            price_range = st.sidebar.slider("Select Price Range (INR)", min_value=min_price, max_value=max_price,
                                            value=(min_price, max_price))
        else:
            price_range = (min_price, max_price)
    else:
        price_range = (0, 0)

    # Star Rating filter
    if df["star_rating"].notna().any():
        min_rating = float(df["star_rating"].min())
        max_rating = float(df["star_rating"].max())
        if min_rating < max_rating:
            star_range = st.sidebar.slider("Select Star Rating", min_value=min_rating, max_value=max_rating,
                                           value=(min_rating, max_rating))
        else:
            star_range = (min_rating, max_rating)
    else:
        star_range = (0, 5)

    # Seats Availability filter
    if df["seats_available"].notna().any():
        min_seats = int(df["seats_available"].min())
        max_seats = int(df["seats_available"].max())
        if min_seats < max_seats:
            seat_range = st.sidebar.slider("Select Seats Available", min_value=min_seats, max_value=max_seats,
                                           value=(min_seats, max_seats))
        else:
            seat_range = (min_seats, max_seats)
    else:
        seat_range = (0, 0)

    # --- Apply Filters ---
    filtered_df = df[
        (df["route_name"].isin(selected_routes)) &
        (df["bustype"].isin(selected_bustypes)) &
        (df["price"].between(price_range[0], price_range[1], inclusive="both")) &
        (df["star_rating"].between(star_range[0], star_range[1], inclusive="both")) &
        (df["seats_available"].between(seat_range[0], seat_range[1], inclusive="both"))
    ]

    # --- Display Data ---
    st.subheader("Filtered Bus Data")
    st.write(f"Showing {len(filtered_df)} buses")
    st.dataframe(filtered_df)

   
