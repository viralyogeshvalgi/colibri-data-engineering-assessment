
from pathlib import Path
import pandas as pd


# File locations
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_data():
    """Load the three CSV files into one dataset."""

    files = [
        DATA_DIR / "data_group_1.csv",
        DATA_DIR / "data_group_2.csv",
        DATA_DIR / "data_group_3.csv"
    ]

    dataframes = []

    for file in files:
        df = pd.read_csv(file)
        print(f"Loaded {file.name}: {len(df)} rows")
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)

    return combined_df


def profile_data(df):
    """Check the raw data for any issues."""

    print("\n--- DATA QUALITY REPORT ---")

    # Convert timestamps so we can check the dates and missing hours
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    print("\nDate range:")
    print(df["timestamp"].min(), "to", df["timestamp"].max())

    # Check for more than one reading per turbine at the same hour
    duplicate_keys = df.duplicated(
        subset=["timestamp", "turbine_id"]
    ).sum()

    print("\nDuplicate turbine-hour records:", duplicate_keys)

    print("\nRecords per turbine:")
    print(df.groupby("turbine_id").size())

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nSensor statistics:")
    print(df[["wind_speed", "wind_direction", "power_output"]].describe())

    # Check for readings outside valid ranges
    invalid_wind_speed = (df["wind_speed"] < 0).sum()

    invalid_direction = (
        (df["wind_direction"] < 0) |
        (df["wind_direction"] > 360)
    ).sum()

    invalid_power = (df["power_output"] < 0).sum()

    print("\nNegative wind speeds:", invalid_wind_speed)
    print("Invalid wind directions:", invalid_direction)
    print("Negative power readings:", invalid_power)

    # There should be 24 hourly readings per day for each turbine
    expected_hours = pd.date_range(
        start="2022-03-01",
        end="2022-03-31 23:00:00",
        freq="h"
    )

    print("\nMissing hourly observations:")

    for turbine_id, group in df.groupby("turbine_id"):
        missing_hours = expected_hours.difference(group["timestamp"])

        print(f"Turbine {turbine_id}: {len(missing_hours)} missing hours")

    return df


def clean_data(df):
    """Apply cleaning rules to the sensor data."""

    df = df.copy()

    print("\n--- DATA CLEANING ---")

    initial_rows = len(df)

    # Remove duplicates so readings aren't counted twice
    df = df.drop_duplicates()

    # Keep one reading per turbine and timestamp
    df = df.drop_duplicates(
        subset=["timestamp", "turbine_id"],
        keep="first"
    )

    # Only expecting turbine IDs from 1 to 15
    df = df[df["turbine_id"].between(1, 15)]

    # Only keep readings from March 2022
    df = df[
        df["timestamp"].between(
            "2022-03-01",
            "2022-03-31 23:00:00"
        )
    ].copy()

    # Use NaN for invalid values rather than replacing them with zero
    df.loc[df["wind_speed"] < 0, "wind_speed"] = float("nan")

    df.loc[
        ~df["wind_direction"].between(0, 360),
        "wind_direction"
    ] = float("nan")

    df.loc[df["power_output"] < 0, "power_output"] = float("nan")

    df = df.sort_values(
        ["turbine_id", "timestamp"]
    ).reset_index(drop=True)

    print(f"Rows before cleaning: {initial_rows}")
    print(f"Rows after cleaning: {len(df)}")
    print(f"Rows removed: {initial_rows - len(df)}")

    return df


def calculate_daily_summary(df):
    """Calculate the daily power figures for each turbine."""

    print("\n--- DAILY TURBINE SUMMARY ---")

    df = df.copy()

    # Separate the date from the hourly timestamp
    df["date"] = df["timestamp"].dt.date

    # Group by day and turbine, then calculate power statistics
    daily_summary = (
        df.groupby(["date", "turbine_id"])
        .agg(
            min_power=("power_output", "min"),
            max_power=("power_output", "max"),
            avg_power=("power_output", "mean"),
            reading_count=("power_output", "count")
        )
        .reset_index()
    )

    daily_summary = daily_summary.sort_values(
        ["date", "turbine_id"]
    ).reset_index(drop=True)

    print(f"Daily summary records: {len(daily_summary)}")

    print("\nFirst 10 daily summaries:")
    print(daily_summary.head(10))

    return daily_summary


def detect_anomalies(daily_summary):
    """Identify turbines with unusual daily average power output."""

    print("\n--- ANOMALY DETECTION ---")

    daily_summary = daily_summary.copy()

    # Get the mean and standard deviation of the turbine averages each day
    daily_stats = (
        daily_summary.groupby("date")["avg_power"]
        .agg(
            daily_mean="mean",
            daily_std=lambda x: x.std(ddof=0)
        )
        .reset_index()
    )

    # Add these daily figures back to each turbine
    daily_summary = daily_summary.merge(
        daily_stats,
        on="date",
        how="left"
    )

    # Work out the upper and lower limits using 2 standard deviations
    daily_summary["lower_threshold"] = (
        daily_summary["daily_mean"] - 2 * daily_summary["daily_std"]
    )

    daily_summary["upper_threshold"] = (
        daily_summary["daily_mean"] + 2 * daily_summary["daily_std"]
    )

    # Flag turbines outside those limits
    daily_summary["is_anomaly"] = (
        (daily_summary["avg_power"] < daily_summary["lower_threshold"]) |
        (daily_summary["avg_power"] > daily_summary["upper_threshold"])
    )

    anomalies = daily_summary[daily_summary["is_anomaly"]]

    print(f"Total anomalies detected: {len(anomalies)}")

    if not anomalies.empty:
        print("\nFlagged turbines:")
        print(
            anomalies[
                ["date", "turbine_id", "avg_power",
                 "daily_mean", "daily_std"]
            ].to_string(index=False)
        )
    else:
        print("No anomalies detected.")

    return daily_summary


def save_outputs(cleaned_df, daily_summary):
    """Save the cleaned data and daily summaries."""

    print("\n--- SAVING OUTPUTS ---")

    output_dir = BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = output_dir / "cleaned_data.csv"
    summary_path = output_dir / "daily_summary.csv"

    # Save the results as CSV files without the pandas index
    cleaned_df.to_csv(cleaned_path, index=False)
    daily_summary.to_csv(summary_path, index=False)

    print(f"Cleaned data saved to: {cleaned_path}")
    print(f"Daily summary saved to: {summary_path}")


def main():
    print("Starting wind turbine data pipeline...\n")

    df = load_data()
    df = profile_data(df)
    df = clean_data(df)

    daily_summary = calculate_daily_summary(df)
    daily_summary = detect_anomalies(daily_summary)

    save_outputs(df, daily_summary)

    print("\nPipeline completed.")


if __name__ == "__main__":
    main()
