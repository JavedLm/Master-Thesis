import pandas as pd
import os
from datetime import datetime
from meteostat import Point, Hourly
import numpy as np
import pgeocode
import holidays

selected_load_ids = [1, 23, 49, 997]

r"Folder with the datasets, sy like .../EVA - ÜGZ Load"
dir_path = r"..."

r"Folder to save the results"
selected_data_path = rf"..."

# Name of the 3 datasets
files = ["hlt_profiles_tabsep.csv", "load_profiles_tabsep.csv", "master_data_tabsep.csv"]

def plz2_to_centroid_and_state(plz2: str):
    """
    Returns:
      (lat, lon, state_name)
    computed from all 5-digit DE postal codes starting with the given 2-digit prefix.
    """
    _nomi_de = pgeocode.Nominatim("de")

    plz2 = str(plz2).zfill(2)

    # pgeocode dataset (DataFrame)
    codes = _nomi_de._data.copy()

    pc = codes["postal_code"].astype(str).str.replace(r"\.0$", "", regex=True)

    subset = codes[pc.str.startswith(plz2)].copy()

    # keep rows with valid coordinates
    subset = subset.dropna(subset=["latitude", "longitude"])
    if subset.empty:
        raise ValueError(f"No matches / no coordinates for PLZ prefix {plz2}")

    lat = float(subset["latitude"].mean())
    lon = float(subset["longitude"].mean())

    # state name (mode = most frequent)
    state_col = "state_name" if "state_name" in subset.columns else None
    state = None
    if state_col:
        m = subset[state_col].dropna()
        state = str(m.mode().iloc[0]) if not m.empty else None

    return lat, lon, state

# Get weather data
def get_weather_2016_meteostat(lat, lon):
    start = datetime(2016, 1, 1)
    end   = datetime(2016, 12, 31, 23, 59)
    p = Point(lat, lon)
    weather_h = Hourly(p, start, end).fetch()
    weather_h.index = pd.to_datetime(weather_h.index)
    return weather_h

def merge_weather_15min(df_load_15min, weather_hourly):
    # Upsample hourly → 15min and forward-fill (common for weather features)
    weather_15 = weather_hourly.resample("15min").ffill()

    # Align to load index and merge
    weather_15 = weather_15.reindex(df_load_15min.index, method="ffill")
    return df_load_15min.join(weather_15, how="left")

# Add calendar variables
def add_basic_calendar_features(df):
    out = df.copy()
    idx = out.index

    out["dow"] = idx.dayofweek          # 0=Mon .. 6=Sun
    out["is_weekend"] = (out["dow"] >= 5).astype(int)
    out["hour"] = idx.hour
    out["minute"] = idx.minute
    out["month"] = idx.month
    out["is_workday"] = (out["dow"] < 5).astype(int)
    return out

def add_cyclical_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    idx = out.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise TypeError("df.index must be a DatetimeIndex")

    # --- daily cycle (minute-of-day) ---
    minute_of_day = idx.hour * 60 + idx.minute
    out["sin_day"] = np.sin(2 * np.pi * minute_of_day / (24 * 60))
    out["cos_day"] = np.cos(2 * np.pi * minute_of_day / (24 * 60))

    # --- weekly cycle (day-of-week) optional but often useful ---
    dow = idx.dayofweek  # 0..6
    out["sin_week"] = np.sin(2 * np.pi * dow / 7)
    out["cos_week"] = np.cos(2 * np.pi * dow / 7)

    # --- yearly cycle (day-of-year; handles leap years) ---
    doy = idx.dayofyear  # 1..365/366
    days_in_year = 366 if idx.is_leap_year.any() else 365
    out["sin_year"] = np.sin(2 * np.pi * doy / days_in_year)
    out["cos_year"] = np.cos(2 * np.pi * doy / days_in_year)

    return out

def add_holiday_features_by_plz2(df, state, years=None, time_col=None):
    """
    Adds:
      - is_holiday (0/1)
      - holiday_name (string, optional)
    based on German state approximated from PLZ2.
    """
    out = df.copy()
    idx = out.index if time_col is None else pd.to_datetime(out[time_col])

    if years is None:
        years = sorted(set(idx.year))

    de_holidays = holidays.country_holidays("DE", subdiv=state, years=years)

    dates = idx.normalize()
    out["is_holiday"] = dates.isin(de_holidays).astype(int)

    return out

if __name__ == "__main__":

    # Read data
    data_dict = {}

    for fname in files:
        file_path = os.path.join(dir_path, fname)
        dat = pd.read_csv(file_path, sep="\t")
        dat = dat.loc[:, ~dat.columns.str.contains('^Unnamed')]
        data_dict[fname] = dat

    master_data = data_dict[files[2]]
    load_data = data_dict[files[1]]

    selected_master_data = master_data[np.isin(master_data["Id"], selected_load_ids)]

    selected_load_data = load_data[load_data.id.isin(selected_master_data.Id)]
    selected_load_data.index = selected_load_data.id
    selected_load_data.drop("id", axis=1, inplace=True)

    df = selected_load_data.T

    time_index = pd.date_range(
        start="2016-01-01 00:00:00",
        end="2016-12-31 23:45:00",
        freq="15min"
    )
    df.index = time_index

    # Merge with weather data
    lat_long = {}
    for id, zip_prefix in zip(selected_master_data.Id, selected_master_data.Zip_code):
        lat_long[id] = plz2_to_centroid_and_state(plz2=str(zip_prefix))

    load_datasets = {}
    for load_var in df.columns:
        weather_dat = get_weather_2016_meteostat(lat_long[load_var][0], lat_long[load_var][1])
        merged_dat = merge_weather_15min(df.loc[:, [load_var]], weather_dat)
        load_datasets[load_var] = merged_dat.rename(columns={merged_dat.columns[0]: "load"})

    # Add calendar features
    for load_var in load_datasets.keys():
        basic_calendar_extension = add_basic_calendar_features(load_datasets[load_var])
        cyclical_time_extension = add_cyclical_time_features(basic_calendar_extension)
        calendar_extended_dat = add_holiday_features_by_plz2(cyclical_time_extension, lat_long[load_var][2])
        load_datasets[load_var] = calendar_extended_dat

    # Save data and explo for all selected datasets
    os.makedirs(selected_data_path, exist_ok=True)
    for load_var in df.columns:
        act_df = load_datasets[load_var]
        act_df.to_csv(rf"{selected_data_path}/{load_var}.csv")
