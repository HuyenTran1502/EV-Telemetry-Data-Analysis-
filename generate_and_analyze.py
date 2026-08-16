import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

np.random.seed(42)

# 1. Generate Synthetic Data
n_samples = 1500
time_ms = np.arange(0, n_samples * 1000, 1000) # 1 sec intervals
speed = np.zeros(n_samples)
for i in range(1, n_samples):
    speed[i] = max(0, speed[i-1] + np.random.normal(0, 2.5))
    if speed[i] > 120: speed[i] = 120

temp = np.random.normal(20, 5, n_samples)
accel = np.gradient(speed) / 3.6 # m/s^2

# Current depends heavily on acceleration and speed
current = (speed * 0.5) + (np.maximum(0, accel) * 50) + np.random.normal(0, 5, n_samples)
# Cold temp (<15) increases resistance -> higher current needed
current[temp < 15] *= 1.2
# Hot temp (>30) increases cooling system current
current[temp > 30] += 10

soc = np.zeros(n_samples)
soc[0] = 100
for i in range(1, n_samples):
    # battery capacity mock
    soc[i] = soc[i-1] - (current[i] / 3600) * 0.1 

df = pd.DataFrame({
    'DayNum': 1,
    'VehId': 101,
    'Trip': 1,
    'Timestamp(ms)': time_ms,
    'Vehicle Speed[km/h]': speed,
    'OAT[Celcius]': temp,
    'HV Battery Current[A]': current,
    'HV Battery SOC[%]': soc,
    'HV Battery Voltage[V]': np.random.normal(350, 2, n_samples)
})

df.to_csv('dataset.csv', index=False)

# 2. Generate Plots for README
import re
def clean_col(c):
    c = c.lower()
    c = re.sub(r'\[.*?\]|\(.*?\)', '', c)
    return c.strip().replace(' ', '_')

df.columns = [clean_col(c) for c in df.columns]
df['time_diff_sec'] = df['timestamp'].diff() / 1000.0
df['speed_diff_m_s'] = df['vehicle_speed'].diff() / 3.6
df['acceleration'] = df['speed_diff_m_s'] / df['time_diff_sec']
df['acceleration'] = df['acceleration'].fillna(0)

def classify(a):
    if a > 2.0: return 'Harsh Accel'
    elif a < -2.0: return 'Harsh Brake'
    elif abs(a) > 0.5: return 'Normal'
    else: return 'Cruise/Idle'

df['driving_style'] = df['acceleration'].apply(classify)
df['power_usage_abs'] = df['hv_battery_current'].abs()

plt.style.use('seaborn-v0_8-whitegrid')

# Plot 1: Correlation
plt.figure(figsize=(8,6))
sns.heatmap(df[['vehicle_speed', 'acceleration', 'hv_battery_current', 'hv_battery_soc', 'oat']].corr(), annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('correlation.png')
plt.close()

# Plot 2: Driving Style
plt.figure(figsize=(8,5))
sns.barplot(x='driving_style', y='power_usage_abs', data=df)
plt.title('Power Consumption by Driving Style')
plt.ylabel('Avg Current (A)')
plt.tight_layout()
plt.savefig('drivability.png')
plt.close()

# Plot 3: Temperature
df['temp_zone'] = pd.cut(df['oat'], bins=[-10, 15, 25, 50], labels=['Cold (<15C)', 'Optimal (15-25C)', 'Hot (>25C)'])
plt.figure(figsize=(8,5))
sns.boxplot(x='temp_zone', y='power_usage_abs', data=df[df['driving_style']=='Cruise/Idle'])
plt.title('Temperature Impact on Cruising Current')
plt.tight_layout()
plt.savefig('temperature.png')
plt.close()

# 3. Create Jupyter Notebook File
notebook = {
 "cells": [
  {"cell_type": "markdown", "metadata": {}, "source": ["# EV Telemetry Data Analysis (Energy Management)"]},
  {"cell_type": "code", "execution_count": 1, "metadata": {}, "outputs": [], "source": [
    "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport re\n",
    "plt.style.use('seaborn-v0_8-whitegrid')\n",
    "df = pd.read_csv('dataset.csv')\n",
    "df.head()"
  ]},
  {"cell_type": "code", "execution_count": 2, "metadata": {}, "outputs": [], "source": [
    "df.columns = [re.sub(r'\\[.*?\\]|\\(.*?\\)', '', c.lower()).strip().replace(' ', '_') for c in df.columns]\n",
    "df['acceleration'] = (df['vehicle_speed'].diff() / 3.6) / (df['timestamp'].diff() / 1000.0)\n",
    "df['acceleration'] = df['acceleration'].fillna(0)\n",
    "def classify(a):\n",
    "    if a > 2.0: return 'Harsh Accel'\n",
    "    elif a < -2.0: return 'Harsh Brake'\n",
    "    elif abs(a) > 0.5: return 'Normal'\n",
    "    else: return 'Cruise/Idle'\n",
    "df['driving_style'] = df['acceleration'].apply(classify)\n",
    "df['power_usage_abs'] = df['hv_battery_current'].abs()"
  ]},
  {"cell_type": "code", "execution_count": 3, "metadata": {}, "outputs": [], "source": [
    "plt.figure(figsize=(8,5))\n",
    "sns.barplot(x='driving_style', y='power_usage_abs', data=df)\n",
    "plt.title('Power Consumption by Driving Style')\n",
    "plt.show()"
  ]}
 ],
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
 "nbformat": 4, "nbformat_minor": 4
}
with open('ev_analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print("Data, Plots, and Notebook generated successfully.")
