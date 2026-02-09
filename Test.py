import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load your data
df = pd.read_csv('C:/Users/Javed Khan/Downloads/Fraunhofer MA Industrial Data Patterns/sample_data.csv')
df['Time+Date'] = pd.to_datetime(df['Time+Date'])
df = df.sort_values('Time+Date')

# # 1. Full time series
# fig, ax = plt.subplots(figsize=(16, 5))
# ax.plot(df['Time+Date'], df['Electrical_Load'], linewidth=0.8)
# ax.set_title('Electrical Load Over Full Time Period', fontsize=14)
# ax.set_ylabel('Load (kW)', fontsize=12)
# ax.grid(True, alpha=0.3)
# plt.tight_layout()
# plt.savefig('01_full_timeseries.png', dpi=300)
# plt.show()

# # 2. Monthly facet plot
# df['Month'] = df['Time+Date'].dt.month
# fig, axes = plt.subplots(4, 3, figsize=(18, 12))
# axes = axes.flatten()

# for month in range(1, 13):
#     month_data = df[df['Month'] == month]
#     axes[month-1].plot(month_data['Time+Date'], month_data['Electrical_Load'])
#     axes[month-1].set_title(f'Month {month}', fontsize=10)
#     axes[month-1].grid(True, alpha=0.3)

# plt.tight_layout()
# plt.savefig('02_monthly_decomposition.png', dpi=300)
# plt.show()

# # 3. Weekly zoom (first 2 weeks)
# two_weeks = df.head(336)  # 7 days × 24 hours × 2
# fig, ax = plt.subplots(figsize=(14, 5))
# ax.plot(two_weeks['Time+Date'], two_weeks['Electrical_Load'], marker='o', markersize=3)
# ax.set_title('Two-Week Detailed View (Daily Seasonality)', fontsize=14)
# ax.set_ylabel('Load (kW)', fontsize=12)
# ax.grid(True, alpha=0.3)
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.savefig('03_two_week_zoom.png', dpi=300)
# plt.show()

# # 4. Average hourly pattern (reveals daily seasonality)
# df['Hour'] = df['Time+Date'].dt.hour
# hourly_avg = df.groupby('Hour')['Electrical_Load'].mean()
# fig, ax = plt.subplots(figsize=(12, 5))
# ax.bar(hourly_avg.index, hourly_avg.values, color='steelblue')
# ax.set_title('Average Hourly Load Pattern (Daily Seasonality)', fontsize=14)
# ax.set_xlabel('Hour of Day', fontsize=12)
# ax.set_ylabel('Average Load (kW)', fontsize=12)
# ax.grid(True, axis='y', alpha=0.3)
# plt.tight_layout()
# plt.savefig('04_daily_seasonality.png', dpi=300)
# plt.show()