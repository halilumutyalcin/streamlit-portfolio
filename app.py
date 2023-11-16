import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

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



username = st.selectbox("Profil Seç", ['umut', 'hakan', 'genel'])


def calculate_current_value(ort_maliyet, adet, güncel_fiyat):
    return adet * güncel_fiyat - ort_maliyet

    # Display accessible stocks for the selected user
from config import profiles

if username != 'genel':
    st.success(f"Hoş Geldiniz {username}!")

    # Display accessible stocks for the authenticated user
    accessible_stocks = profiles[username]['AccessibleStocks']
    # Remove the stock selection
    # selected_stocks = st.multiselect("Hisse Kodlarını Seçin", accessible_stocks)

    # If there are accessible stocks, fetch and display the trade information
    if accessible_stocks:
        trades_df = profiles[username]['Trades'].loc[profiles[username]['Trades']['Hisse'].isin(accessible_stocks)]
        trades_df['Pozisyon Günü'] = trades_df['Alım Tarihi'].apply(get_position_days)

        # Print the first accessible stock's current price (assuming there is at least one accessible stock)
        print(float(get_stock_data(accessible_stocks[0])['Son İşlem Fiyatı'][0][1:].replace(",", ".")))

        # Add a check for an empty DataFrame before accessing its elements
        trades_df['Güncel Fiyat'] = trades_df.apply(
            lambda row: round(float(get_stock_data(row['Hisse'])['Son İşlem Fiyatı'][0][1:].replace(",", ".")),2),
            axis=1,
        )

        trades_df['Tutar'] = trades_df.apply(
            lambda row: calculate_current_value(
                row['Ort. Maliyet'],
                row['Adet'],
                round(float(get_stock_data(row['Hisse'])['Son İşlem Fiyatı'][0][1:].replace(",", ".")),2)
            ),
            axis=1,
        )

        # trades_df['Tutar'] = trades_df.apply(
        #     lambda row: int(round(row['Tutar'],2)) if isinstance(row['Tutar'], (int, float)) else row['Tutar'],
        #     axis=1,
        # )



        trades_df = trades_df.sort_values(by='Tutar', ascending=False)
        # Display the data
        st.subheader("Hisse Bilgileri")
        st.dataframe(trades_df)


else:
    selected_stocks = st.multiselect("Hisse Kodlarını Seçin", liste_guncelle().index)
    # # Eğer kullanıcı bir hisse seçtiyse devam et

    if selected_stocks:
        result_df = pd.DataFrame(
            columns=['Hisse Kodu', 'Açılış Fiyatı', 'Son İşlem Fiyatı', 'Günlük Değişim (TL)', 'Günlük Değişim %',
                     'Haftalık En Düşük', 'Haftalık En Yüksek', 'Aylık En Düşük', 'Aylık En Yüksek', 'Alış', 'Satış',
                     'Sermaye'])

        for s in selected_stocks:
            result_df = pd.concat([result_df, get_stock_data(s)], ignore_index=True)

        st.subheader("Seçilen Hisse Fiyatları")
        st.dataframe(result_df.drop(
            ['Satış', 'Piyasa Değeri', 'Yabancı Oranı (%)', 'Alış', 'Sermaye', 'Aylık En Yüksek', 'Haftalık En Yüksek',
             'Haftalık En Düşük', 'Aylık En Düşük'], axis=1))

    else:
        st.warning("Lütfen en az bir hisse seçin.")