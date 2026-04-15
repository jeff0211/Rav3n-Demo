import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- PAGE SETUP ---
st.set_page_config(page_title="Asset Register", layout="wide")
st.title("🏢 Fixed Asset Management")

# --- DATABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- FETCH LOOKUP DATA ---
# This grabs the default categories and locations we just injected
@st.cache_data(ttl=600)
def get_categories():
    return supabase.table("categories").select("*").execute().data

@st.cache_data(ttl=600)
def get_locations():
    return supabase.table("locations").select("*").execute().data

categories = get_categories()
locations = get_locations()

# Create dictionaries to easily map the names to their database IDs
category_options = {cat['name']: cat['id'] for cat in categories}
location_options = {loc['name']: loc['id'] for loc in locations}

# --- UI TABS ---
tab1, tab2 = st.tabs(["➕ Add New Asset", "📋 Asset Register"])

# --- TAB 1: ADD ASSET FORM ---
with tab1:
    st.header("Register a New Asset")
    with st.form("add_asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            asset_tag = st.text_input("Asset Tag (e.g., COMP-2026-001)")
            name = st.text_input("Asset Name / Description")
            category_name = st.selectbox("Category", options=list(category_options.keys()))
            location_name = st.selectbox("Location", options=list(location_options.keys()))
            
        with col2:
            purchase_date = st.date_input("Purchase Date")
            purchase_price = st.number_input("Purchase Price (RM)", min_value=0.0, format="%.2f")
            status = st.selectbox("Status", ["Active", "In Maintenance", "Disposed"])
            
        submitted = st.form_submit_button("Save Asset")
        
        if submitted:
            new_asset = {
                "asset_tag": asset_tag,
                "name": name,
                "category_id": category_options[category_name],
                "location_id": location_options[location_name],
                "purchase_date": str(purchase_date),
                "purchase_price": purchase_price,
                "status": status
            }
            
            try:
                supabase.table("assets").insert(new_asset).execute()
                st.success(f"Successfully added {asset_tag} to the database!")
            except Exception as e:
                st.error(f"Database Error: {e}")

# --- TAB 2: VIEW REGISTER ---
with tab2:
    st.header("Current Asset Register")
    
    # We use Supabase's foreign key syntax to pull the actual names of the categories/locations, not just the ID numbers
    response = supabase.table("assets").select("asset_tag, name, purchase_date, purchase_price, status, categories(name), locations(name)").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Flatten the nested category and location names
        df['Category'] = df['categories'].apply(lambda x: x['name'] if x else 'N/A')
        df['Location'] = df['locations'].apply(lambda x: x['name'] if x else 'N/A')
        
        # Reorder and rename columns for a clean display
        display_df = df[['asset_tag', 'name', 'Category', 'Location', 'purchase_date', 'purchase_price', 'status']]
        display_df.columns = ['Tag', 'Name', 'Category', 'Location', 'Purchase Date', 'Price (RM)', 'Status']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No assets found. Add your first piece of equipment in the other tab!")
        