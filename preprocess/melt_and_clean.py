import pandas as pd
import os


def read_csv(path):
    df = pd.read_csv(path)
    return df


def clean_nintendo_qty_values(df):
    df.iloc[:, 3:] = df.iloc[:, 3:]\
        .fillna("0")\
        .astype("string")\
        .applymap(lambda x: x.strip())\
        .applymap(lambda x: x.replace(',', ''))\
        .applymap(lambda x: x.split(".")[0])\
        .astype(int)
    return df


def melt_nintendo_tables(df):
    index_cols = ["Product", "Group", "Geo"]
    df = df.melt(id_vars=index_cols, var_name="Date", value_name="Qty")
    return df


def clean_nintendo_dates(df):
    df["Date"] = df["Date"].str.replace("M", "")
    df["Date"] = pd.to_datetime(df['Date'].str.replace('FY3/', '') + '-03-31')
    return df


def change_nintendo_units_to_millions(df):
    df["Qty"] = df["Qty"] * (10_000 / int(1e6))  # ten thousands to millions of units
    return df


def clean_playstation_dates(df):
    df['Date'] = pd.to_datetime((df['Date'].str.replace('FY', '').astype(int) + 1).astype(str) + '-03-31')
    return df


def nintendo_pipeline(df):
    df = clean_nintendo_qty_values(df)
    df = melt_nintendo_tables(df)
    df = clean_nintendo_dates(df)
    df = change_nintendo_units_to_millions(df)
    return df


def playstation_pipeline(df):
    df = clean_playstation_dates(df)
    return df


if __name__ == "__main__":
    default_data_path = "data"
    nintendo_folder = "nintendo"
    playstation_folder = "playstation"
    output_folder = "processed"

    nintendo_path = os.path.join(default_data_path, nintendo_folder)
    playstation_path = os.path.join(default_data_path, playstation_folder)
    output_path = os.path.join(default_data_path, output_folder)

    nintendo_files = os.listdir(nintendo_path)
    playstation_files = os.listdir(playstation_path)

    # load nintendo data file by file
    nintendo_dfs = []
    for file in nintendo_files:
        df = read_csv(os.path.join(nintendo_path, file))
        df = nintendo_pipeline(df)
        df.to_csv(os.path.join(output_path, file), index=False)
        nintendo_dfs.append(df)
    df_nintendo = pd.concat(nintendo_dfs)
    df_nintendo_software = df_nintendo[df_nintendo["Product"] == "Software"]
    df_nintendo_hardware = df_nintendo[df_nintendo["Product"] != "Software"]

    df_nintendo_software_totals_by_date = df_nintendo_software.groupby(["Group", "Date"])["Qty"].sum().reset_index()
    df_nintendo_software_totals_by_date.to_csv(os.path.join(output_path, "nintendo_software_totals_by_date.csv"), index=False)

    df_nintendo_hardware_totals_by_date = df_nintendo_hardware.groupby(["Group", "Date"])["Qty"].sum().reset_index()
    df_nintendo_hardware_totals_by_date.to_csv(os.path.join(output_path, "nintendo_hardware_totals_by_date.csv"), index=False)
    print("Nintendo: done")

    # load playstation data
    df_playstation = pd.read_csv(os.path.join(playstation_path, playstation_files[0]))
    df_playstation = playstation_pipeline(df_playstation).rename(columns={"Product": "Group"})
    df_playstation.to_csv(os.path.join(output_path, "playstation_hardware_totals_by_date.csv"), index=False)
    print("Playstation: done")