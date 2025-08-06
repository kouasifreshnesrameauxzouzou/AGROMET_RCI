import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium import plugins
import json

# Configuration de la page
st.set_page_config(
    page_title="AGROMET_RCI",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le style
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E8B57, #228B22);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .stSelectbox > div > div {
        background-color: #f0f8f0;
    }
    .weather-card {
        background: linear-gradient(135deg, #87CEEB, #4682B4);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 5px;
    }
    .folium-map {
        border: 2px solid #2E8B57;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Données étendues de stations par région avec coordonnées géographiques
STATIONS_DATA = {
    "N'ZI": {
        "Dimbokro": {"lat": 6.65, "lon": -4.7},
        "Bocanda": {"lat": 7.066667, "lon": -4.516667},
        "Bongouanou": {"lat": 6.65, "lon": -4.2}
    },
    "GOH": {
        "Gagnoa": {"lat": 6.133333, "lon": -5.95},
        "Ouragahio": {"lat": 6.316667, "lon": -5.933333},
        "Oumé": {"lat": 6.366667, "lon": -5.416667}
    },
    "LAGUNES": {
        "Abidjan": {"lat": 5.359952, "lon": -4.008256},
        "Grand-Bassam": {"lat": 5.200833, "lon": -3.738889},
        "Dabou": {"lat": 5.325, "lon": -4.376667}
    },
    "SASSANDRA-MARAHOUÉ": {
        "Daloa": {"lat": 6.877222, "lon": -6.450833},
        "Bouaflé": {"lat": 6.988889, "lon": -5.745556},
        "Zuénoula": {"lat": 7.426667, "lon": -6.053333}
    },
    "VALLÉE DU BANDAMA": {
        "Bouaké": {"lat": 7.690556, "lon": -5.030556},
        "Katiola": {"lat": 8.135833, "lon": -5.106944},
        "Béoumi": {"lat": 7.673889, "lon": -5.580556}
    },
    "MONTAGNES": {
        "Man": {"lat": 7.412222, "lon": -7.553056},
        "Danané": {"lat": 7.264167, "lon": -8.151944},
        "Biankouma": {"lat": 7.744722, "lon": -7.620833}
    },
    "SAVANES": {
        "Korhogo": {"lat": 9.458056, "lon": -5.629167},
        "Boundiali": {"lat": 9.520833, "lon": -6.489722},
        "Ferkessédougou": {"lat": 9.590833, "lon": -5.195833}
    },
    "ZANZAN": {
        "Bondoukou": {"lat": 8.040278, "lon": -2.798611},
        "Tanda": {"lat": 7.803056, "lon": -3.168611},
        "Bouna": {"lat": 9.273611, "lon": -2.996667}
    },
    "COMOÉ": {
        "Abengourou": {"lat": 6.729167, "lon": -3.496944},
        "Agnibilékrou": {"lat": 7.123611, "lon": -3.200833},
        "Bettié": {"lat": 6.235, "lon": -3.173333}
    },
    "LACS": {
        "Yamoussoukro": {"lat": 6.820556, "lon": -5.276667},
        "Tiébissou": {"lat": 7.158333, "lon": -5.223056},
        "Toumodi": {"lat": 6.557222, "lon": -5.018333}
    }
}

# Coordonnées des frontières de la Côte d'Ivoire pour créer un polygone
COTE_DIVOIRE_BOUNDS = [
    [10.740197, -2.494897],  # Nord-Est
    [10.740197, -8.599302],  # Nord-Ouest  
    [4.357067, -8.599302],   # Sud-Ouest
    [4.357067, -2.494897],   # Sud-Est
    [10.740197, -2.494897]   # Retour au point de départ
]

# Fonction pour créer une belle carte thermique avec Folium
def create_folium_heatmap(data_dict, title, colormap='RdYlBu_r', unit="", map_type="temperature"):
    # Centre de la Côte d'Ivoire
    center_lat, center_lon = 7.5, -5.5
    
    # Créer la carte de base avec un style moderne
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles=None,
        prefer_canvas=True
    )
    
    # Ajouter différentes couches de fond
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB Positron', name='CartoDB Positron').add_to(m)
    folium.TileLayer('CartoDB Dark_Matter', name='CartoDB Dark').add_to(m)
    
    # Utiliser CartoDB Positron par défaut pour un look propre
    folium.TileLayer('CartoDB Positron').add_to(m)
    
    # Préparer les données pour la carte
    heat_data = []
    markers_data = []
    
    # Déterminer les valeurs min et max pour la normalisation des couleurs
    values = list(data_dict.values())
    min_val = min(values)
    max_val = max(values)
    
    # Choisir la palette de couleurs selon le type de données
    color_palettes = {
        'temperature': ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', 
                       '#ffffcc', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'],
        'precipitation': ['#ffffff', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', 
                         '#2171b5', '#08519c', '#08306b', '#041f47', '#021238'],
        'humidity': ['#f7fcf0', '#e0f3db', '#ccebc5', '#a8ddb5', '#7bccc4', 
                    '#4eb3d3', '#2b8cbe', '#0868ac', '#084081', '#042753'],
        'water_satisfaction': ['#8c2d04', '#cc4c02', '#ec7014', '#fe9929', '#fec44f', 
                              '#fee391', '#fff7bc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#2c7fb8']
    }
    
    palette = color_palettes.get(map_type, color_palettes['temperature'])
    
    for region, value in data_dict.items():
        if region in STATIONS_DATA:
            # Utiliser la première station comme point représentatif de la région
            station_name = list(STATIONS_DATA[region].keys())[0]
            station_data = STATIONS_DATA[region][station_name]
            
            lat, lon = station_data['lat'], station_data['lon']
            
            # Normaliser la valeur pour la carte de chaleur
            normalized_value = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            heat_data.append([lat, lon, normalized_value])
            
            # Déterminer la couleur du marqueur basée sur la valeur
            color_index = int(normalized_value * (len(palette) - 1))
            marker_color = palette[color_index]
            
            # Créer un marqueur avec style personnalisé
            icon_color = 'white' if normalized_value > 0.5 else 'black'
            
            # Choisir l'icône selon le type de données
            icons = {
                'temperature': 'thermometer-half',
                'precipitation': 'tint',
                'humidity': 'eye-dropper',
                'water_satisfaction': 'leaf'
            }
            icon_name = icons.get(map_type, 'info-sign')
            
            # Popup avec informations détaillées
            popup_html = f"""
            <div style='font-family: Arial, sans-serif; width: 200px;'>
                <h4 style='color: #2E8B57; margin-bottom: 10px;'>{region}</h4>
                <p><strong>Station:</strong> {station_name}</p>
                <p><strong>{title.split('-')[-1].strip()}:</strong> 
                   <span style='font-size: 18px; font-weight: bold; color: #d73027;'>
                   {value}{unit}
                   </span>
                </p>
                <p><strong>Coordonnées:</strong> {lat:.3f}°N, {abs(lon):.3f}°W</p>
            </div>
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{region}: {value}{unit}",
                icon=folium.Icon(
                    color='red' if normalized_value > 0.7 else 'orange' if normalized_value > 0.4 else 'green',
                    icon=icon_name,
                    prefix='fa'
                )
            ).add_to(m)
            
            # Ajouter un cercle coloré pour l'effet thermique
            circle_color = marker_color
            folium.CircleMarker(
                location=[lat, lon],
                radius=20 + (normalized_value * 30),  # Taille variable selon la valeur
                popup=f"{region}: {value}{unit}",
                color='white',
                weight=2,
                fillColor=circle_color,
                fillOpacity=0.7
            ).add_to(m)
    
    # Ajouter une carte de chaleur en arrière-plan
    if heat_data:
        plugins.HeatMap(
            heat_data,
            min_opacity=0.2,
            max_zoom=10,
            radius=50,
            blur=40,
            gradient={
                0.0: '#313695',
                0.2: '#4575b4', 
                0.4: '#abd9e9',
                0.6: '#fee090',
                0.8: '#f46d43',
                1.0: '#a50026'
            }
        ).add_to(m)
    
    # Ajouter une légende personnalisée
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: auto;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px; border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
    <p style="margin: 0 0 10px 0;"><strong>{title}</strong></p>
    <p style="margin: 0;"><i class="fa fa-circle" style="color:#a50026"></i> Élevé ({max_val:.1f}{unit})</p>
    <p style="margin: 0;"><i class="fa fa-circle" style="color:#f46d43"></i> Moyen-Élevé</p>
    <p style="margin: 0;"><i class="fa fa-circle" style="color:#fee090"></i> Moyen</p>
    <p style="margin: 0;"><i class="fa fa-circle" style="color:#abd9e9"></i> Moyen-Faible</p>
    <p style="margin: 0;"><i class="fa fa-circle" style="color:#313695"></i> Faible ({min_val:.1f}{unit})</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Ajouter un contrôle des couches
    folium.LayerControl().add_to(m)
    
    # Ajouter un plugin de mesure
    plugins.MeasureControl().add_to(m)
    
    # Ajouter la position de la souris
    plugins.MousePosition().add_to(m)
    
    # Limiter la vue à la Côte d'Ivoire
    m.fit_bounds([[4.0, -8.6], [10.8, -2.4]])
    
    return m

# Fonction pour afficher une carte Folium dans Streamlit
def display_folium_map(folium_map, height=500):
    """Fonction pour afficher une carte Folium dans Streamlit avec un style personnalisé"""
    map_html = folium_map._repr_html_()
    
    # Ajouter du CSS personnalisé pour la carte
    styled_html = f"""
    <div class="folium-map" style="border: 3px solid #2E8B57; border-radius: 15px; overflow: hidden; box-shadow: 0 6px 12px rgba(0,0,0,0.3);">
        <div style="height: {height}px;">
            {map_html}
        </div>
    </div>
    """
    
    st.components.v1.html(styled_html, height=height + 20)

# Fonction d'authentification
def authenticate_user():
    # Initialisation des variables de session
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'login_attempted' not in st.session_state:
        st.session_state.login_attempted = False
    
    if not st.session_state.authenticated:
        st.markdown('<div class="main-header"><h1>🌾 AGROMET_RCI</h1><p>Application de diffusion d\'informations agrométéorologiques</p></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Authentification")
            
            # Utilisation de form pour éviter les rerun multiples
            with st.form("login_form"):
                username = st.text_input("Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
                password = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
                submit_button = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
                
                if submit_button:
                    if username and password:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.login_attempted = True
                        st.success("✅ Connexion réussie! Redirection en cours...")
                        st.rerun()
                    else:
                        st.error("❌ Veuillez saisir vos identifiants")
        
        # Logo SODEXAM (simulation)
        st.markdown("---")
        st.markdown("<center><strong>SODEXAM - Direction de la Météorologie Nationale</strong></center>", unsafe_allow_html=True)
        return False
    
    return True

# Génération de données météo simulées
def generate_weather_data(station, days=7):
    np.random.seed(42)
    dates = [datetime.now() - timedelta(days=i) for i in range(days)]
    dates.reverse()
    
    data = []
    for date in dates:
        data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Station': station,
            'Température Min (°C)': round(np.random.uniform(20, 25), 1),
            'Température Max (°C)': round(np.random.uniform(28, 35), 1),
            'Humidité Min (%)': round(np.random.uniform(45, 60), 1),
            'Humidité Max (%)': round(np.random.uniform(75, 95), 1),
            'Précipitations (mm)': round(np.random.uniform(0, 25), 1),
            'Vitesse Vent (m/s)': round(np.random.uniform(1, 8), 1),
            'Direction Vent': np.random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
            'Insolation (h)': round(np.random.uniform(4, 12), 1)
        })
    
    return pd.DataFrame(data)

# Génération de données pluviométriques décadaires
def generate_decade_rainfall_data(region):
    decades = ['Décade 1', 'Décade 2', 'Décade 3']
    months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    
    data = []
    for month in months:
        for decade in decades:
            data.append({
                'Période': f"{month} - {decade}",
                'Pluie observée (mm)': round(np.random.uniform(10, 150), 1),
                'Moyenne 30 ans (mm)': round(np.random.uniform(50, 120), 1),
                'Écart (mm)': round(np.random.uniform(-50, 50), 1),
                'Année précédente (mm)': round(np.random.uniform(20, 140), 1)
            })
    
    return pd.DataFrame(data)

# Interface principale
def main_interface():
    # En-tête de l'application
    username = st.session_state.get('username', 'Utilisateur')
    st.markdown(f'<div class="main-header"><h1>🌾 AGROMET_RCI</h1><p>Bienvenue {username} | Informations Agrométéorologiques en Temps Réel</p></div>', unsafe_allow_html=True)
    
    # Bouton de déconnexion avec confirmation
    if st.sidebar.button("🚪 Se déconnecter", key="logout_btn"):
        # Reset des variables de session
        for key in ['authenticated', 'username', 'login_attempted']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Sélection de la région
    st.sidebar.markdown("### 📍 Sélection de la région")
    
    # Utilisation de session state pour maintenir les sélections
    if 'selected_region' not in st.session_state:
        st.session_state.selected_region = "N'ZI"
    if 'selected_station' not in st.session_state:
        st.session_state.selected_station = "Dimbokro"
    
    selected_region = st.sidebar.selectbox(
        "Choisissez une région:",
        options=list(STATIONS_DATA.keys()),
        index=list(STATIONS_DATA.keys()).index(st.session_state.selected_region),
        key="region_select"
    )
    
    # Mise à jour de la station si la région change
    if selected_region != st.session_state.selected_region:
        st.session_state.selected_region = selected_region
        st.session_state.selected_station = list(STATIONS_DATA[selected_region].keys())[0]
    
    # Sélection de la station
    stations = list(STATIONS_DATA[selected_region].keys())
    try:
        station_index = stations.index(st.session_state.selected_station)
    except ValueError:
        station_index = 0
        st.session_state.selected_station = stations[0]
    
    selected_station = st.sidebar.selectbox(
        "Choisissez une station:",
        options=stations,
        index=station_index,
        key="station_select"
    )
    
    st.session_state.selected_station = selected_station
    
    # Menu de navigation
    st.sidebar.markdown("### 📊 Navigation")
    menu_options = [
        "📊 Paramètres Météo Journaliers",
        "🌧️ Situation Pluviométrique", 
        "📅 Prévision Saisonnière",
        "💧 Satisfaction en Eau des Cultures",
        "🌍 Réserve en Eau du Sol",
        "💡 Avis et Conseils"
    ]
    
    # Maintenir la sélection du menu
    if 'selected_menu_index' not in st.session_state:
        st.session_state.selected_menu_index = 0
    
    selected_menu = st.sidebar.radio(
        "", 
        menu_options, 
        index=st.session_state.selected_menu_index,
        key="menu_radio"
    )
    
    # Mettre à jour l'index du menu sélectionné
    st.session_state.selected_menu_index = menu_options.index(selected_menu)
    
    # Affichage du contenu selon le menu sélectionné
    try:
        if selected_menu == "📊 Paramètres Météo Journaliers":
            show_daily_weather(selected_region, selected_station)
        elif selected_menu == "🌧️ Situation Pluviométrique":
            show_rainfall_situation(selected_region)
        elif selected_menu == "📅 Prévision Saisonnière":
            show_seasonal_forecast(selected_region)
        elif selected_menu == "💧 Satisfaction en Eau des Cultures":
            show_crop_water_satisfaction(selected_region)
        elif selected_menu == "🌍 Réserve en Eau du Sol":
            show_soil_water_reserve(selected_region)
        elif selected_menu == "💡 Avis et Conseils":
            show_advice_and_recommendations(selected_region)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du contenu: {str(e)}")
        st.info("🔄 Veuillez rafraîchir la page ou sélectionner un autre menu.")

def show_daily_weather(region, station):
    st.header(f"📊 Paramètres Météorologiques Journaliers - {station}")
    
    # Génération des données météo
    weather_data = generate_weather_data(station)
    
    # Métriques principales
    latest_data = weather_data.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🌡️ Température Max",
            value=f"{latest_data['Température Max (°C)']}°C",
            delta=f"{round(np.random.uniform(-2, 2), 1)}°C"
        )
    
    with col2:
        st.metric(
            label="💧 Humidité Max",
            value=f"{latest_data['Humidité Max (%)']}%",
            delta=f"{round(np.random.uniform(-5, 5), 1)}%"
        )
    
    with col3:
        st.metric(
            label="🌧️ Précipitations",
            value=f"{latest_data['Précipitations (mm)']} mm",
            delta=f"{round(np.random.uniform(-10, 10), 1)} mm"
        )
    
    with col4:
        st.metric(
            label="💨 Vitesse Vent",
            value=f"{latest_data['Vitesse Vent (m/s)']} m/s",
            delta=f"{round(np.random.uniform(-1, 1), 1)} m/s"
        )
    
    # Tableau des données
    st.subheader("📋 Données des 7 derniers jours")
    st.dataframe(weather_data, use_container_width=True)
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique des températures
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=weather_data['Date'],
            y=weather_data['Température Max (°C)'],
            mode='lines+markers',
            name='Temp Max',
            line=dict(color='red')
        ))
        fig_temp.add_trace(go.Scatter(
            x=weather_data['Date'],
            y=weather_data['Température Min (°C)'],
            mode='lines+markers',
            name='Temp Min',
            line=dict(color='blue')
        ))
        fig_temp.update_layout(title="📈 Évolution des Températures", xaxis_title="Date", yaxis_title="Température (°C)")
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        # Carte Folium des précipitations journalières
        st.subheader("🌧️ Précipitations Journalières par Région")
        precipitation_data = {}
        np.random.seed(42)
        for reg in STATIONS_DATA.keys():
            precipitation_data[reg] = round(np.random.uniform(0, 50), 1)
        
        folium_map = create_folium_heatmap(
            precipitation_data, 
            "Précipitations Journalières", 
            colormap='Blues',
            unit=" mm",
            map_type="precipitation"
        )
        display_folium_map(folium_map, height=400)

def show_rainfall_situation(region):
    st.header(f"🌧️ Situation Pluviométrique - Région {region}")
    
    # Génération des données pluviométriques
    rainfall_data = generate_decade_rainfall_data(region)
    
    # Graphique de comparaison
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Pluie observée',
        x=rainfall_data['Période'],
        y=rainfall_data['Pluie observée (mm)'],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Moyenne 30 ans',
        x=rainfall_data['Période'],
        y=rainfall_data['Moyenne 30 ans (mm)'],
        marker_color='darkblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Année précédente',
        x=rainfall_data['Période'],
        y=rainfall_data['Année précédente (mm)'],
        marker_color='green'
    ))
    
    fig.update_layout(
        title="📊 Comparaison Pluviométrique par Décade",
        barmode='group',
        xaxis_title="Période",
        yaxis_title="Précipitations (mm)"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Carte Folium de la situation pluviométrique
    st.subheader("🗺️ Situation Pluviométrique Régionale")
    regional_rainfall = {}
    np.random.seed(123)
    for reg in STATIONS_DATA.keys():
        regional_rainfall[reg] = round(np.random.uniform(20, 200), 1)
    
    folium_map = create_folium_heatmap(
        regional_rainfall, 
        "Précipitations Cumulées Mensuelles", 
        colormap='Blues',
        unit=" mm",
        map_type="precipitation"
    )
    display_folium_map(folium_map, height=500)
    
    # Tableau des écarts
    st.subheader("📋 Écarts par rapport à la normale")
    rainfall_data['Écart (%)'] = round((rainfall_data['Pluie observée (mm)'] - rainfall_data['Moyenne 30 ans (mm)']) / rainfall_data['Moyenne 30 ans (mm)'] * 100, 1)
    st.dataframe(rainfall_data[['Période', 'Pluie observée (mm)', 'Moyenne 30 ans (mm)', 'Écart (mm)', 'Écart (%)']], use_container_width=True)

def show_seasonal_forecast(region):
    st.header(f"📅 Prévision Saisonnière - Région {region}")
    
    st.info("📋 Prévisions pour la saison agricole 2024-2025")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Carte Folium des prévisions saisonnières de précipitations
        st.subheader("🌧️ Prévisions Saisonnières - Précipitations Cumulées")
        seasonal_precipitation_data = {}
        np.random.seed(100)
        for reg in STATIONS_DATA.keys():
            seasonal_precipitation_data[reg] = round(np.random.uniform(800, 1800), 0)
        
        folium_map = create_folium_heatmap(
            seasonal_precipitation_data, 
            "Prévisions Précipitations Saisonnières", 
            colormap='RdYlBu_r',
            unit=" mm",
            map_type="precipitation"
        )
        display_folium_map(folium_map, height=450)
        
        # Graphique temporel des prévisions mensuelles
        months = ['Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre']
        precipitation_forecast = [120, 180, 200, 250, 180, 100]
        temperature_forecast = [28, 26, 25, 24, 26, 29]
        
        fig_timeline = go.Figure()
        
        fig_timeline.add_trace(go.Bar(
            name='Précipitations (mm)',
            x=months,
            y=precipitation_forecast,
            yaxis='y',
            marker_color='lightblue'
        ))
        
        fig_timeline.add_trace(go.Scatter(
            name='Température (°C)',
            x=months,
            y=temperature_forecast,
            yaxis='y2',
            mode='lines+markers',
            marker_color='red'
        ))
        
        fig_timeline.update_layout(
            title="📈 Évolution Mensuelle des Prévisions",
            xaxis_title="Mois",
            yaxis=dict(title="Précipitations (mm)", side="left"),
            yaxis2=dict(title="Température (°C)", side="right", overlaying="y")
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Tendances Attendues")
        st.success("✅ **Saison favorable** pour les cultures de riz")
        st.warning("⚠️ **Attention** aux variations pluviométriques en juillet")
        st.info("ℹ️ **Recommandation** : Planifier les semis pour mi-mai")
        
        st.markdown("### 📊 Probabilités")
        st.metric("Saison normale", "65%", "↑ 5%")
        st.metric("Saison sèche", "20%", "↓ 3%")
        st.metric("Saison humide", "15%", "↓ 2%")

def show_crop_water_satisfaction(region):
    st.header(f"💧 Niveau de Satisfaction en Eau des Cultures - Région {region}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Carte Folium de satisfaction en eau des cultures par région
        st.subheader("💧 Satisfaction en Eau des Cultures par Région")
        water_satisfaction_data = {}
        np.random.seed(50)
        for reg in STATIONS_DATA.keys():
            water_satisfaction_data[reg] = round(np.random.uniform(45, 95), 0)
        
        folium_map = create_folium_heatmap(
            water_satisfaction_data, 
            "Satisfaction en Eau des Cultures", 
            colormap='RdYlGn',
            unit="%",
            map_type="water_satisfaction"
        )
        display_folium_map(folium_map, height=450)
        
        # Graphique par stade de développement pour la région sélectionnée
        stages = ['Début croissance', 'Croissance végétative', 'Phase reproductive']
        satisfaction_levels = [water_satisfaction_data.get(region, 75) + np.random.randint(-10, 10) for _ in range(3)]
        satisfaction_levels = [max(0, min(100, level)) for level in satisfaction_levels]  # Limiter entre 0 et 100
        
        fig_stages = go.Figure(data=[
            go.Bar(
                x=stages,
                y=satisfaction_levels,
                marker_color=['green' if x >= 80 else 'orange' if x >= 60 else 'red' for x in satisfaction_levels],
                text=[f"{x}%" for x in satisfaction_levels],
                textposition='auto'
            )
        ])
        
        fig_stages.update_layout(
            title=f"📊 Satisfaction en Eau par Stade - {region}",
            xaxis_title="Stades de Développement",
            yaxis_title="Niveau de Satisfaction (%)",
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig_stages, use_container_width=True)
    
    with col2:
        st.markdown("### 🌾 État des Cultures")
        
        kc_values = ['(Kc=0.3-0.5)', '(Kc=0.8)', '(Kc=1.2)']
        for i, (stage, level, kc) in enumerate(zip(stages, satisfaction_levels, kc_values)):
            if level >= 80:
                st.success(f"✅ **{stage} {kc}**: {level}% - Excellent")
            elif level >= 60:
                st.warning(f"⚠️ **{stage} {kc}**: {level}% - Correct")
            else:
                st.error(f"❌ **{stage} {kc}**: {level}% - Insuffisant")
        
        st.markdown("### 📅 Dates de Semis Recommandées")
        st.info("🌱 **Semis précoce**: 15-30 Mai 2024")
        st.info("🌱 **Semis normal**: 1-15 Juin 2024")
        st.info("🌱 **Semis tardif**: 16-30 Juin 2024")

def show_soil_water_reserve(region):
    st.header(f"🌍 Réserve en Eau du Sol et Prévisions - Région {region}")
    
    # Données simulées de réserve en eau
    dates = pd.date_range(start='2024-05-01', end='2024-05-31', freq='D')
    water_reserve = np.random.uniform(40, 100, len(dates))
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Carte Folium de la réserve en eau du sol
        st.subheader("🗺️ Réserve en Eau du Sol par Région")
        soil_water_data = {}
        np.random.seed(75)
        for reg in STATIONS_DATA.keys():
            soil_water_data[reg] = round(np.random.uniform(30, 95), 0)
        
        folium_map = create_folium_heatmap(
            soil_water_data, 
            "Réserve en Eau du Sol", 
            colormap='Blues',
            unit="%",
            map_type="humidity"
        )
        display_folium_map(folium_map, height=450)
        
        # Graphique de l'évolution de la réserve en eau
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=water_reserve,
            mode='lines+markers',
            name='Réserve en eau (%)',
            line=dict(color='blue', width=3),
            fill='tonexty'
        ))
        
        # Ligne de seuil critique
        fig.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Seuil critique")
        fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Seuil optimal")
        
        fig.update_layout(
            title="📈 Évolution de la Réserve en Eau du Sol",
            xaxis_title="Date",
            yaxis_title="Réserve en Eau (%)",
            yaxis=dict(range=[0, 100])
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🔮 Prévisions 7 Jours")
        
        forecast_days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        rain_forecast = [5, 12, 0, 8, 15, 3, 7]
        
        for day, rain in zip(forecast_days, rain_forecast):
            if rain > 10:
                st.success(f"🌧️ **{day}**: {rain}mm - Pluie significative")
            elif rain > 5:
                st.info(f"🌦️ **{day}**: {rain}mm - Pluie modérée")
            elif rain > 0:
                st.warning(f"🌤️ **{day}**: {rain}mm - Pluie faible")
            else:
                st.error(f"☀️ **{day}**: {rain}mm - Pas de pluie")
        
        # Métriques actuelles
        st.markdown("### 📊 État Actuel")
        st.metric("Réserve Utile", f"{water_reserve[-1]:.1f}%", f"{water_reserve[-1] - water_reserve[-2]:.1f}%")
        st.metric("Capacité au champ", "100 mm", "Stable")

def show_advice_and_recommendations(region):
    st.header(f"💡 Avis et Conseils Agrométéorologiques - Région {region}")
    
    # Conseils basés sur les conditions actuelles
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    st.markdown(f"### 📅 Bulletin du {current_date}")
    
    # Conseils par type de culture
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌾 **Riziculture**")
        
        advice_rice = [
            "✅ **Préparation des champs**: Conditions favorables pour le labour",
            "🌱 **Semis**: Période optimale pour les variétés précoces",
            "💧 **Irrigation**: Maintenir 5cm d'eau dans les rizières",
            "🚜 **Travaux**: Éviter les interventions mécaniques lourdes",
            "🌿 **Fertilisation**: Apporter l'engrais de fond avant repiquage"
        ]
        
        for advice in advice_rice:
            st.success(advice)
    
    with col2:
        st.markdown("#### 🌽 **Cultures Vivrières**")
        
        advice_crops = [
            "⚠️ **Maïs**: Reporter les semis de 7 jours",
            "✅ **Igname**: Conditions favorables pour la plantation",
            "🌿 **Légumineuses**: Période idéale pour le semis",
            "💨 **Protection**: Installer des brise-vents si nécessaire",
            "🐛 **Phytosanitaire**: Surveiller les attaques de chenilles"
        ]
        
        for advice in advice_crops:
            if "⚠️" in advice:
                st.warning(advice)
            else:
                st.success(advice)
    
    # Alertes météorologiques
    st.markdown("### 🚨 Alertes et Recommandations Urgentes")
    
    alerts = [
        ("🌧️", "Fort risque de pluies intenses", "Sécuriser les récoltes en cours de séchage", "warning"),
        ("💨", "Vents forts prévus", "Renforcer les tuteurages des jeunes plants", "error"),
        ("☀️", "Période sèche prolongée", "Planifier l'irrigation des cultures sensibles", "info")
    ]
    
    for icon, title, recommendation, alert_type in alerts:
        if alert_type == "warning":
            st.warning(f"{icon} **{title}**: {recommendation}")
        elif alert_type == "error":
            st.error(f"{icon} **{title}**: {recommendation}")
        else:
            st.info(f"{icon} **{title}**: {recommendation}")
    
    # Calendrier agricole
    st.markdown("### 📅 Calendrier Agricole - Prochaines Semaines")
    
    calendar_activities = pd.DataFrame({
        'Semaine': ['Semaine 1', 'Semaine 2', 'Semaine 3', 'Semaine 4'],
        'Activités Principales': [
            'Préparation des pépinières de riz',
            'Semis des légumineuses de saison',
            'Repiquage du riz (variétés précoces)',
            'Premier sarclage des cultures installées'
        ],
        'Conditions Météo': [
            'Pluviosité modérée attendue',
            'Conditions sèches favorables',
            'Retour des pluies régulières',
            'Alternance soleil-pluie'
        ],
        'Priorité': ['Haute', 'Moyenne', 'Haute', 'Moyenne']
    })
    
    st.dataframe(calendar_activities, use_container_width=True)
    
    # Téléchargement des recommandations
    st.markdown("### 📥 Télécharger les Recommandations")
    
    # Utilisation d'un container pour éviter les problèmes de rerun
    with st.container():
        if st.button("📄 Générer le bulletin PDF", type="primary", key="pdf_button"):
            with st.spinner("⏳ Génération du bulletin en cours..."):
                # Simulation du temps de génération
                import time
                time.sleep(1)
                st.success("✅ Bulletin PDF généré avec succès!")
                st.info("💾 Le fichier sera disponible dans votre espace de téléchargement.")

# Point d'entrée principal
def main():
    if authenticate_user():
        main_interface()

if __name__ == "__main__":
    main()
