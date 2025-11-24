"""
Data processing functions for fire prediction model.
Based on Ygol.ipynb data preparation pipeline.
"""

import pandas as pd
import numpy as np
import glob
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def load_raw_data(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load raw data from CSV files.

    Args:
        data_dir: Path to data directory

    Returns:
        Tuple of (fires, temperature, supplies, weather) DataFrames
    """
    data_dir = Path(data_dir)

    logger.info(f"Loading data from {data_dir}")

    fires = pd.read_csv(data_dir / "fires.csv", sep=",")
    temperature = pd.read_csv(data_dir / "temperature.csv", sep=",")
    supplies = pd.read_csv(data_dir / "supplies.csv", sep=",")

    # Load all weather files
    weather_files = glob.glob(str(data_dir / "weather_data_*.csv"))
    weather_list = [pd.read_csv(f, sep=",") for f in weather_files]
    weather = pd.concat(weather_list, ignore_index=True)

    logger.info(f"Loaded fires: {fires.shape}, temperature: {temperature.shape}, "
                f"supplies: {supplies.shape}, weather: {weather.shape}")

    return fires, temperature, supplies, weather


def rename_columns(fires: pd.DataFrame, temperature: pd.DataFrame,
                   supplies: pd.DataFrame, weather: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Rename columns to English names.

    Args:
        fires, temperature, supplies, weather: Raw DataFrames

    Returns:
        Tuple of renamed DataFrames
    """
    fires = fires.rename(columns={
        "Груз": "coal_grade",
        "Склад": "stockyard",
        "Дата начала": "fire_start",
        "Дата оконч.": "fire_end",
        "Нач.форм.штабеля": "pile_start",
        "Штабель": "pile_id"
    })

    temperature = temperature.rename(columns={
        "Штабель": "pile_id",
        "Марка": "coal_grade",
        "Максимальная температура": "temp_max",
        "Пикет": "location",
        "Дата акта": "date",
        "Смена": "shift"
    })

    supplies = supplies.rename(columns={
        "ВыгрузкаНаСклад": "unload_time",
        "Наим. ЕТСНГ": "coal_grade",
        "Штабель": "pile_id",
        "ПогрузкаНаСудно": "load_time",
        "На склад, тн": "to_stock_tons",
        "На судно, тн": "from_stock_tons",
        "Склад": "stockyard"
    })

    weather = weather.rename(columns={
        "t": "temp_air",
        "p": "pressure",
        "humidity": "humidity",
        "precipitation": "precip",
        "wind_dir": "wind_dir",
        "v_avg": "wind_avg",
        "v_max": "wind_max",
        "cloudcover": "cloudcover",
        "visibility": "visibility",
        "weather_code": "weather_code"
    })

    return fires, temperature, supplies, weather


def parse_dates(fires: pd.DataFrame, temperature: pd.DataFrame,
                supplies: pd.DataFrame, weather: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Parse date columns to datetime format.

    Args:
        fires, temperature, supplies, weather: DataFrames with renamed columns

    Returns:
        Tuple of DataFrames with parsed dates
    """
    # fires
    fires["fire_start"] = pd.to_datetime(fires["fire_start"], errors="coerce")
    fires["fire_end"] = pd.to_datetime(fires["fire_end"], errors="coerce")
    fires["pile_start"] = pd.to_datetime(fires["pile_start"], errors="coerce")

    # temperature
    temperature["date"] = pd.to_datetime(temperature["date"], errors="coerce")

    # supplies
    supplies["unload_time"] = pd.to_datetime(supplies["unload_time"], errors="coerce")
    supplies["load_time"] = pd.to_datetime(supplies["load_time"], errors="coerce")
    supplies["unload_date"] = pd.to_datetime(supplies["unload_time"].dt.date)
    supplies["load_date"] = pd.to_datetime(supplies["load_time"].dt.date)

    # weather - find date column
    date_col = None
    for cand in ["dt", "date", "datetime", "time"]:
        if cand in weather.columns:
            date_col = cand
            break

    if date_col is None:
        raise ValueError("Date column not found in weather data")

    weather[date_col] = pd.to_datetime(weather[date_col], errors="coerce")
    weather["date"] = pd.to_datetime(weather[date_col].dt.date)

    return fires, temperature, supplies, weather


def build_temperature_daily(temperature: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate temperature data by pile and day.

    Args:
        temperature: Temperature DataFrame with parsed dates

    Returns:
        Daily aggregated temperature DataFrame
    """
    agg = (
        temperature
        .sort_values(["pile_id", "date"])
        .groupby(["pile_id", "date"])
        .agg(
            temp_max_mean=("temp_max", "mean"),
            temp_max_min=("temp_max", "min"),
            temp_max_max=("temp_max", "max"),
            temp_max_std=("temp_max", "std"),
            n_measurements=("temp_max", "count"),
            coal_grade=("coal_grade", "first")
        )
        .reset_index()
    )

    return agg


def build_supplies_daily(supplies: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate supply logistics by pile and day, calculate cumulative stock.

    Args:
        supplies: Supplies DataFrame with parsed dates

    Returns:
        Daily aggregated supplies DataFrame with stock levels
    """
    # Incoming to stock
    incoming = (
        supplies
        .dropna(subset=["unload_date"])
        .groupby(["pile_id", "unload_date"])
        .agg(to_stock_tons_daily=("to_stock_tons", "sum"))
        .reset_index()
        .rename(columns={"unload_date": "date"})
    )

    # Outgoing from stock
    outgoing = (
        supplies
        .dropna(subset=["load_date"])
        .groupby(["pile_id", "load_date"])
        .agg(from_stock_tons_daily=("from_stock_tons", "sum"))
        .reset_index()
        .rename(columns={"load_date": "date"})
    )

    daily = pd.merge(incoming, outgoing, on=["pile_id", "date"], how="outer")

    daily["to_stock_tons_daily"] = daily["to_stock_tons_daily"].fillna(0.0)
    daily["from_stock_tons_daily"] = daily["from_stock_tons_daily"].fillna(0.0)

    daily = daily.sort_values(["pile_id", "date"])
    daily["net_flow"] = daily["to_stock_tons_daily"] - daily["from_stock_tons_daily"]

    # Cumulative stock
    daily["stock_tons"] = daily.groupby("pile_id")["net_flow"].cumsum()

    return daily


def build_weather_daily(weather: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate weather data by day.

    Args:
        weather: Weather DataFrame with parsed dates

    Returns:
        Daily aggregated weather DataFrame
    """
    agg = (
        weather
        .groupby("date")
        .agg(
            temp_air_mean=("temp_air", "mean"),
            temp_air_min=("temp_air", "min"),
            temp_air_max=("temp_air", "max"),
            humidity_mean=("humidity", "mean"),
            precip_sum=("precip", "sum"),
            wind_avg_mean=("wind_avg", "mean"),
            wind_max_max=("wind_max", "max"),
            cloudcover_mean=("cloudcover", "mean"),
            visibility_mean=("visibility", "mean")
        )
        .reset_index()
    )
    return agg


def add_fire_labels(base_df: pd.DataFrame, fires: pd.DataFrame,
                    horizon_days: int = 3) -> pd.DataFrame:
    """
    Add fire labels and targets to the dataset.

    Args:
        base_df: Base DataFrame with features
        fires: Fires DataFrame
        horizon_days: Prediction horizon in days

    Returns:
        DataFrame with fire labels
    """
    fire_first = (
        fires
        .dropna(subset=["fire_start"])
        .sort_values("fire_start")
        .groupby("pile_id")
        .first()
        .reset_index()[["pile_id", "fire_start", "coal_grade", "stockyard"]]
    )

    df = base_df.merge(fire_first, on="pile_id", how="left", suffixes=("", "_fire"))

    df["days_to_fire"] = (df["fire_start"] - df["date"]).dt.days
    df["days_to_fire"] = df["days_to_fire"].astype("float")

    df["fire_in_horizon"] = np.where(
        (df["days_to_fire"] >= 0) & (df["days_to_fire"] <= horizon_days),
        1, 0
    )

    df["ever_fire"] = np.where(df["fire_start"].notna(), 1, 0)

    return df


def add_stockyard_from_supplies(full_df: pd.DataFrame, supplies: pd.DataFrame) -> pd.DataFrame:
    """
    Add stockyard information from supplies if missing.

    Args:
        full_df: Full DataFrame
        supplies: Supplies DataFrame

    Returns:
        DataFrame with stockyard information
    """
    supplies_meta = (
        supplies[["pile_id", "stockyard"]]
        .dropna()
        .drop_duplicates()
    )

    df = full_df.merge(
        supplies_meta,
        on="pile_id",
        how="left",
        suffixes=("", "_sup")
    )

    df["stockyard"] = df["stockyard"].fillna(df["stockyard_sup"])
    df = df.drop(columns=["stockyard_sup"])

    return df


def build_full_dataset(data_dir: str, horizon_days: int = 3) -> pd.DataFrame:
    """
    Main function to build complete dataset.

    Args:
        data_dir: Path to data directory
        horizon_days: Prediction horizon in days

    Returns:
        Complete DataFrame ready for training
    """
    logger.info("Building full dataset...")

    fires, temperature, supplies, weather = load_raw_data(data_dir)
    fires, temperature, supplies, weather = rename_columns(fires, temperature, supplies, weather)
    fires, temperature, supplies, weather = parse_dates(fires, temperature, supplies, weather)

    temp_daily = build_temperature_daily(temperature)
    supplies_daily = build_supplies_daily(supplies)
    weather_daily = build_weather_daily(weather)

    base = temp_daily.merge(supplies_daily, on=["pile_id", "date"], how="left")
    base = base.merge(weather_daily, on="date", how="left")

    full_df = add_fire_labels(base, fires, horizon_days=horizon_days)
    full_df = add_stockyard_from_supplies(full_df, supplies)

    # Sort by pile and date
    full_df = full_df.sort_values(["pile_id", "date"]).reset_index(drop=True)

    logger.info(f"Full dataset shape: {full_df.shape}")

    return full_df