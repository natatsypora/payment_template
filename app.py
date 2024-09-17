import streamlit as st
import pandas as pd
from functions import *
from pandas.tseries.offsets import CustomBusinessDay
from streamlit_extras.add_vertical_space import add_vertical_space as avs
import xlsxwriter
from io import BytesIO
import pytz


#----------Page config-------------------------------------------------------
st.set_page_config(page_title="Payment list", page_icon="🗓️", layout="wide")

#=========== Using CSS Style =====================================
with open("style.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

# Define the properties for styling the dataframe
properties = {'background-color': 'rgba(255, 255, 255, 0.3)', 
              "font-size": "16px"}
#---------------------------------------------------------------

# Define the Google Drive file URL
buffer = BytesIO()

# Initialize the session state
if 'h_days' not in st.session_state:
    st.session_state.h_days = None

# Read CSV file
h_days = read_csv_data(url, parse_dates=['תאריך'])
# Convert the values in the column to Timestamp objects
h_days['תאריך'] = pd.to_datetime(h_days['תאריך'])

# Store data in the session state
st.session_state.h_days = h_days

# Define a custom business day frequency that includes Sundays
holidays = h_days['תאריך'].tolist()
custom_bd_6 = CustomBusinessDay(weekmask='Sun Mon Tue Wed Thu Fri', holidays=holidays)
custom_bd_5 = CustomBusinessDay(weekmask='Sun Mon Tue Wed Thu', holidays=holidays)
st.session_state.custom_bd_6 = custom_bd_6
st.session_state.custom_bd_5 = custom_bd_5

#----------Header and body------------------------------------------------------------   
st.markdown("<p style='text-align: center; color: rgb(10 39 67); font-size: 1.5em'>ברוכים הבאים לאתר שיעזור לכם להכין בקלות רשימת תשלומים בהתבסס על התאריך, הסכום, מספר התשלומים וימי העבודה בשבוע</p>", unsafe_allow_html=True)

avs(1)

tab1, tab2, tab3 = st.tabs(["תשלומים", "חגים בנקאיים",  "לוחות שנה"])
with tab1:
    tab_df, tab_img = st.columns(2)
    tab_img.image('image/Check-Printing.png')
    tab_img.write()

#----------Definition of tabs--------------------------------------------------------------
with tab2:    
    # Create the all holidays table
    all_bh = pd.crosstab(h_days['מועד'], 
                         h_days['שנה'],
                         values= h_days['תאריך'], 
                         aggfunc='min').sort_values(by=2024)
    for col in all_bh.columns:
        all_bh[col] = all_bh[col].apply(lambda x : x.strftime('%d-%m'))
    all_bh = all_bh.reset_index()  
    #Display the table chart
    st.plotly_chart(all_holidays_table(all_bh))
    #Add link buttons
    col_1, col_2, col_3 = st.columns(3)
    col_1.link_button('להוריד את הקובץ', url=url, help='Click to download the csv file', use_container_width=True)
    col_2.link_button(":rainbow[מועדי החופשות בבורסה]", "https://www.tase.co.il/he/content/knowledge_center/trading_vacation_schedule#vacations", use_container_width=True) 
    col_3.link_button('ימי פעילות מערכת זה"ב', "https://www.boi.org.il/roles/paymentsystems/ilpaymentsystems/zahav/", use_container_width=True)

with tab3:
    col_d, col_n = st.columns(2)
    col_d.link_button(":rainbow[לוח שנה דינמי עם חגים]", "https://dynamic-calendar.streamlit.app", use_container_width=True)
    col_n.link_button("לוח שנה שנתי עם חגים", "https://calendar.2net.co.il/annual-calendar.aspx", use_container_width=True)
with tab3.expander("2024 לוח שנה עם חגים"):
    st.image("image/calendar2024.jpg")
with tab3.expander("2025 לוח שנה עם חגים"):
    st.image("image/calendar2025.jpg")
with tab3.expander("2026 לוח שנה עם חגים"):
    st.image("image/calendar2026.jpg")        

#=================Sidebar========================================================
with st.sidebar:
        st.write(dt.now(pytz.timezone('Israel')).strftime("Today is %A : **%d %B %Y**"), unsafe_allow_html=True)
        st.write(dt.now(pytz.timezone('Israel')).strftime("&emsp;Current time : **%H:%M %p**"), unsafe_allow_html=True)
        st.divider()
choose = st.sidebar.radio(
        "בחר תבנית ליצירת הרשימה",
        ["**מתחיל מתאריך**", "**התאריך הממוצע**"],
        index=0)
workdays = st.sidebar.radio(
            "בחר את מספר ימי העבודה בשבוע",
            ['5', '6'],
            index=0)

#-------------**מתחיל מתאריך**---------------------------------------------
if choose == "**מתחיל מתאריך**":
    date_from = st.sidebar.date_input("בחר תאריך תחילת התשלום ", value=None)  
    if date_from == None:
        st.stop()  
    if date_from < dt.now(pytz.timezone('Israel')).date():
        st.sidebar.warning('יום התשלום הראשון לא יכול להיות מוקדם יותר מאשר היום', icon="🚨")
        st.stop()
    else: 
        sum_of_payments = st.sidebar.number_input("הזן את סכום כולל לתשלום", min_value=0, format="%.0d", step=10_000)                   
        n_payments = st.sidebar.number_input("הזן את מספר התשלומים", min_value=0, format="%.0d", step=1)        
        st.sidebar.write('')
        if n_payments and sum_of_payments != 0:
            st.session_state.n_payments = n_payments    
            st.session_state.sum_of_payments = sum_of_payments
            st.session_state.date_from = date_from
            st.session_state.workdays = workdays
            st.session_state.choose = choose
            if workdays == '5':
                    custom_bd = custom_bd_5
            elif workdays == '6':
                    custom_bd = custom_bd_6
            go = st.sidebar.button("לייצר רשימת התשלומים", use_container_width=True)
            if go:
                try:   
                    # Create the list of payments and workdays for the start date
                    df_start = sequence_workdays_start(date_from, custom_bd, sum_of_payments, n_payments) 
                    tab_df.dataframe(df_start.style.format({'payments':'{:,.0f}'}).set_properties(**properties), height=740 , width=300)  
                except Exception as e:
                    st.warning (e, icon="🚨") 
                    st.stop()
                message = f'''<p style="text-align: center;">
                            רשימה תוצרת כעת עם <b>{n_payments}</b> תשלומים<br>
                            בסכום של <b>{sum_of_payments:,.0f}</b> ש"ח
                            כולל <br> מתאריך <b>{date_from}</b>
                            <br> ו-<b>{workdays}</b> יומיים עבודה בשבוע
                            '''
                tab_img.markdown(message, unsafe_allow_html=True)              
                 
                #---------------------------------------------------------------
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    # Write  dataframe as a worksheet
                    df_start.to_excel(writer, sheet_name='payments')    

                    # Close the Pandas Excel writer and output the Excel file to the buffer
                    writer.close()

                tab_img.download_button(use_container_width=True,
                        label="Download The File as Excel worksheet",
                        data=buffer,
                        file_name="payments_start.xlsx",
                        mime="application/vnd.ms-excel")
                tab_img.image("image/save_as_scv2.jpg")                
                
#-------------**התאריך הממוצע**-------------------------------------------    
if choose == "**התאריך הממוצע**":
    middle_date = st.sidebar.date_input("בחר תאריך הממוצע לתשלום ", value=None)  
    if middle_date == None:
        st.stop()  
    if middle_date < dt.now(pytz.timezone('Israel')).date():
        st.sidebar.warning('התאריך הממוצע לא יכול להיות מוקדם יותר מאשר היום', icon="🚨")
        st.stop()
    else: 
        sum_of_payments = st.sidebar.number_input("הזן את סכום כולל לתשלום", min_value=0, format="%.0d", step=10_000)                   
        n_payments = st.sidebar.number_input("הזן את מספר התשלומים", min_value=0, format="%.0d", step=1)        
        st.sidebar.write('')
        if n_payments and sum_of_payments != 0:
            st.session_state.n_payments = n_payments    
            st.session_state.sum_of_payments = sum_of_payments
            st.session_state.midlle_date =middle_date
            st.session_state.workdays = workdays
            st.session_state.choose = choose
            if workdays == '5':
                    custom_bd = custom_bd_5
            elif workdays == '6':
                    custom_bd = custom_bd_6
            do_it = st.sidebar.button("לייצר רשימת התשלומים", use_container_width=True)
            if do_it:
                try:   
                    # Create the list of payments and workdays for the middle date
                    df_middle = sequence_workdays_middle(middle_date, custom_bd, sum_of_payments, n_payments) 
                    tab_df.dataframe(df_middle.style.format({'payments':'{:,.0f}'}).set_properties(**properties), height=740 , width=300)  
                except Exception as e:
                    st.warning (e, icon="🚨") 
                    st.stop()
                message = f'''<p style="text-align: center;">
                            רשימה תוצרת כעת עם <b>{n_payments}</b> תשלומים<br>
                            בסכום של <b>{sum_of_payments:,.0f}</b> ש"ח
                            כולל <br> התאריך הממוצע <b>{middle_date}</b>
                            <br> ו-<b>{workdays}</b> יומיים עבודה בשבוע
                            '''                
                tab_img.markdown(message, unsafe_allow_html=True)

                #---------------------------------------------------------------
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    # Write  dataframe as a worksheet
                    df_middle.to_excel(writer, sheet_name='payments')    

                    # Close the Pandas Excel writer and output the Excel file to the buffer
                    writer.close()

                tab_img.download_button(use_container_width=True,
                        label="Download The File as Excel worksheet",
                        data=buffer,
                        file_name="payments_middle.xlsx",
                        mime="application/vnd.ms-excel")
                tab_img.image("image/save_as_scv2.jpg")                         
               
with st.sidebar:    
    avs(5)         # add 5 vertical spaces
    st.divider()    # add a horizontal line  
    st.markdown("""
                <p style="text-align: center;">Made with 🤍 by Natalia</p>""" 
                , unsafe_allow_html=True)                  
                             