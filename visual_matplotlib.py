import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import glob
import os
import sys
from datetime import datetime, timedelta

def load_air_quality_data(file_path=None):
    """
    CSV-Datei mit Luftqualitätsdaten laden
    
    Parameters:
        file_path (str): Pfad zur CSV-Datei oder None, um die neueste Datei zu laden
    
    Returns:
        DataFrame: Pandas DataFrame mit Luftqualitätsdaten
    """
    if file_path is None:
        # Suche nach allen CSV-Dateien, die mit 'aqicn_luftqualitaet_' beginnen
        csv_files = glob.glob("aqicn_luftqualitaet_*.csv")
        
        if not csv_files:
            print("Keine Luftqualitätsdaten gefunden. Bitte CSV-Datei angeben.")
            return None
        
        # Sortiere nach Änderungsdatum (neueste zuerst)
        csv_files.sort(key=os.path.getmtime, reverse=True)
        file_path = csv_files[0]
        print(f"Neueste Datei wird verwendet: {file_path}")
    
    try:
        # Daten laden
        df = pd.read_csv(file_path)
        
        # Datum in datetime umwandeln
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        
        return df
    
    except Exception as e:
        print(f"Fehler beim Laden der Daten: {e}")
        return None

def plot_air_quality_parameters(df, parameters=None, save_fig=False):
    """
    Luftqualitätsparameter über Zeit visualisieren
    
    Parameters:
        df (DataFrame): Luftqualitätsdaten
        parameters (list): Liste der zu visualisierenden Parameter oder None für alle
        save_fig (bool): Ob die Grafik gespeichert werden soll
    """
    if df is None or df.empty:
        print("Keine Daten zum Visualisieren vorhanden.")
        return
    
    # Prüfen, ob erforderliche Spalten vorhanden sind
    required_cols = ['parameter', 'value', 'datetime']
    if not all(col in df.columns for col in required_cols):
        print(f"Erforderliche Spalten fehlen. Benötigt: {required_cols}")
        print(f"Vorhandene Spalten: {df.columns.tolist()}")
        return
    
    # Falls keine Parameter angegeben wurden, alle verfügbaren verwenden
    if parameters is None:
        parameters = df['parameter'].unique().tolist()
    else:
        # Nur Parameter verwenden, die tatsächlich in den Daten vorhanden sind
        parameters = [p for p in parameters if p in df['parameter'].unique()]
    
    if not parameters:
        print("Keine gültigen Parameter zum Visualisieren gefunden.")
        return
    
    # Bestimme den Standort für den Titel
    location = "Unbekannt"
    if 'location' in df.columns and not df['location'].empty:
        location = df['location'].iloc[0]
        # Falls location ein komplexer String ist, nur den Hauptteil verwenden
        location = location.split(',')[0].split('(')[0].strip()
    
    # Größe der Abbildung einstellen
    plt.figure(figsize=(12, 8))
    
    # Farben für verschiedene Parameter
    colors = plt.cm.tab10(np.linspace(0, 1, len(parameters)))
    
    # Für jeden Parameter einen Linienplot erstellen
    for i, param in enumerate(parameters):
        param_data = df[df['parameter'] == param].sort_values('datetime')
        
        if param_data.empty:
            continue
        
        # Einheitenbezeichnung
        unit = "AQI"
        if 'unit' in param_data.columns and not param_data['unit'].empty:
            unit = param_data['unit'].iloc[0]
        
        # Plot erstellen
        plt.plot(param_data['datetime'], param_data['value'], 
                 marker='o', linestyle='-', linewidth=2, 
                 color=colors[i], label=f"{param.upper()} ({unit})")
    
    # Bestimme den Zeitraum für die x-Achse
    if 'datetime' in df.columns and not df['datetime'].empty:
        min_date = df['datetime'].min()
        max_date = df['datetime'].max()
        
        # Formatierung für die x-Achse je nach Zeitraum
        time_range = max_date - min_date
        
        if time_range <= timedelta(hours=24):
            # Stündliche Ansicht
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.xlabel('Uhrzeit')
        else:
            # Tägliche Ansicht
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.'))
            plt.xlabel('Datum')
    
    # Titel und Beschriftungen
    current_date = datetime.now().strftime('%d.%m.%Y')
    plt.title(f'Luftqualitätsindizes für {location} (Stand: {current_date})', fontsize=16)
    plt.ylabel('Wert', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Legende und Layout
    plt.legend(fontsize=12)
    plt.tight_layout()
    
    # AQI-Kategorien anzeigen (für die y-Achse)
    if "AQI" in ''.join(df['unit'].astype(str).tolist()):
        # Horizontale Linien für AQI-Kategorien
        aqi_levels = [
            (0, 50, 'Gut', 'green'),
            (51, 100, 'Moderat', 'yellow'),
            (101, 150, 'Ungesund für sensible Gruppen', 'orange'),
            (151, 200, 'Ungesund', 'red'),
            (201, 300, 'Sehr ungesund', 'purple'),
            (301, 500, 'Gefährlich', 'brown')
        ]
        
        # Bestimme den y-Achsenbereich
        y_min, y_max = plt.ylim()
        y_max = max(y_max, 300)  # Mindestens bis zum Bereich "Sehr ungesund" anzeigen
        
        # Zeichne horizontale Linien für AQI-Kategorien
        for low, high, label, color in aqi_levels:
            if low <= y_max:
                plt.axhspan(low, min(high, y_max), alpha=0.1, color=color)
                
                # Beschriftung nur für sichtbare Bereiche
                if high > y_min and low < y_max:
                    plt.text(min_date, (low + min(high, y_max))/2, 
                             f" {label}", verticalalignment='center',
                             fontsize=9, color=color)
    
    # Grafik speichern oder anzeigen
    if save_fig:
        # Dateiname aus Ort und Datum generieren
        safe_location = ''.join(c if c.isalnum() else '_' for c in location)
        fig_filename = f"luftqualitaet_{safe_location}_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(fig_filename, dpi=300, bbox_inches='tight')
        print(f"Grafik gespeichert als: {fig_filename}")
    
    # Grafik anzeigen
    plt.show()

def plot_parameter_comparison(df, parameter='pm25', save_fig=False):
    """
    Vergleich verschiedener Standorte für einen bestimmten Parameter
    
    Parameters:
        df (DataFrame): Luftqualitätsdaten
        parameter (str): Zu analysierender Parameter (z.B. 'pm25')
        save_fig (bool): Ob die Grafik gespeichert werden soll
    """
    if df is None or df.empty:
        print("Keine Daten zum Visualisieren vorhanden.")
        return
    
    # Prüfen, ob erforderliche Spalten vorhanden sind
    required_cols = ['parameter', 'value', 'location']
    if not all(col in df.columns for col in required_cols):
        print(f"Erforderliche Spalten fehlen. Benötigt: {required_cols}")
        return
    
    # Nur den ausgewählten Parameter filtern
    param_data = df[df['parameter'] == parameter]
    
    if param_data.empty:
        print(f"Keine Daten für Parameter '{parameter}' gefunden.")
        return
    
    # Gruppierung nach Standort für die Balkendiagramme
    location_data = param_data.groupby('location')['value'].mean().reset_index()
    
    # Einheit bestimmen
    unit = "AQI"
    if 'unit' in param_data.columns and not param_data['unit'].empty:
        unit = param_data['unit'].iloc[0]
    
    # Balkendiagramm erstellen
    plt.figure(figsize=(12, 6))
    
    bars = plt.bar(location_data['location'], location_data['value'], 
                   color=plt.cm.viridis(np.linspace(0, 0.8, len(location_data))))
    
    # Werte über den Balken anzeigen
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{height:.1f}', ha='center', va='bottom')
    
    # Titel und Beschriftungen
    current_date = datetime.now().strftime('%d.%m.%Y')
    plt.title(f'{parameter.upper()}-Werte nach Standort (Stand: {current_date})', fontsize=16)
    plt.ylabel(f'{parameter.upper()}-Wert ({unit})', fontsize=14)
    plt.xlabel('Standort', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Grafik speichern oder anzeigen
    if save_fig:
        fig_filename = f"vergleich_{parameter}_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(fig_filename, dpi=300, bbox_inches='tight')
        print(f"Grafik gespeichert als: {fig_filename}")
    
    # Grafik anzeigen
    plt.show()

def create_aqi_dashboard(df, save_fig=False):
    """
    Erstellt ein Dashboard mit mehreren Visualisierungen der Luftqualitätsdaten
    
    Parameters:
        df (DataFrame): Luftqualitätsdaten
        save_fig (bool): Ob die Grafik gespeichert werden soll
    """
    if df is None or df.empty:
        print("Keine Daten zum Visualisieren vorhanden.")
        return
    
    # Bestimme den Standort für den Titel
    location = "Unbekannt"
    if 'location' in df.columns and not df['location'].empty:
        location = df['location'].iloc[0]
        location = location.split(',')[0].split('(')[0].strip()
    
    # Einzigartige Parameter finden
    parameters = df['parameter'].unique().tolist()
    
    # Erstelle eine Subplot-Rasteranordnung
    fig = plt.figure(figsize=(15, 10))
    
    # Layout definieren: Zeitreihe oben, Aktuelle Werte unten links, AQI-Skala unten rechts
    gs = fig.add_gridspec(2, 2, height_ratios=[1.5, 1])
    
    # 1. Zeitreihe für alle Parameter
    ax_time = fig.add_subplot(gs[0, :])
    
    # Farben für verschiedene Parameter
    colors = plt.cm.tab10(np.linspace(0, 1, len(parameters)))
    
    # Für jeden Parameter einen Linienplot erstellen
    for i, param in enumerate(parameters):
        param_data = df[df['parameter'] == param].sort_values('datetime')
        
        if param_data.empty:
            continue
        
        # Einheitenbezeichnung
        unit = "AQI"
        if 'unit' in param_data.columns and not param_data['unit'].empty:
            unit = param_data['unit'].iloc[0]
        
        # Plot erstellen
        ax_time.plot(param_data['datetime'], param_data['value'], 
                     marker='o', linestyle='-', linewidth=2, 
                     color=colors[i], label=f"{param.upper()} ({unit})")
    
    # Bestimme den Zeitraum für die x-Achse
    if 'datetime' in df.columns and not df['datetime'].empty:
        min_date = df['datetime'].min()
        max_date = df['datetime'].max()
        
        # Formatierung für die x-Achse je nach Zeitraum
        time_range = max_date - min_date
        
        if time_range <= timedelta(hours=24):
            # Stündliche Ansicht
            ax_time.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax_time.set_xlabel('Uhrzeit', fontsize=12)
        else:
            # Tägliche Ansicht
            ax_time.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.'))
            ax_time.set_xlabel('Datum', fontsize=12)
    
    ax_time.set_title(f'Luftqualitätsindizes über Zeit', fontsize=14)
    ax_time.set_ylabel('Wert', fontsize=12)
    ax_time.grid(True, linestyle='--', alpha=0.7)
    ax_time.legend(fontsize=10)
    
    # 2. Aktuelle Werte als Balkendiagramm
    ax_bar = fig.add_subplot(gs[1, 0])
    
    # Neueste Werte für jeden Parameter
    latest_values = []
    for param in parameters:
        param_data = df[df['parameter'] == param].sort_values('datetime')
        if not param_data.empty:
            latest = param_data.iloc[-1]
            latest_values.append({
                'parameter': param.upper(),
                'value': latest['value']
            })
    
    latest_df = pd.DataFrame(latest_values)
    
    # Balkendiagramm für aktuelle Werte
    bars = ax_bar.bar(latest_df['parameter'], latest_df['value'], 
                     color=plt.cm.tab10(np.linspace(0, 1, len(latest_df))))
    
    # Werte über den Balken anzeigen
    for bar in bars:
        height = bar.get_height()
        ax_bar.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    
    ax_bar.set_title('Aktuelle Messwerte', fontsize=14)
    ax_bar.set_ylabel('Wert', fontsize=12)
    ax_bar.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    # 3. AQI-Skala und Informationen
    ax_info = fig.add_subplot(gs[1, 1])
    
    # AQI-Kategorien
    aqi_levels = [
        (0, 50, 'Gut', 'green'),
        (51, 100, 'Moderat', 'yellow'),
        (101, 150, 'Ungesund für sensible Gruppen', 'orange'),
        (151, 200, 'Ungesund', 'red'),
        (201, 300, 'Sehr ungesund', 'purple'),
        (301, 500, 'Gefährlich', 'brown')
    ]
    
    # AQI-Skala visualisieren
    y_pos = np.arange(len(aqi_levels))
    ax_info.set_yticks(y_pos)
    ax_info.set_yticklabels([level[2] for level in aqi_levels])
    
    # Farbige Balken für AQI-Kategorien
    for i, (low, high, label, color) in enumerate(aqi_levels):
        width = (high - low) / 50  # Skalieren für bessere Visualisierung
        ax_info.barh(i, width, color=color, alpha=0.7)
        ax_info.text(width/2, i, f"{low}-{high}", 
                    ha='center', va='center', color='black', fontweight='bold')
    
    ax_info.set_title('AQI-Skala und Gesundheitsauswirkungen', fontsize=14)
    ax_info.set_xlim([0, 10])  # Skalieren für bessere Darstellung
    ax_info.set_xticks([])  # x-Achsenbeschriftung ausblenden
    
    # Haupttitel für das gesamte Dashboard
    current_date = datetime.now().strftime('%d.%m.%Y %H:%M')
    fig.suptitle(f'Luftqualitätsdashboard: {location} (Stand: {current_date})', 
                fontsize=18, y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Platz für den Haupttitel lassen
    
    # Grafik speichern oder anzeigen
    if save_fig:
        safe_location = ''.join(c if c.isalnum() else '_' for c in location)
        fig_filename = f"dashboard_{safe_location}_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(fig_filename, dpi=300, bbox_inches='tight')
        print(f"Dashboard gespeichert als: {fig_filename}")
    
    # Grafik anzeigen
    plt.show()

def main():
    """Hauptfunktion zum Starten der Visualisierung"""
    # Befehlszeilenargumente verarbeiten
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = None
    
    # Daten laden
    air_data = load_air_quality_data(file_path)
    
    if air_data is None:
        return
    
    print("\nVerfügbare Parameter:")
    parameters = air_data['parameter'].unique()
    for i, param in enumerate(parameters):
        print(f"{i+1}. {param}")
    
    # Menüoptionen anzeigen
    print("\nVisualisierungsoptionen:")
    print("1. Alle Parameter über Zeit darstellen")
    print("2. Bestimmte Parameter auswählen")
    print("3. Dashboard erstellen")
    print("4. Beenden")
    
    choice = input("\nWähle eine Option (1-4): ")
    
    if choice == "1":
        save = input("Grafik speichern? (j/n): ").lower() == 'j'
        plot_air_quality_parameters(air_data, save_fig=save)
    
    elif choice == "2":
        param_input = input("Parameter eingeben (durch Komma getrennt, z.B. pm25,o3): ")
        selected_params = [p.strip().lower() for p in param_input.split(',')]
        save = input("Grafik speichern? (j/n): ").lower() == 'j'
        plot_air_quality_parameters(air_data, parameters=selected_params, save_fig=save)
    
    elif choice == "3":
        save = input("Dashboard speichern? (j/n): ").lower() == 'j'
        create_aqi_dashboard(air_data, save_fig=save)
    
    elif choice == "4":
        print("Programm wird beendet.")
    
    else:
        print("Ungültige Auswahl.")

if __name__ == "__main__":
    main()