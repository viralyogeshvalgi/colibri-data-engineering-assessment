# Wind Turbine Data Engineering Pipeline

## 1. Overview

This project uses Python and pandas to process hourly sensor data from 15 wind turbines over March 2022.

The aim was to combine the three CSV files, check for any data quality issues, clean the data where needed and calculate daily power output statistics for each turbine. I also implemented anomaly detection to identify turbines whose daily average power output was unusually high or low compared to the others.

The cleaned data and daily summaries are then saved as CSV files .

## 2. Technologies Used

- Python 3.12
- pandas 2.3.3

## 3. Project Structure

```text
colibri-data-engineering-assessment/
├── data/
│   ├── data_group_1.csv
│   ├── data_group_2.csv
│   └── data_group_3.csv
├── output/
│   ├── cleaned_data.csv
│   └── daily_summary.csv
├── main.py
├── requirements.txt
└── README.md
```

## 4. How to Run

Make sure Python is installed. I used Python 3.12 for this project.

Install the required packages by running:

```bash
python -m pip install -r requirements.txt
```

The three CSV files should be placed inside the `data/` folder.

To run the pipeline, open the terminal in the project directory and execute:

```bash
python main.py
```

This will load the data, carry out the cleaning and validation checks, calculate the daily summaries, detect anomalies and save the results in the `output/` folder.

## 5. Data Quality and Cleaning

After combining the three files, the dataset contained 11,160 records across 15 turbines.

I started by checking the data for missing values, duplicates, invalid measurements and missing hourly readings.

These were the results:

| Check | Result |
|---|---|
| Missing values | 0 |
| Exact duplicate rows | 0 |
| Duplicate turbine/timestamp records | 0 |
| Missing hourly readings | 0 |
| Negative wind speeds | 0 |
| Invalid wind directions | 0 |
| Negative power outputs | 0 |

I also checked the range of the sensor readings:

- Wind speed: 9–15 m/s
- Wind direction: 0–359°
- Power output: 1.5–4.5 MW

### How I handled the data

I added cleaning rules to deal with possible errors in the data.

- Duplicate rows are removed to avoid counting the same reading twice.
- If a turbine has multiple records for the same timestamp, the first record is kept.
- Turbine IDs outside the expected range of 1–15 are removed.
- Records outside March 2022 are excluded.
- Negative wind speeds, invalid wind directions and negative power outputs are replaced with `NaN` rather than zero, as zero could be a valid measurement.
- Finally, the data is sorted by turbine ID and timestamp.

For the supplied data, none of these issues were found, so no rows needed to be removed or values replaced.

The cleaned dataset therefore still contains all 11,160 records.

One limitation of the duplicate handling is that keeping the first record doesn't necessarily mean it is the correct one if the values conflict. In a real project, I would want to investigate these cases further.

## 6. Daily Power Summary

Using pandas `groupby()`, I calculated the following for each turbine on each day:

- Minimum power output (MW)
- Maximum power output (MW)
- Average power output (MW)
- Number of valid power readings

This produced 465 daily summary records, covering 15 turbines over 31 days.

Each turbine had 24 valid hourly power readings per day.

I included the reading count as an additional check, since an average calculated from fewer readings may be less representative of the full day.

## 7. Anomaly Detection

For anomaly detection, I compared each turbine's average daily power output against the other turbines on the same day.

For each day, I calculated the mean and standard deviation of the 15 turbine averages.

A turbine was flagged if its average was more than two standard deviations above or below the daily mean.

I used the population standard deviation (`ddof=0`) because all 15 turbines in the wind farm were included in the calculation.

### Results

The pipeline identified **20 anomalies** across March 2022.

The flagged turbines were:

| Date (March 2022) | Turbine ID |
|---|---|
| 1 | 15 |
| 2 | 2 |
| 3 | 12 |
| 4 | 8 |
| 6 | 3 |
| 7 | 1 |
| 8 | 11 |
| 11 | 4 |
| 12 | 12 |
| 13 | 7 |
| 15 | 9 |
| 18 | 2, 15 |
| 20 | 4 |
| 22 | 11 |
| 24 | 13 |
| 25 | 2 |
| 26 | 4 |
| 28 | 3 |
| 29 | 9 |

Turbines 2 and 4 were flagged most frequently, with three days each.

These anomalies don't necessarily mean the turbines are faulty. They just indicate that their average power output was noticeably different from the other turbines that day.

I kept these readings in the cleaned dataset, as they are still valid measurements based on the data quality checks.

## 8. Output Files

The pipeline generates two CSV files inside the `output/` folder.

**`cleaned_data.csv`**

Contains all 11,160 hourly readings after applying the cleaning rules .

**`daily_summary.csv`**

Contains the 465 daily turbine summaries, including minimum, maximum and average power output, reading counts, daily mean and standard deviation, anomaly thresholds and anomaly flags.

## 9. Assumptions

A few assumptions were made when processing the data:

- The data covers 1–31 March 2022.
- Valid turbine IDs range from 1 to 15.
- Wind speed is measured in m/s, wind direction in degrees and power output in MW.
- Wind directions between 0° and 360° are accepted, with 360° representing the same direction as 0°.
- Negative power output is considered invalid for this assessment.
- Invalid sensor readings are set to `NaN` instead of being replaced with zero or an estimated value.
- The 15 turbines are treated as the full population when calculating the daily standard deviation
- Anomaly detection is based on comparisons between turbines on the same day.

I also assumed that the provided measurements were otherwise reliable, as I didn't have access to turbine specifications, maintenance records or other operational information to verify whether each reading was realistic.

## 10. What I Would Improve With More Time

If I had more time, there are a few areas I would look to improve:

1. Add automated tests to check how the pipeline handles different types of missing, duplicated or invalid data.
2. Include more detailed logging to show how many records were affected by each cleaning rule.
3. Improve how conflicting readings for the same turbine and timestamp are handled, rather than automatically  keeping the first record.
4. Use turbine-specific operating limits or historical performance data to make anomaly detection more meaningful.
5. Look into scheduling the pipeline so it could process new readings automatically.
6. Explore using cloud services such as AWS or Azure if the data volumes increased or the pipeline needed to run  regularly

## 11. Validation

After running the pipeline, I checked the exported CSV files separately to make sure the results matched what I expected

The checks confirmed:

- Cleaned records: 11,160
- Daily summary records: 465
- Anomalies detected: 20
- Duplicate turbine-day records: 0
- Days with fewer than 15 turbines: 0
- Turbine-days with fewer than 24 valid power readings: 0

### Testing the Cleaning Function

Since the original dataset didn't contain any invalid readings based on my checks, I also tested the cleaning function using a small sample dataset with deliberately incorrect values.

The test included duplicate records, an invalid turbine ID, a negative wind speed, an out-of-range wind direction and a negative power output.

All the test assertions passed. The duplicate and invalid turbine ID were removed, while the invalid sensor values were replaced with `NaN`.

I ran this test separately, so the original data and final output files were not changed.