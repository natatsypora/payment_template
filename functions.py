import pandas as pd
import streamlit as st
from datetime import date, timedelta, datetime as dt
import plotly.graph_objects as go
import pytz


#Define colors for the table
bg_head='#BCD9EC'
bg_body='rgba(255, 255, 255, 0.3)'
f_color_title='#1E5473'
line_color='#536490'

# Define the Google Drive file URL for 'bank_holidays.csv
url = 'https://drive.google.com/file/d/1m7Z6umeKpMj-rikz_wjvId7zIyUZ5yTF/view?usp=sharing'

# Define the function to get the file path and download the file
def get_path_from_url(url):
    path = url.split('/')[-2]
    file_path = 'https://drive.google.com/uc?export=download&id=' + path
    return file_path
# Define the function to read the csv
@st.cache_data
def read_csv_data(url, **kwargs):
    file_path = get_path_from_url(url)
    df = pd.read_csv(file_path)

    return df

#=========Define function for creating the list of payments =====
@st.cache_data
def list_of_payments(sum_of_payments, n_payments):
    payment = round(sum_of_payments / n_payments, 0)
    payments = [payment for i in range(n_payments) ]
    delta = sum_of_payments - n_payments * payment
    if delta != 0 : 
        payments[0]+= delta

    return payments  

#=========Define functions for creating the list of workdays ====
@st.cache_data
def sequence_workdays_middle(middle_date, custom_bd, sum_of_payments, n_payments):
    if n_payments == 1:
        st.warning('מספר התשלומים לתאריך הממוצע צריך להיות גדול מ 1', icon="🚨")
        st.stop()
    else:
        # Calculate the number of workdays before and after the middle date 
        before = round(n_payments/2, 0)
        after = n_payments - before  
        
        # Generate workdays before the middle date
        range_before = pd.date_range(start=middle_date,
                                     periods=before,
                                     freq=-custom_bd,
                                     name='pay_days')    
        min_day = range_before.min().date()
        if min_day < dt.now(pytz.timezone('Israel')).date():
            st.warning(f'תאריך תשלום מינימלי הוא {min_day}.\
                       שנה את התאריך,יום התשלום הראשון לא יכול להיות מוקדם יותר מאשר היום', icon= "🚨") 
            st.stop()       
        else:  
            # Generate workdays after the middle date
            range_after = pd.date_range(start=range_before.max() + pd.Timedelta(days=1),
                                        periods=after,
                                        freq=custom_bd,
                                        name='pay_days') 
            # Create dataframe from range of dates and payments
            df_dates = pd.DataFrame(data=range_before.union(range_after),
                                    index=range(1, n_payments + 1))
            df_dates['payments'] = list_of_payments(sum_of_payments, n_payments)
            # Convert 'pay_days' column to the date part
            df_dates['pay_days'] = pd.to_datetime(df_dates['pay_days']).dt.date  

            return df_dates  
                            
@st.cache_data
def sequence_workdays_start(start_date, cust_freq, sum_of_payments, n_payments):
    date_range = pd.date_range(start=start_date, periods=n_payments,
                               freq=cust_freq, name='pay_days')
    df_dates = pd.DataFrame(data=date_range,
                            index=range(1, n_payments + 1))
    df_dates['payments'] = list_of_payments(sum_of_payments, n_payments)
    df_dates['pay_days'] = pd.to_datetime(df_dates['pay_days']).dt.date

    return df_dates

#----------All Holidays Table --------------------------------------
@st.cache_data
def all_holidays_table(all_bh):   
        fig = go.Figure(data=[go.Table(
        columnwidth = [150]+[50]*10,
        header = dict(
            values = [f'<b>{h}<b>' for h in all_bh.columns],            
            fill_color=bg_head,
            font_size=16, font_color='rgba(0, 0, 0, 0.7)',
            height=40),
        cells=dict(
            values=all_bh.T.values,            
            fill_color=[bg_head]+[bg_body]*10,
            font_size=16,
            height=35))
        ])
        fig.update_layout(title=f'Bank Holidays 2024-2033', title_x=0.4, 
                          title_font_size=20, title_font_color=f_color_title,
                          width=800, height=all_bh.shape[0]*35+150, 
                          margin=dict(l=10, r=10, b=10, t=70))
        return fig


