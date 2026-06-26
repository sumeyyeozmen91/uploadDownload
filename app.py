def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        df = pd.read_excel(file_path)

        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]

        fname = os.path.basename(file_path).replace(".xlsx", "")

        # Örnek:
        # 5.1.23_Bip_4.5G_HDPhoto

        parts = fname.split("_")

        if len(parts) != 4:
            return None

        version = parts[0]          # 5.1.23
        app = parts[1]              # Bip
        network = parts[2]          # 4.5G / Wifi
        photo_type = parts[3]       # HDPhoto / SDPhoto

        if network.lower() == "wifi":
            network = "Wi-Fi"
        elif "4.5" in network:
            network = "4.5G"

        df["Uygulama"] = "BiP"
        df["Versiyon"] = version
        df["Şebeke"] = network
        df["Fotoğraf"] = photo_type

        if version.startswith("5.1"):
            grup = "BiP 5.1.23"
        elif version.startswith("5.2"):
            grup = "BiP 5.2.6"
        else:
            grup = version

        df["Grup"] = grup

        df["Uzantı"] = df["Test Adı"].apply(
            lambda x: str(x).split(".")[-1].upper()
        )

        df["Boyut"] = df["Test Adı"].apply(
            lambda x: str(x).split(".")[0]
        )

        return df[[
            "Test Adı",
            "Uzantı",
            "Boyut",
            "Yükleme Süresi",
            "İndirme Süresi",
            "Şebeke",
            "Fotoğraf",
            "Versiyon",
            "Grup"
        ]]

    except Exception as e:
        st.error(f"{file_path} okunamadı : {e}")
        return None
