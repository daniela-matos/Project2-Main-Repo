# Dependencies 
import pandas as pd 
import requests 
from sqlalchemy import create_engine
import datetime

from mySQLCredentials import *

# Covid-19 Confirmed Cases
confirmed_url = "https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
confirmed_html = requests.get(confirmed_url).text 
confirmed_df = pd.read_html(confirmed_html)[0]
confirmed_df = confirmed_df.iloc[:, 1:]
confirmed_df = confirmed_df.melt(id_vars=['Country/Region', 'Province/State', 'Lat', 'Long'])
confirmed_df = confirmed_df.rename(columns={"Country/Region": "country_region", "Province/State": "province_state",  "Lat": "lat", "Long": "long", "variable":"date", "value": "confirmed"})

# Covid-19 Deaths
deaths_url = "https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
deaths_html = requests.get(deaths_url).text 
deaths_df = pd.read_html(deaths_html)[0]
deaths_df = deaths_df.iloc[:, 1:]
deaths_df = deaths_df.melt(id_vars=['Country/Region', 'Province/State', 'Lat', 'Long'])
deaths_df = deaths_df.rename(columns={"Country/Region": "country_region", "Province/State": "province_state", "Lat": "lat", "Long": "long", "variable":"date", "value": "deaths"})

# Covid-19 Recovered
recovered_url = "https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"
recovered_html = requests.get(recovered_url).text 
recovered_df = pd.read_html(recovered_html)[0]
recovered_df = recovered_df.iloc[:, 1:]
recovered_df = recovered_df.melt(id_vars=['Country/Region', 'Province/State', 'Lat', 'Long'])
recovered_df = recovered_df.rename(columns={"Country/Region": "country_region", "Province/State": "province_state", "Lat": "lat", "Long": "long", "variable":"date", "value": "recovered"})

# Merge three dataframes
covid_merge1 = pd.merge(confirmed_df, deaths_df, how="outer")
covid_merge2 = pd.merge(covid_merge1, recovered_df, how="outer")

# Transform "Date" column into datatime format
covid_merge2["date"] = pd.to_datetime(covid_merge2["date"])
covid_merge2["date"] = covid_merge2["date"].dt.date

### Add column ISO3 to "covid_df"
# iso_url = "https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv"
# iso_html = requests.get(iso_url).text
# iso_df = pd.read_html(iso_html)[0]
# iso3_df = iso_df[["iso3", "Country_Region"]].rename(columns={"Country_Region": "country_region"})[:173]
# new_rows_df = pd.DataFrame({"iso3": ["AUS", "CAN", "CHN", "USA"], "country_region": ["Australia", "Canada", "China", "US"]})
# iso3_df = iso3_df.append(new_rows_df, ignore_index=True)

iso3_df = pd.read_csv("iso3.csv", index_col=0)
covid_df = pd.merge(covid_merge2, iso3_df, how="left")

# Create a customized dataframe for Sinah's plots
old_pop_df = pd.read_csv("older_pop_2018.csv")
covid_df2 = covid_df[["country_region", "date", "province_state", "confirmed", "deaths", "recovered"]]
covid_df2 = covid_df2.groupby(["country_region", "date"]).sum().reset_index()
covid_df2["case_fatality"] = round(covid_df2["deaths"] / covid_df2["confirmed"] * 100, 2)
covid_df3 = pd.merge(covid_df2, iso3_df, how="left")
plot_df = pd.merge(covid_df3, old_pop_df, how="left")
plot_df = plot_df.loc[plot_df["date"] >= datetime.date(2020,3,1)].reset_index().drop("index", axis=1)

# Connect to the "Covid" database in MySQL (CHANGE PASSWORD)
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = mySQLUsername
PASSWORD = mySQLPassword
DIALECT = "mysql"
DRIVER = "pymysql"
DATABASE = "Covid"
TABLE_WORLD_TIMESERIES = "world_timeseries"

connection_string = ( f"{DIALECT}+{DRIVER}://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}" )
engine = create_engine(connection_string)

# Create "daily_cases" table in "Covid" database with "covid_db" dataframe
covid_df.to_sql(con=engine, name="daily_cases", if_exists="replace")
plot_df.to_sql(con=engine, name="plotting", if_exists="replace")

# CREATE [OR REPLACE] [TEMPORARY] TABLE [IF NOT EXISTS] tbl_name
engine.execute(f"DROP TABLE IF EXISTS {TABLE_WORLD_TIMESERIES}")

engine.execute(
    "CREATE table world_timeseries (id INT NOT NULL auto_increment, date datetime, total_confirmed bigint(20), total_deaths bigint(20), total_recovered bigint(20), primary key (id)) SELECT date, SUM(confirmed) as total_confirmed, SUM(deaths) as total_deaths, SUM(recovered) as total_recovered FROM Covid.daily_cases GROUP BY date"
    )



