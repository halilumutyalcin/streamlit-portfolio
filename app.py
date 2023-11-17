import json

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from tradingview_ta import TA_Handler, Interval

st.title("Hisse Fiyatları Analiz Uygulaması")


def liste_guncelle():
    url = "https://www.getmidas.com/canli-borsa/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the table element with class 'stock-table'
    table = soup.find('table', class_='stock-table')

    # Get column headers from the table header
    headers = [th.text.strip() for th in table.find('thead').find('tr').find_all('th')]

    # Initialize an empty list to store rows
    rows = []

    # Extract data from each row in the table body
    for row in table.find('tbody').find_all('tr'):
        # Get data from each cell in the row
        cells = [cell.text.strip() for cell in row.find_all(['td', 'th'])]
        # Append the row data to the list
        rows.append(cells)

    # Create a DataFrame with the extracted data
    df = pd.DataFrame(rows, columns=headers)

    # Set 'Hisse Kodu' as the index
    df.set_index('Hisse', inplace=True)

    # Display the DataFrame
    return df


def get_stock_data(stock_code):
    # URL of the page containing the data
    url = f"https://www.getmidas.com/canli-borsa/{stock_code.lower()}-hisse/"

    # Send an HTTP request to the URL and get the HTML content
    response = requests.get(url)
    html_content = response.content

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all elements with class 'data'
    data_elements = soup.find_all(class_='data')

    # Create a dictionary to store titles and values
    data_dict = {'Hisse Kodu': stock_code}

    # Extract titles and values from data elements and add to the dictionary
    for data in data_elements:
        title_elem = data.find('p', class_='title')
        val_elem = data.find('span', class_='val')

        # Check if both title and value elements are present
        if title_elem and val_elem:
            title = title_elem.text
            val = val_elem.text
            data_dict[title] = val

    df = pd.DataFrame([data_dict])

    return df

def get_stock_data2(stock):
    info = TA_Handler(
    symbol=stock,
    screener="turkey",
    exchange="BIST",
    interval=Interval.INTERVAL_1_DAY,
)
    return pd.DataFrame(
        columns=['Stock', 'Open', 'High', 'Low', 'Close', 'Change'],
        data=[[stock, info.get_indicators()['open'], info.get_indicators()['high'], info.get_indicators()['low'],
               info.get_indicators()['close'], info.get_indicators()['change']]]
    )

def get_position_days(alım_tarihi):
    alım_tarihi = datetime.strptime(alım_tarihi, "%Y-%m-%d")
    today = datetime.now()

    # Calculate the number of business days
    iş_günü_sayısı = 0
    current_date = alım_tarihi
    while current_date < today:
        if current_date.weekday() < 5:  # Monday to Friday are considered business days
            iş_günü_sayısı += 1
        current_date += timedelta(days=1)

    return iş_günü_sayısı


username = st.selectbox("Profil Seç", ['Umut', 'Hakan', 'Genel'], index=2)


def get_historical_prices(stock_code):
    # Calculate the date one month ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Fetch historical data using yfinance
    data = yf.download(stock_code + ".IS", start=start_date, end=end_date, progress=False)

    return data['Close']


def calculate_current_value(ort_maliyet, adet, güncel_fiyat):
    return adet * güncel_fiyat - ort_maliyet

    # Display accessible stocks for the selected user


def update_user_data(profiles):
    with open("profiles.json", "w", encoding="utf-8") as file:
        json.dump(profiles, file, ensure_ascii=False, indent=4)


# Load profiles from a JSON file
def load_user_data():
    try:
        with open("profiles.json", "r", encoding="utf-8") as json_file:
            profiles = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, return an empty dictionary
        profiles = {}
    return profiles

selected_page = st.sidebar.radio("Sayfa Seç", ["Hisse Al", "Hisse Görüntüle"],index=1)
profiles = load_user_data()


if selected_page == "Hisse Al":
    if 'Genel' != username:
        st.success(f"Hoş Geldiniz {username}!")

        st.subheader("Hisse Alım Bilgileri")

        new_stock_code = st.text_input("Hisse Kodu:")
        new_stock_purchase_price = st.number_input("Ort. Maliyet:", min_value=0.0)
        new_stock_quantity = st.number_input("Adet:", min_value=0)
        alım_tarihi = st.date_input("Alım Tarihi", value=None)

        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d")

        if st.button("Hisse Ekle"):
            new_trade = {
                'Hisse': new_stock_code,
                'Alım Tarihi': str(alım_tarihi),
                'Ort. Maliyet': new_stock_purchase_price,
                'Adet': new_stock_quantity,
            }
            profiles[username]['Trades'].append(new_trade)
            profiles[username]['AccessibleStocks'].append(new_stock_code)

            update_user_data(profiles)

            st.success(f"{new_stock_quantity} adet {new_stock_code} hissesi başarıyla eklendi!")
    else:

        st.text("Genel profilinde sadece hisse görüntüleytebilirsiniz!")

elif selected_page == "Hisse Görüntüle":
    if username != 'Genel':
        st.success(f"Hoş Geldiniz {username}!")

        accessible_stocks = profiles[username]['AccessibleStocks']

        if accessible_stocks:
            trades_df = pd.DataFrame(profiles[username]['Trades'])

            trades_df['Pozisyon Günü'] = trades_df['Alım Tarihi'].apply(get_position_days)
            # print(trades_df.columns)
            # print(get_stock_data("ENSRI").columns)
            trades_df['Güncel Fiyat'] = trades_df.apply(
                lambda row:
                    float(get_stock_data2(row['Hisse'])['Close']
                ),
                axis=1,
            )

            trades_df['Tutar'] = trades_df.apply(
                lambda row: calculate_current_value(
                    row['Ort. Maliyet'],
                    row['Adet'],

                        float(get_stock_data2(row['Hisse'])['Close'])

                ),
                axis=1,
            )

            total_portfolio_value = trades_df['Tutar'].sum()

            trades_df['Yüzde'] = (trades_df['Tutar'] / total_portfolio_value) * 100

            trades_df['Yüzde Kazanç'] = ((trades_df['Güncel Fiyat'] - trades_df['Ort. Maliyet']) / trades_df[
                'Ort. Maliyet']) * 100

            trades_df = trades_df.sort_values(by='Tutar', ascending=False)

            total_cost = (trades_df['Ort. Maliyet'] * trades_df['Adet']).sum()
            total_value = trades_df['Tutar'].sum()
            gain = total_value - total_cost
            percentage_gain = (gain / total_cost) * 100

            st.subheader("Hisse Bilgileri")
            trades_df = trades_df.reset_index(drop=True)
            st.dataframe(trades_df.drop(['Yüzde'],axis=1))
            st.subheader("Portföy Dağılımı (%)")
            st.bar_chart(trades_df.set_index('Hisse')['Yüzde'])

            additional_info_df = pd.DataFrame({
                'Bilgi': ['Toplam Maliyet', 'Toplam Tutar', 'Kazanç', 'Yüzde Kazanç'],
                'Değer': [total_cost, total_value, gain, percentage_gain]
            })

            # Format the numeric values in the additional_info_df DataFrame
            additional_info_df['Değer'] = additional_info_df['Değer'].apply(
                lambda x: '{:,.2f}'.format(x).replace(",", "").replace(".", ",")
            )

            # Display the 'Portföy Dağılımı' table (if trades_df is available)
            if 'Hisse' in trades_df.columns and 'Yüzde' in trades_df.columns:
                st.table(trades_df[['Hisse', 'Yüzde']].set_index('Hisse').style.format({'Yüzde': '{:.2f}%'}))

            # Display the table for additional information
            st.table(additional_info_df.set_index('Bilgi'))

            # Display the 'Portföy Dağılımı' table (if trades_df is available)

            # Display the additional information
            # st.text(portfolio_distribution_text)

    else:
        selected_stocks = st.multiselect("Hisse Kodlarını Seçin", liste_guncelle().index)

        if selected_stocks:
            result_df = pd.DataFrame(
                columns=['Stock','Open','High','Low','Close','Change'])

            for s in selected_stocks:
                result_df = pd.concat([result_df, get_stock_data2(s)], ignore_index=True)

            st.subheader("Seçilen Hisse Fiyatları ve Son 1 Ay Kapanış Fiyatları")

            # st.dataframe(result_df.drop(
            #     ['Satış', 'Piyasa Değeri', 'Yabancı Oranı (%)', 'Alış', 'Sermaye', 'Aylık En Yüksek', 'Haftalık En Yüksek',
            #      'Haftalık En Düşük', 'Aylık En Düşük'], axis=1))

            st.dataframe(result_df)

            historical_data = {}

            for s in selected_stocks:
                historical_data[s] = get_historical_prices(s)

            st.subheader("Son 1 Ay Kapanış Fiyatları")

            historical_prices_df = pd.DataFrame(historical_data)
            st.line_chart(historical_prices_df)

            update_user_data(profiles)
        else:
            st.warning("Lütfen en az bir hisse seçin.")