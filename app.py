import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp Performans Karşılaştırma Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23 & V5.2.6) vs WhatsApp İndirme Performansı Karşılaştırması")
st.markdown("""
    Bu panelde BiP ve WhatsApp uygulamalarının **Download_Duration (İndirme Süresi)** performansları analiz edilir.
    
    ⚠️ **Önemli Not:** Ölçülen değerler milisaniye (ms) cinsinden **süre** belirttiği için, **küçük olan değer daha hızlı** anlamına gelmektedir.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except:
            df = pd.read_excel(file_path)

        if df.empty:
            return None

        df.columns = [str(c).strip() for c in df.columns]
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)

        # --- DOWNLOAD_DURATION ODAKLI KONTROL ---
        duration_col = None
        for col in df.columns:
            if col.lower() == 'download_
