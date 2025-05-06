import configparser

config = configparser.ConfigParser()

config.read("database.ini")

key = config["AQI"]["apikey"]


import requests
import pandas as pd
from datetime import datetime

def get_air_quality_data(country="DE", city="Berlin", parameter="pm25", limit=100):
    """
    OpenAQ API abfragen, um Luftqualitätsdaten zu erhalten
    
    Parameters:
        country (str): Ländercode (z.B. 'DE' für Deutschland)
        city (str): Stadt
        parameter (str): Luftqualitätsparameter (pm25, pm10, o3, no2, so2, co)
        limit (int): Maximale Anzahl der zurückgegebenen Datensätze
    
    Returns:
        DataFrame: Pandas DataFrame mit Luftqualitätsdaten
    """
    base_url = f"https://api.waqi.info/feed/@10833/?token={key}"
    
    params = {
        "country": country,
        "city": city,
        "parameter": parameter,
        "limit": limit,
        "order_by": "datetime",
        "sort": "desc"
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Fehler auslösen, wenn Request nicht erfolgreich
        
        data = response.json()
        
        if "results" not in data or len(data["results"]) == 0:
            print(f"Keine Daten für {city}, {country} gefunden.")
            return None
        
        # Daten in DataFrame umwandeln
        results = data["results"]
        df = pd.DataFrame(results)
        
        # Datum formatieren
        df["datetime"] = pd.to_datetime(df["date.utc"])
        
        # Relevante Spalten auswählen
        df = df[["location", "parameter", "value", "unit", "datetime"]]
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim API-Aufruf: {e}")
        return None

if __name__ == "__main__":
    # Beispielaufruf für Berlin, Deutschland, PM2.5-Werte
    air_data = get_air_quality_data(country="DE", city="Berlin", parameter="pm25")
    
    if air_data is not None:
        print(f"Anzahl der abgerufenen Datensätze: {len(air_data)}")
        print("\nLetzten 5 Einträge:")
        print(air_data.head(5))
        
        # Speichern der Daten als CSV (optional)
        current_date = datetime.now().strftime("%Y%m%d")
        air_data.to_csv(f"luftqualitaet_berlin_{current_date}.csv", index=False)
        print(f"\nDaten wurden als CSV gespeichert.")