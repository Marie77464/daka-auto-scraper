import streamlit as st
import pandas as pd
import sqlite3
from requests import get
from bs4 import BeautifulSoup as bs
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="DAKA_AUTO_SCRAPER",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful design
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    h1 {
        color: #ffffff;
        text-align: center;
        font-size: 3.5em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        padding: 20px;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        to { text-shadow: 0 0 20px rgba(255,255,255,0.8); }
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF6B6B 0%, #FFE66D 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 15px 30px;
        border: none;
        font-size: 1.2em;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #4facfe 0%, #00f2fe 100%);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2em;
        color: #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# Database functions
def init_db():
    conn = sqlite3.connect('daka_auto.db')
    c = conn.cursor()
    
    # Table for cars
    c.execute('''CREATE TABLE IF NOT EXISTS voitures
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand TEXT, model TEXT, year TEXT, kilometer TEXT,
                  fuel_type TEXT, gearbox TEXT, adress TEXT,
                  owner TEXT, price TEXT, scraped_date TEXT)''')
    
    # Table for motos
    c.execute('''CREATE TABLE IF NOT EXISTS motos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand TEXT, year TEXT, kilometer TEXT,
                  adress TEXT, owner TEXT, price TEXT, scraped_date TEXT)''')
    
    # Table for car rental
    c.execute('''CREATE TABLE IF NOT EXISTS location
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand TEXT, year TEXT, adress TEXT,
                  owner TEXT, price TEXT, scraped_date TEXT)''')
    
    conn.commit()
    conn.close()

def save_to_db(df, table_name):
    df['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('daka_auto.db')
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

def load_from_db(table_name):
    conn = sqlite3.connect('daka_auto.db')
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# Scraping functions
def scrape_voitures(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f'Scraping page {index}/{num_pages}...')
        progress_bar.progress(index / num_pages)
        
        url = f'https://dakar-auto.com/senegal/voitures-4?&page={index}'
        res = get(url)
        soup = bs(res.content, 'html.parser')
        containers = soup.find_all('div', class_='listings-cards__list-item mb-md-3 mb-3')
        
        data = []
        for container in containers:
            try:
                gen_inf = container.find('h2', class_='listing-card__header__title mb-md-2 mb-0').a.text.strip().split()
                brand = gen_inf[0]
                model = " ".join(gen_inf[1:len(gen_inf)-1])
                year = gen_inf[-1]
                
                gen_inf1 = container.find('ul', 'listing-card__attribute-list list-inline mb-0')
                gen_inf2 = gen_inf1.find_all('li', 'listing-card__attribute list-inline-item')
                kms_driven = gen_inf2[1].text.replace('km','')
                gearbox = gen_inf2[2].text
                fuel_type = gen_inf2[3].text
                
                adress = container.find('div',class_='col-12 entry-zone-address').text
                owner = "".join(container.find('p', class_='time-author m-0').a.text).replace('Par','')
                price = "".join(container.find('h3','listing-card__header__price font-weight-bold text-uppercase mb-0').text.strip().split()).replace('FCFA','')
                
                dic = {
                    "brand": brand, "model": model, "year": year,
                    "kilometer": kms_driven, "fuel_type": fuel_type,
                    "gearbox": gearbox, "adress": adress,
                    "owner": owner, "price": price
                }
                data.append(dic)
            except:
                pass
        
        DF = pd.DataFrame(data)
        df = pd.concat([df, DF], axis=0).reset_index(drop=True)
    
    df = df.drop_duplicates()
    progress_bar.empty()
    status_text.empty()
    return df

def scrape_motos(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f'Scraping page {index}/{num_pages}...')
        progress_bar.progress(index / num_pages)
        
        url = f'https://dakar-auto.com/senegal/motos-and-scooters-3?&page={index}'
        res = get(url)
        soup = bs(res.content, 'html.parser')
        containers = soup.find_all('div', class_='listings-cards__list-item mb-md-3 mb-3')
        
        data = []
        for container in containers:
            try:
                gen_inf = container.find('h2', class_='listing-card__header__title mb-md-2 mb-0').a.text.strip().split()
                brand = gen_inf[0]
                year = gen_inf[-1]
                
                kms_driven = None
                gen_inf1 = container.find('ul', class_='listing-card__attribute-list list-inline mb-0')
                if gen_inf1:
                    gen_inf2 = gen_inf1.find_all('li', class_='listing-card__attribute list-inline-item')
                    if len(gen_inf2) > 1:
                        kms_driven = gen_inf2[1].text.replace('km', '')
                if not kms_driven:
                    kms_driven = "0"
                
                adress = container.find('div', class_='col-12 entry-zone-address').text
                owner = "".join(container.find('p', class_='time-author m-0').a.text).replace('Par','')
                price = "".join(container.find('h3', 'listing-card__header__price font-weight-bold text-uppercase mb-0').text.strip().split()).replace('FCFA','')
                
                dic = {
                    "brand": brand, "year": year, "kilometer": kms_driven,
                    "adress": adress, "owner": owner, "price": price
                }
                data.append(dic)
            except:
                pass
        
        DF = pd.DataFrame(data)
        df = pd.concat([df, DF], axis=0).reset_index(drop=True)
    
    df = df.drop_duplicates()
    progress_bar.empty()
    status_text.empty()
    return df

def scrape_location(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f'Scraping page {index}/{num_pages}...')
        progress_bar.progress(index / num_pages)
        
        url = f'https://dakar-auto.com/senegal/location-de-voitures-19?&page={index}'
        res = get(url)
        soup = bs(res.content, 'html.parser')
        containers = soup.find_all('div', class_='listings-cards__list-item mb-md-3 mb-3')
        
        data = []
        for container in containers:
            try:
                gen_inf = container.find('h2',class_='listing-card__header__title mb-md-2 mb-0').a.text.strip().split()
                brand = gen_inf[0]
                year = gen_inf[-1]
                
                owner = "".join(container.find('p',class_='time-author m-0').a.text).replace('Par','')
                adress = container.find('div', class_='col-12 entry-zone-address').text
                price = "".join(container.find('h3','listing-card__header__price font-weight-bold text-uppercase mb-0').text.strip().split()).replace('FCFA','')
                
                dic = {
                    "brand": brand, "year": year, "adress": adress,
                    "owner": owner, "price": price
                }
                data.append(dic)
            except:
                pass
        
        DF = pd.DataFrame(data)
        df = pd.concat([df, DF], axis=0).reset_index(drop=True)
    
    df = df.drop_duplicates()
    progress_bar.empty()
    status_text.empty()
    return df

# Initialize database
init_db()

# Main title
st.markdown("<h1> DAKA_AUTO_SCRAPER </h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/000000/car.png")
    st.markdown("###  Navigation")
    menu = st.radio(
        "",
        [" Home", " Scraper", " Dashboard", " View Data", " Web Evaluation App"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.info("DAKA_AUTO_SCRAPER is a powerful tool to scrape and analyze car data from Dakar-Auto.com")

# HOME PAGE
if menu == " Home":
    st.markdown("##  Welcome to DAKA_AUTO_SCRAPER!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Cars</h3>
            <p>Scrape detailed car listings including brand, model, year, and more!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Motos</h3>
            <p>Get information about motorcycles and scooters available in Senegal!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Rental</h3>
            <p>Explore car rental options with pricing and availability!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("###  Quick Start Guide")
    st.markdown("""
    1. **Go to Scraper** - Choose your data source and number of pages
    2. **Run the scraper** - Get fresh data from Dakar-Auto.com
    3. **View Dashboard** - Analyze the scraped data with beautiful charts
    4. **View Data** - Browse and download your scraped data
    5. **Web Evaluation** - Fill out evaluation forms
    """)

# SCRAPER PAGE
elif menu == " Scraper":
    st.markdown("##  Start Scraping")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url_choice = st.selectbox(
            " Select data source:",
            [" Voitures (Cars)", " Motos & Scooters", " Location de Voitures (Car Rental)"]
        )
    
    with col2:
        num_pages = st.number_input(" Number of pages:", min_value=1, max_value=50, value=1)
    
    st.markdown("---")
    
    if st.button(" Start Scraping", use_container_width=True):
        with st.spinner(' Scraping in progress...'):
            try:
                if "Voitures" in url_choice and "Location" not in url_choice:
                    df = scrape_voitures(num_pages)
                    save_to_db(df, 'voitures')
                    st.success(f' Successfully scraped {len(df)} cars!')
                    
                elif "Motos" in url_choice:
                    df = scrape_motos(num_pages)
                    save_to_db(df, 'motos')
                    st.success(f' Successfully scraped {len(df)} motos!')
                    
                elif "Location" in url_choice:
                    df = scrape_location(num_pages)
                    save_to_db(df, 'location')
                    st.success(f' Successfully scraped {len(df)} rental cars!')
                
                st.balloons()
                st.dataframe(df, use_container_width=True)
                
            except Exception as e:
                st.error(f' Error during scraping: {str(e)}')

# DASHBOARD PAGE
elif menu == " Dashboard":
    st.markdown("##  Data Analytics Dashboard")
    
    data_type = st.selectbox(
        "Select data to visualize:",
        ["Voitures", "Motos", "Location"]
    )
    
    table_map = {"Voitures": "voitures", "Motos": "motos", "Location": "location"}
    df = load_from_db(table_map[data_type])
    
    if len(df) > 0:
        # Remove scraped_date and id for analysis
        df_clean = df.drop(['scraped_date', 'id'], axis=1, errors='ignore')
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(" Total Records", len(df_clean))
        with col2:
            st.metric(" Unique Brands", df_clean['brand'].nunique())
        with col3:
            if 'price' in df_clean.columns:
                avg_price = df_clean['price'].str.replace(',', '').astype(float).mean()
                st.metric(" Avg Price (FCFA)", f"{avg_price:,.0f}")
        with col4:
            st.metric(" Latest Year", df_clean['year'].max() if 'year' in df_clean.columns else "N/A")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Brand distribution
            brand_counts = df_clean['brand'].value_counts().head(10)
            fig1 = px.bar(
                x=brand_counts.values,
                y=brand_counts.index,
                orientation='h',
                title="Top 10 Brands",
                labels={'x': 'Count', 'y': 'Brand'},
                color=brand_counts.values,
                color_continuous_scale='Viridis'
            )
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Year distribution
            if 'year' in df_clean.columns:
                year_counts = df_clean['year'].value_counts().sort_index()
                fig2 = px.line(
                    x=year_counts.index,
                    y=year_counts.values,
                    title="Vehicles by Year",
                    labels={'x': 'Year', 'y': 'Count'},
                    markers=True
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        # Price distribution
        if 'price' in df_clean.columns:
            st.markdown("###  Price Distribution")
            df_clean['price_numeric'] = df_clean['price'].str.replace(',', '').astype(float)
            fig3 = px.histogram(
                df_clean,
                x='price_numeric',
                nbins=30,
                title="Price Distribution",
                labels={'price_numeric': 'Price (FCFA)'},
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig3, use_container_width=True)
        
    else:
        st.warning(" No data available. Please scrape some data first!")

# VIEW DATA PAGE
elif menu == " View Data":
    st.markdown("##  View Scraped Data")
    
    data_type = st.selectbox(
        "Select data to view:",
        ["Voitures", "Motos", "Location"]
    )
    
    table_map = {"Voitures": "voitures", "Motos": "motos", "Location": "location"}
    df = load_from_db(table_map[data_type])
    
    if len(df) > 0:
        st.success(f" Found {len(df)} records in {data_type} table")
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input(" Search in data:", "")
        with col2:
            if st.button(" Clear Table"):
                if st.checkbox("Confirm deletion"):
                    conn = sqlite3.connect('daka_auto.db')
                    conn.execute(f"DELETE FROM {table_map[data_type]}")
                    conn.commit()
                    conn.close()
                    st.success(" Table cleared!")
                    st.rerun()
        
        # Filter dataframe
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            df = df[mask]
        
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=" Download CSV",
            data=csv,
            file_name=f"{data_type}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.warning(" No data available in this table. Please scrape some data first!")

# WEB EVALUATION APP PAGE
elif menu == " Web Evaluation App":
    st.markdown("##  Web Application Evaluation Forms")
    
    st.markdown("### Please fill out one of the evaluation forms below:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Google Form</h3>
            <p>Evaluate the web application using Google Forms</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(" Open Google Form", key="google", use_container_width=True):
            st.markdown("""
                <iframe src="https://docs.google.com/forms/d/e/1FAIpQLSeL5dzKVxgxD-rOZqLLiDWmIE1dPhBjeeYcrEl3_EcTGeH2zw/viewform?embedded=true" 
                width="100%" height="800" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> KoboToolbox Form</h3>
            <p>Evaluate the web application using KoboToolbox</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(" Open KoboToolbox Form", key="kobo", use_container_width=True):
            st.markdown("""
                <iframe src="https://ee.kobotoolbox.org/x/afz6PkAH2MUXehMZW8w42D" 
                width="100%" height="800" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info(" Tip: You can open the forms in a new tab by right-clicking the buttons and selecting 'Open in new tab'")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white;'>
    <p>Made with MARIE | © 2024 DAKA_AUTO_SCRAPER</p>
</div>
""", unsafe_allow_html=True) 
import streamlit as st
import pandas as pd
import sqlite3
from requests import get
from bs4 import BeautifulSoup as bs
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="DAKA_AUTO_SCRAPER",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful design
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    h1 {
        color: #ffffff;
        text-align: center;
        font-size: 3.5em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        padding: 20px;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        to { text-shadow: 0 0 20px rgba(255,255,255,0.8); }
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF6B6B 0%, #FFE66D 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 15px 30px;
        border: none;
        font-size: 1.2em;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #4facfe 0%, #00f2fe 100%);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2em;
        color: #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# Database functions
def init_db():
    conn = sqlite3.connect('daka_auto.db')
    c = conn.cursor()
    
    # Table for cars
    c.execute('''CREATE TABLE IF NOT EXISTS voitures
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand TEXT, model TEXT, year TEXT, kilometer TEXT,
                  fuel_type TEXT, gearbox TEXT, adress TEXT,
                  owner TEXT, price TEXT, scraped_date TEXT)''')
    
    # Table for motos
    c.execute('''CREATE TABLE IF NOT EXISTS motos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand TEXT, year TEXT, kilometer TEXT,
                  adress TEXT, owner TEXT, price TEXT, scraped_date TEXT)''')
    
    # Table for car rental
    c.execute('''CREATE TABLE IF NOT EXISTS location
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  brand TEXT, year TEXT, adress TEXT,
                  owner TEXT, price TEXT, scraped_date TEXT)''')
    
    conn.commit()
    conn.close()

def save_to_db(df, table_name):
    df['scraped_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('daka_auto.db')
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.close()

def load_from_db(table_name):
    conn = sqlite3.connect('daka_auto.db')
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# Scraping functions
def scrape_voitures(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f'Scraping page {index}/{num_pages}...')
        progress_bar.progress(index / num_pages)
        
        url = f'https://dakar-auto.com/senegal/voitures-4?&page={index}'
        res = get(url)
        soup = bs(res.content, 'html.parser')
        containers = soup.find_all('div', class_='listings-cards__list-item mb-md-3 mb-3')
        
        data = []
        for container in containers:
            try:
                gen_inf = container.find('h2', class_='listing-card__header__title mb-md-2 mb-0').a.text.strip().split()
                brand = gen_inf[0]
                model = " ".join(gen_inf[1:len(gen_inf)-1])
                year = gen_inf[-1]
                
                gen_inf1 = container.find('ul', 'listing-card__attribute-list list-inline mb-0')
                gen_inf2 = gen_inf1.find_all('li', 'listing-card__attribute list-inline-item')
                kms_driven = gen_inf2[1].text.replace('km','')
                gearbox = gen_inf2[2].text
                fuel_type = gen_inf2[3].text
                
                adress = container.find('div',class_='col-12 entry-zone-address').text
                owner = "".join(container.find('p', class_='time-author m-0').a.text).replace('Par','')
                price = "".join(container.find('h3','listing-card__header__price font-weight-bold text-uppercase mb-0').text.strip().split()).replace('FCFA','')
                
                dic = {
                    "brand": brand, "model": model, "year": year,
                    "kilometer": kms_driven, "fuel_type": fuel_type,
                    "gearbox": gearbox, "adress": adress,
                    "owner": owner, "price": price
                }
                data.append(dic)
            except:
                pass
        
        DF = pd.DataFrame(data)
        df = pd.concat([df, DF], axis=0).reset_index(drop=True)
    
    df = df.drop_duplicates()
    progress_bar.empty()
    status_text.empty()
    return df

def scrape_motos(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f'Scraping page {index}/{num_pages}...')
        progress_bar.progress(index / num_pages)
        
        url = f'https://dakar-auto.com/senegal/motos-and-scooters-3?&page={index}'
        res = get(url)
        soup = bs(res.content, 'html.parser')
        containers = soup.find_all('div', class_='listings-cards__list-item mb-md-3 mb-3')
        
        data = []
        for container in containers:
            try:
                gen_inf = container.find('h2', class_='listing-card__header__title mb-md-2 mb-0').a.text.strip().split()
                brand = gen_inf[0]
                year = gen_inf[-1]
                
                kms_driven = None
                gen_inf1 = container.find('ul', class_='listing-card__attribute-list list-inline mb-0')
                if gen_inf1:
                    gen_inf2 = gen_inf1.find_all('li', class_='listing-card__attribute list-inline-item')
                    if len(gen_inf2) > 1:
                        kms_driven = gen_inf2[1].text.replace('km', '')
                if not kms_driven:
                    kms_driven = "0"
                
                adress = container.find('div', class_='col-12 entry-zone-address').text
                owner = "".join(container.find('p', class_='time-author m-0').a.text).replace('Par','')
                price = "".join(container.find('h3', 'listing-card__header__price font-weight-bold text-uppercase mb-0').text.strip().split()).replace('FCFA','')
                
                dic = {
                    "brand": brand, "year": year, "kilometer": kms_driven,
                    "adress": adress, "owner": owner, "price": price
                }
                data.append(dic)
            except:
                pass
        
        DF = pd.DataFrame(data)
        df = pd.concat([df, DF], axis=0).reset_index(drop=True)
    
    df = df.drop_duplicates()
    progress_bar.empty()
    status_text.empty()
    return df

def scrape_location(num_pages):
    df = pd.DataFrame()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index in range(1, num_pages + 1):
        status_text.text(f'Scraping page {index}/{num_pages}...')
        progress_bar.progress(index / num_pages)
        
        url = f'https://dakar-auto.com/senegal/location-de-voitures-19?&page={index}'
        res = get(url)
        soup = bs(res.content, 'html.parser')
        containers = soup.find_all('div', class_='listings-cards__list-item mb-md-3 mb-3')
        
        data = []
        for container in containers:
            try:
                gen_inf = container.find('h2',class_='listing-card__header__title mb-md-2 mb-0').a.text.strip().split()
                brand = gen_inf[0]
                year = gen_inf[-1]
                
                owner = "".join(container.find('p',class_='time-author m-0').a.text).replace('Par','')
                adress = container.find('div', class_='col-12 entry-zone-address').text
                price = "".join(container.find('h3','listing-card__header__price font-weight-bold text-uppercase mb-0').text.strip().split()).replace('FCFA','')
                
                dic = {
                    "brand": brand, "year": year, "adress": adress,
                    "owner": owner, "price": price
                }
                data.append(dic)
            except:
                pass
        
        DF = pd.DataFrame(data)
        df = pd.concat([df, DF], axis=0).reset_index(drop=True)
    
    df = df.drop_duplicates()
    progress_bar.empty()
    status_text.empty()
    return df

# Initialize database
init_db()

# Main title
st.markdown("<h1> DAKA_AUTO_SCRAPER </h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/000000/car.png")
    st.markdown("###  Navigation")
    menu = st.radio(
        "",
        [" Home", " Scraper", " Dashboard", " View Data", " Web Evaluation App"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.info("DAKA_AUTO_SCRAPER is a powerful tool to scrape and analyze car data from Dakar-Auto.com")

# HOME PAGE
if menu == " Home":
    st.markdown("##  Welcome to DAKA_AUTO_SCRAPER!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Cars</h3>
            <p>Scrape detailed car listings including brand, model, year, and more!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Motos</h3>
            <p>Get information about motorcycles and scooters available in Senegal!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Rental</h3>
            <p>Explore car rental options with pricing and availability!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("###  Quick Start Guide")
    st.markdown("""
    1. **Go to Scraper** - Choose your data source and number of pages
    2. **Run the scraper** - Get fresh data from Dakar-Auto.com
    3. **View Dashboard** - Analyze the scraped data with beautiful charts
    4. **View Data** - Browse and download your scraped data
    5. **Web Evaluation** - Fill out evaluation forms
    """)

# SCRAPER PAGE
elif menu == " Scraper":
    st.markdown("##  Start Scraping")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url_choice = st.selectbox(
            " Select data source:",
            [" Voitures (Cars)", " Motos & Scooters", " Location de Voitures (Car Rental)"]
        )
    
    with col2:
        num_pages = st.number_input(" Number of pages:", min_value=1, max_value=50, value=1)
    
    st.markdown("---")
    
    if st.button(" Start Scraping", use_container_width=True):
        with st.spinner(' Scraping in progress...'):
            try:
                if "Voitures" in url_choice and "Location" not in url_choice:
                    df = scrape_voitures(num_pages)
                    save_to_db(df, 'voitures')
                    st.success(f' Successfully scraped {len(df)} cars!')
                    
                elif "Motos" in url_choice:
                    df = scrape_motos(num_pages)
                    save_to_db(df, 'motos')
                    st.success(f' Successfully scraped {len(df)} motos!')
                    
                elif "Location" in url_choice:
                    df = scrape_location(num_pages)
                    save_to_db(df, 'location')
                    st.success(f' Successfully scraped {len(df)} rental cars!')
                
                st.balloons()
                st.dataframe(df, use_container_width=True)
                
            except Exception as e:
                st.error(f' Error during scraping: {str(e)}')

# DASHBOARD PAGE
elif menu == " Dashboard":
    st.markdown("##  Data Analytics Dashboard")
    
    data_type = st.selectbox(
        "Select data to visualize:",
        ["Voitures", "Motos", "Location"]
    )
    
    table_map = {"Voitures": "voitures", "Motos": "motos", "Location": "location"}
    df = load_from_db(table_map[data_type])
    
    if len(df) > 0:
        # Remove scraped_date and id for analysis
        df_clean = df.drop(['scraped_date', 'id'], axis=1, errors='ignore')
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(" Total Records", len(df_clean))
        with col2:
            st.metric(" Unique Brands", df_clean['brand'].nunique())
        with col3:
            if 'price' in df_clean.columns:
                avg_price = df_clean['price'].str.replace(',', '').astype(float).mean()
                st.metric(" Avg Price (FCFA)", f"{avg_price:,.0f}")
        with col4:
            st.metric(" Latest Year", df_clean['year'].max() if 'year' in df_clean.columns else "N/A")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Brand distribution
            brand_counts = df_clean['brand'].value_counts().head(10)
            fig1 = px.bar(
                x=brand_counts.values,
                y=brand_counts.index,
                orientation='h',
                title="Top 10 Brands",
                labels={'x': 'Count', 'y': 'Brand'},
                color=brand_counts.values,
                color_continuous_scale='Viridis'
            )
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Year distribution
            if 'year' in df_clean.columns:
                year_counts = df_clean['year'].value_counts().sort_index()
                fig2 = px.line(
                    x=year_counts.index,
                    y=year_counts.values,
                    title="Vehicles by Year",
                    labels={'x': 'Year', 'y': 'Count'},
                    markers=True
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        # Price distribution
        if 'price' in df_clean.columns:
            st.markdown("###  Price Distribution")
            df_clean['price_numeric'] = df_clean['price'].str.replace(',', '').astype(float)
            fig3 = px.histogram(
                df_clean,
                x='price_numeric',
                nbins=30,
                title="Price Distribution",
                labels={'price_numeric': 'Price (FCFA)'},
                color_discrete_sequence=['#667eea']
            )
            st.plotly_chart(fig3, use_container_width=True)
        
    else:
        st.warning(" No data available. Please scrape some data first!")

# VIEW DATA PAGE
elif menu == " View Data":
    st.markdown("##  View Scraped Data")
    
    data_type = st.selectbox(
        "Select data to view:",
        ["Voitures", "Motos", "Location"]
    )
    
    table_map = {"Voitures": "voitures", "Motos": "motos", "Location": "location"}
    df = load_from_db(table_map[data_type])
    
    if len(df) > 0:
        st.success(f" Found {len(df)} records in {data_type} table")
        
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Search in data:", "")
        with col2:
            if st.button(" Clear Table"):
                if st.checkbox("Confirm deletion"):
                    conn = sqlite3.connect('daka_auto.db')
                    conn.execute(f"DELETE FROM {table_map[data_type]}")
                    conn.commit()
                    conn.close()
                    st.success(" Table cleared!")
                    st.rerun()
        
        # Filter dataframe
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            df = df[mask]
        
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=" Download CSV",
            data=csv,
            file_name=f"{data_type}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.warning(" No data available in this table. Please scrape some data first!")

# WEB EVALUATION APP PAGE
elif menu == " Web Evaluation App":
    st.markdown("##  Web Application Evaluation Forms")
    
    st.markdown("### Please fill out one of the evaluation forms below:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> Google Form</h3>
            <p>Evaluate the web application using Google Forms</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(" Open Google Form", key="google", use_container_width=True):
            st.markdown("""
                <iframe src="https://docs.google.com/forms/d/e/1FAIpQLSeL5dzKVxgxD-rOZqLLiDWmIE1dPhBjeeYcrEl3_EcTGeH2zw/viewform?embedded=true" 
                width="100%" height="800" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h3 style='color: #667eea;'> KoboToolbox Form</h3>
            <p>Evaluate the web application using KoboToolbox</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button(" Open KoboToolbox Form", key="kobo", use_container_width=True):
            st.markdown("""
                <iframe src="https://ee.kobotoolbox.org/x/afz6PkAH2MUXehMZW8w42D" 
                width="100%" height="800" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info(" Tip: You can open the forms in a new tab by right-clicking the buttons and selecting 'Open in new tab'")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white;'>
    <p>Made with  by MARIE | © 2024 DAKA_AUTO_SCRAPER</p>
</div>
""", unsafe_allow_html=True)