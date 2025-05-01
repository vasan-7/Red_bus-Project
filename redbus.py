import streamlit as st
import pandas as pd
import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Streamlit UI
st.title("Bus Route Scraper & MySQL Uploader")

uploaded_file = st.file_uploader("All_routes_buses.csv", type=["csv"])

if uploaded_file:
    df = pd.read_csv("/home/vasan/Downloads/Python/Project_Red_Bus/All_routes_buses.csv")
    st.success("CSV uploaded successfully.")

    if st.button("Scrape and Insert into MySQL"):
        driver = webdriver.Chrome()
        driver.maximize_window()
        all_buses_data = []

        for i,r in df.iterrows():
            links=r["link"]
            routes=r["route"]

            # Loop through each link
            driver.get(links)
            time.sleep(3)
            
            
            try:
                button = driver.find_elements(By.XPATH, "//div[@class='button']")
                button[0].click()
                time.sleep(3)
            except Exception as e:
                print("No button found or unable to click:", e)
                

            bus_names = driver.find_elements(By.XPATH, "//div[@class='travels lh-24 f-bold d-color']")
            bus_types = driver.find_elements(By.XPATH, "//div[@class='bus-type f-12 m-top-16 l-color evBus']")
            departing_times = driver.find_elements(By.XPATH, "//div[@class='dp-time f-19 d-color f-bold']")
            duration_times = driver.find_elements(By.XPATH, "//div[@class='dur l-color lh-24']")
            reaching_times = driver.find_elements(By.XPATH, "//div[@class='bp-time f-19 d-color disp-Inline']")
            star_ratings = driver.find_elements(By.XPATH, "//div[@class='lh-18 rating rat-green ']")
            prices = driver.find_elements(By.XPATH, "//div[@class='fare d-block']")
            seats_availabilities = driver.find_elements(By.XPATH, "//div[@class='seat-left m-top-16']")
            #print(bus_name,bus_type,departing_time,duration_time,reaching_time,star_rating,price,seats_availability)


            for idx in range(len(bus_names)):
                bus_data = {
                    "route": routes,
                    "link": links,
                    "Bus Name": bus_names[idx].text,
                    "Bus Type": bus_types[idx].text if idx < len(bus_types) else "N/A",
                    "Departing Time": departing_times[idx].text if idx < len(departing_times) else "N/A",
                    "Duration Time": duration_times[idx].text if idx < len(duration_times) else "N/A",
                    "Reaching Time": reaching_times[idx].text if idx < len(reaching_times) else "N/A",
                    "Star Rating": star_ratings[idx].text if idx < len(star_ratings) else "N/A",
                    "Price": prices[idx].text if idx < len(prices) else "N/A",
                    "Seats Availability": seats_availabilities[idx].text if idx < len(seats_availabilities) else "N/A",
                }
                all_buses_data.append(bus_data)
        driver.quit()
        data_df = pd.DataFrame(all_buses_data)
        st.success("Scraping completed successfully.")
        st.dataframe(data_df)

            # Data filters
        st.write("### Filter Data")
        selected_route = st.selectbox("Select Route", ["All"] + list(data_df["Route"].unique()))
        selected_type = st.selectbox("Select Bus Type", ["All"] + list(data_df["Bus Type"].unique()))

        filtered_df = data_df.copy()
        if selected_route != "All":
            filtered_df = filtered_df[filtered_df["Route"] == selected_route]
        if selected_type != "All":
            filtered_df = filtered_df[filtered_df["Bus Type"] == selected_type]

        st.write("### Filtered Data", filtered_df)

        # Analysis
        def extract_price(p):
            try:
                return float(p.replace("INR", "").replace("₹", "").replace(",", "").strip())
            except:
                return None

        filtered_df["Price Num"] = filtered_df["Price"].apply(extract_price)
        filtered_df["Rating Num"] = pd.to_numeric(filtered_df["Star Rating"], errors="coerce")

        st.write("### Summary")
        st.metric("Average Price", f"₹{filtered_df['Price Num'].mean():.2f}" if not filtered_df['Price Num'].isnull().all() else "N/A")
        st.metric("Average Rating", f"{filtered_df['Rating Num'].mean():.2f}" if not filtered_df['Rating Num'].isnull().all() else "N/A")

        # Insert to MySQL
        if st.button("Upload to MySQL"):
            try:
                conn = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='Dheeraj@123',
                    database='vasan',
                    port=3306
                )
                cursor = conn.cursor()

                create_query = """
                CREATE TABLE IF NOT EXISTS bus_routes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    route_name TEXT,
                    route_link TEXT,
                    busname TEXT,
                    bustype TEXT,
                    price DECIMAL(10,2),
                    seats_available INT,
                    departing_time TIME,
                    duration TEXT,
                    reaching_time TIME,
                    star_rating FLOAT
                );
                """
                cursor.execute(create_query)

                insert_query = """
                INSERT INTO bus_routes (
                    route_name, route_link, busname, bustype, price, seats_available,
                    departing_time, duration, reaching_time, star_rating
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                for i, r in filtered_df.iterrows():
                    price = extract_price(r["Price"])
                    seats = int(r["Seats Available"].split()[0]) if "Seats" in r["Seats Available"] else None
                    star = float(r["Star Rating"]) if r["Star Rating"] != "N/A" else None

                    values = (
                        r["Route"], r["Link"], r["Bus Name"], r["Bus Type"],
                        price, seats, r["Departing Time"], r["Duration"],
                        r["Reaching Time"], star
                    )
                    cursor.execute(insert_query, values)

                conn.commit()
                st.success("✅ Data uploaded to MySQL successfully.")

            except Exception as e:
                st.error(f"❌ MySQL Upload Failed: {e}")
        
    