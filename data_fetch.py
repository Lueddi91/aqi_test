#!/usr/bin/python

import configparser
import json
import pickle
import sys

config = configparser.ConfigParser()

config.read("database.ini")

key = config["AQI"]["apikey"]

import requests
import pandas as pd
import os
from datetime import datetime

def get_aqicn_air_quality_data(city=None, token=None, save_csv=True):
    """
    AQICN.org API abfragen, um Luftqualitätsdaten zu erhalten
    
    Parameters:
        city (str): Stadt oder Ort (z.B. 'berlin', 'shanghai', usw.)
        token (str): API-Token für AQICN.org (kostenlos erhältlich)
    
    Returns:
        DataFrame: Pandas DataFrame mit Luftqualitätsdaten
    """
    # API-Token laden oder aus Parameter verwenden
    api_token = key 

    if not api_token:
        print("Fehler: AQICN API-Token fehlt. Registriere dich für einen kostenlosen Token auf https://aqicn.org/data-platform/token/")
        return None
    
    # API-Endpunkt für die Stadtabfrage
    base_url = f"https://api.waqi.info/feed/{city}/"
    
    params = {
        "token": api_token
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Fehler auslösen, wenn Request nicht erfolgreich
        
        data = response.json()
        #print(data)

        # Prüfen, ob die Anfrage erfolgreich war
        if data["status"] != "ok":
            print(f"API-Fehler: {data.get('data', 'Unbekannter Fehler')}")
            return None
        
        if "data" not in data:
            print(f"Keine Daten für {city} gefunden.")
            return None
        
        # Relevante Daten extrahieren
        station_data = data["data"]
        
        # Grundinformationen
        station_name = station_data.get("city", {}).get("name", "Unbekannt")
        timestamp = pd.to_datetime(station_data.get("time", {}).get("iso"), utc=True)
        
        # Messwerte extrahieren
        measurements = []
        iaqi = station_data.get("iaqi", {})

        # Für jeden Parameter (pm25, pm10, o3, etc.) einen Eintrag erstellen
        for parameter, value_dict in iaqi.items():
            if isinstance(value_dict, dict) and "v" in value_dict:
                measurements.append({
                    "location": station_name,
                    "parameter": parameter,
                    "value": value_dict["v"],
                    "unit": "AQI",  # AQICN gibt AQI-Werte zurück, nicht Rohwerte
                    "datetime": timestamp
                })
        
        # Erstellen eines DataFrame aus den Messungen
        df = pd.DataFrame(measurements)
        
        # Zusätzliche Stationsinformationen hinzufügen, falls gewünscht
        df["lat"] = station_data.get("city", {}).get("geo", [0, 0])[0]
        df["lon"] = station_data.get("city", {}).get("geo", [0, 0])[1]
        df["attribution"] = str(station_data.get("attributions", []))

        if save_csv:
            # Daten als CSV speichern mit Stadtnamen im Dateinamen
            current_date = datetime.now().strftime("%Y%m%d") + "-" + datetime.now().strftime("%H%M")
            # Extrahiere den Stadtnamen aus dem ersten Datensatz oder verwende den angegebenen Stadt-Parameter
            city_name = city.lower()
            if not df.empty and 'location' in df.columns:
                # Verwende den Standortnamen aus den Daten, falls verfügbar
                location_name = df['location'].iloc[0]
                # Extrahiere den Hauptstadtnamen (vor Komma oder Klammer)
                city_name = location_name.split(',')[0].split('(')[0].strip().lower()
            
            # Erstelle einen gültigen Dateinamen (ersetze Leerzeichen und Sonderzeichen)
            safe_city_name = ''.join(c if c.isalnum() else '_' for c in city_name)
            
            csv_filename = f"aqicn_luftqualitaet_{safe_city_name}_{current_date}.csv"
            df.to_csv(csv_filename, index=False)
            print(f"\nDaten wurden als CSV für {city_name} gespeichert: {csv_filename}")  
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim API-Aufruf: {e}")
        return None

def get_aqicn_historical_data(city="berlin", parameter="pm25", start_date=None, end_date=None, token=None):
    """
    Historische Daten von AQICN.org abrufen (erfordert möglicherweise ein Premium-Konto)
    
    Parameters:
        city (str): Stadt oder Ort
        parameter (str): Luftqualitätsparameter (pm25, pm10, o3, no2, so2, co)
        start_date (str): Startdatum im Format 'YYYY-MM-DD'
        end_date (str): Enddatum im Format 'YYYY-MM-DD'
        token (str): API-Token für AQICN.org
    
    Returns:
        DataFrame: Pandas DataFrame mit historischen Luftqualitätsdaten
    """
    # API-Token laden oder aus Parameter verwenden
    load_dotenv()
    api_token = token or os.getenv("AQICN_TOKEN")
    
    if not api_token:
        print("Fehler: AQICN API-Token fehlt.")
        return None
    
    # Falls keine Datumsangaben gemacht wurden, die letzten 30 Tage verwenden
    if not start_date:
        start_date = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # API-Endpunkt für historische Daten
    # Hinweis: Der genaue Endpunkt kann sich je nach API-Version ändern
    base_url = f"https://api.waqi.info/feed/{city}/historical/"
    
    params = {
        "token": api_token,
        "parameter": parameter,
        "start": start_date,
        "end": end_date
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Prüfen, ob die Anfrage erfolgreich war
        if data["status"] != "ok":
            error_msg = data.get("data", "Unbekannter Fehler")
            print(f"API-Fehler bei historischen Daten: {error_msg}")
            # Falls ein Zugangsfehler auftritt, Hinweis auf Premium-Konto geben
            if "premium" in str(error_msg).lower():
                print("Hinweis: Für historische Daten wird möglicherweise ein Premium-Konto bei AQICN benötigt.")
            return None
        
        # Datenverarbeitung würde hier fortgesetzt werden
        # (Die genaue Struktur der API-Antwort für historische Daten kann variieren)
        
        # Hinweis: Dies ist ein Platzhalter, da der Zugriff auf historische Daten
        # bei AQICN oft eingeschränkt ist oder ein Premium-Konto erfordert
        print("Historische Daten erfolgreich abgerufen.")
        
        return pd.DataFrame(data.get("data", []))
    
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim API-Aufruf für historische Daten: {e}")
        return None

if __name__ == "__main__":
    # Beispiel: Aktuelle Luftqualitätsdaten für Berlin abrufen
    # Setze deinen API-Token entweder als Umgebungsvariable AQICN_TOKEN oder übergebe ihn direkt
    # Du kannst einen kostenlosen Token auf https://aqicn.org/data-platform/token/ erhalten
    
    # Beispiel mit API-Token als Parameter
    # air_data = get_aqicn_air_quality_data(city="berlin", token="dein_api_token_hier")
    
    # Beispiel mit API-Token aus Umgebungsvariable
    if len(sys.argv) > 1:
        for arg in range(len(sys.argv)):
            air_data = get_aqicn_air_quality_data(city=sys.argv[arg], save_csv=True)

    else:
        air_data = get_aqicn_air_quality_data(city="hamburg", save_csv=True)

    if air_data is not None:
        print(f"Anzahl der abgerufenen Parameter: {len(air_data)}")
        print("\nAktuelle Luftqualitätsdaten:")
        print(air_data[["location", "parameter", "value", "unit", "datetime"]])
        
              
    # Beispiel für historische Daten (erfordert möglicherweise Premium-Konto)
    # hist_data = get_aqicn_historical_data(city="berlin", parameter="pm25")
    # if hist_data is not None:
    #     print("\nHistorische Daten:")
    #     print(hist_data.head())
