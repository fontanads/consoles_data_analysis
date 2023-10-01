# streamlit application for the dashboard
import streamlit as st
import pandas as pd
import altair as alt
import os

# constants
nintendo_groups = ["Gamecube", "DS", "Wii", "2DS/3DS", "Wii U", "Switch"]
nintendo_products = ['Gamecube', 'DS', 'DSi', 'DSi XL', 'DS Lite', 'Wii', 'Wii U', 'New 2DS XL', 'New 3DS', 'New 3DS XL', '2DS', '3DS', '3DS XL', 'Switch', 'Switch Lite', 'Switch – OLED Model']
playstation_groups = ["PS4", "PS5"]
playstation_products = ['PS4', 'PS5']
group_console_order = ["Gamecube", "DS", "Wii", "2DS/3DS", "Wii U", "Switch", "PS4", "PS5"]
product_console_order = ['Gamecube', 'DS', 'DSi', 'DSi XL', 'DS Lite', 'Wii', 'Wii U', 'New 2DS XL', 'New 3DS', 'New 3DS XL', '2DS', '3DS', '3DS XL', 'PS4', 'Switch', 'Switch Lite', 'Switch – OLED Model', 'PS5']
min_values_in_millions = 0.001

# settings
st.set_page_config(page_title="Video Game Sales Dashboard", layout="wide")


# method to read data
@st.cache_data
def read_data(path):
    df = pd.read_csv(path)
    return df


# load hardware sales
def load_hardware_sales():
    # get path of file
    this_file_path = os.path.sep.join(os.path.abspath(__file__).split(os.path.sep)[:-1])
    processed_data_path = os.path.join(this_file_path, "..", "data", "processed")
    hardware_files = [f for f in os.listdir(processed_data_path) if "hardware" in f]
    hardware_dfs = []
    for file in hardware_files:
        df = read_data(os.path.join(processed_data_path, file))
        hardware_dfs.append(df)
    df_hardware = pd.concat(hardware_dfs)
    df_hardware = df_hardware[df_hardware["Qty"] >= min_values_in_millions]
    return df_hardware


# method to aggregate data by ["Group", "Date"] columns
def aggregate_data(df):
    df = df.groupby(["Group", "Date"]).sum().reset_index()
    return df


# method to replace Date column by dense-ranked version over groups
def replace_date_by_dense_ranked(df):
    df["Date"] = df.groupby("Group")["Date"].rank("dense")
    return df


# absolute values of sales over time
def plot_absolute_sales_over_time(
        df,
        fy_totals: pd.DataFrame = pd.DataFrame(),
        grouping_field="Group",
        ranked_dates=True,
        title=None,
        width=500,
        height=500,
        opacity_max=1.,
        opacity_min=0.2,
        point_size=50,
        point_shape="square"):

    # create order list for color encoding
    console_order = group_console_order if grouping_field == "Group" else product_console_order

    # bind selection to legend
    selection = alt.selection_point(fields=[grouping_field], bind='legend')

    # prepare encodings
    opacity = alt.condition(selection, alt.value(opacity_max), alt.value(opacity_min))
    x_encoding = alt.X("Date:Q", title="Ranked Date") if ranked_dates else alt.X("Date:T", title="Date")
    y_encoding = alt.Y("Qty:Q", title=["Units Sold", "(Millions)"])
    color_encoding = alt.Color(f"{grouping_field}:N", title=grouping_field).sort(console_order)
    tooltip_encoding = [grouping_field, "Date", "Qty"]

    # group curves
    chart = alt.Chart(df).mark_line(point={"shape": point_shape, "size": point_size})\
        .encode(
            x=x_encoding,
            y=y_encoding,
            color=color_encoding,
            opacity=opacity,
            tooltip=tooltip_encoding,
            strokeWidth=alt.value(3))
    chart = chart.add_params(selection)

    if not (ranked_dates or fy_totals.empty):
        # total sales curve
        fiscal_year_totals_chart = alt.Chart(fy_totals)\
            .mark_line(color='black', strokeDash=[5, 5], point={"shape": point_shape, "size": point_size, "color": "black"})\
            .encode(x=x_encoding, y=y_encoding)
        chart += fiscal_year_totals_chart

    chart = chart.properties(
        title=title,
        width=width,
        height=height
    ).interactive()
    return chart


# tab_1: absolute values of sales over time
def tab_1(df_hardware_products, df_hardware_groups, fy_totals_product, fy_totals_group, ranked_dates, width=800, tab_title=None):

    st.title(tab_title)
    col1, col2 = st.columns(2)
    with col1:
        # plot absolute values over time
        chart = plot_absolute_sales_over_time(df_hardware_products, fy_totals_product, "Product", ranked_dates=ranked_dates, width=width, title="Product View")
        st.altair_chart(chart, use_container_width=True)

    with col2:
        # plot absolute values over time
        chart = plot_absolute_sales_over_time(df_hardware_groups, fy_totals_group, "Group", ranked_dates=ranked_dates, width=width, title="Group View")
        st.altair_chart(chart, use_container_width=True)


def process_data_using_parameters(df_hardware, df_hardware_group_agg, selected_products, selected_groups, ranked_dates):
    df_hardware_products = df_hardware[df_hardware["Product"].isin(selected_products)]
    df_hardware_groups = df_hardware_group_agg[df_hardware_group_agg["Group"].isin(selected_groups)]

    if ranked_dates:
        df_hardware_products = df_hardware_products[df_hardware_products["Qty"] >= min_values_in_millions]
        df_hardware_groups = df_hardware_groups[df_hardware_groups["Qty"] >= min_values_in_millions]
        df_hardware_products = replace_date_by_dense_ranked(df_hardware_products)
        df_hardware_groups = replace_date_by_dense_ranked(df_hardware_groups)

    fy_totals_product = df_hardware_products.groupby("Date")["Qty"].sum().reset_index()
    fy_totals_group = df_hardware_groups.groupby("Date")["Qty"].sum().reset_index()

    return (df_hardware_products, fy_totals_product), (df_hardware_groups, fy_totals_group)


if __name__ == "__main__":

    # load hardware sales
    df_hardware = load_hardware_sales()
    # aggregate data
    df_hardware_group_agg = aggregate_data(df_hardware.drop(columns=["Product"]).copy())

    # create sidebar
    st.sidebar.title("Video Game Sales Dashboard")
    st.sidebar.markdown("Select a product and a group to see the sales evolution over time.")

    # create a Nintendo and Playstation multiselect option
    selected_consoles = st.sidebar.multiselect("Console", ["Nintendo", "Playstation"], default=["Nintendo", "Playstation"])
    if "Nintendo" in selected_consoles:
        st.sidebar.markdown("Nintendo Consoles")
        nintendo_selected_products = st.sidebar.multiselect("Product", nintendo_products, default=nintendo_products)
        nintendo_selected_groups = st.sidebar.multiselect("Group", nintendo_groups, default=nintendo_groups)
    else:
        nintendo_selected_products = []
        nintendo_selected_groups = []

    if "Playstation" in selected_consoles:
        st.sidebar.markdown("Playstation Consoles")
        ps_selected_products = st.sidebar.multiselect("Product", playstation_products, default=playstation_products)
        ps_selected_groups = st.sidebar.multiselect("Group", playstation_groups, default=playstation_groups)
    else:
        ps_selected_products = []
        ps_selected_groups = []

    # create a multiselect option for products and groups
    selected_products = nintendo_selected_products + ps_selected_products
    selected_groups = nintendo_selected_groups + ps_selected_groups

    assert len(selected_products) > 0, "Please select at least one product"
    assert len(selected_groups) > 0, "Please select at least one group"

    # option to switch between regular dates and ranked dates
    ranked_dates = st.sidebar.checkbox("Use ranked dates", value=True)

    # process data
    (df_hardware_products, fy_totals_product), (df_hardware_groups, fy_totals_group) = process_data_using_parameters(df_hardware, df_hardware_group_agg, selected_products, selected_groups, ranked_dates=ranked_dates)

    tab_1(df_hardware_products, df_hardware_groups, fy_totals_product, fy_totals_group, ranked_dates, width=800, tab_title="Absolute Values")

    # create cumulative sales tab
    df_hardware_products_cumulative = df_hardware_products.groupby(["Product", "Date"])["Qty"].sum().groupby(level=[0]).cumsum().reset_index()
    df_hardware_groups_cumulative = df_hardware_groups.groupby(["Group", "Date"])["Qty"].sum().groupby(level=[0]).cumsum().reset_index()
    fy_totals_product_cumulative = fy_totals_product.copy().sort_values("Date")
    fy_totals_product_cumulative["Qty"] = fy_totals_product_cumulative["Qty"].cumsum()
    fy_totals_group_cumulative = fy_totals_group.copy().sort_values("Date")
    fy_totals_group_cumulative["Qty"] = fy_totals_group_cumulative["Qty"].cumsum()

    tab_1(df_hardware_products_cumulative, df_hardware_groups_cumulative, fy_totals_product_cumulative, fy_totals_group_cumulative, ranked_dates, width=800, tab_title="Cumulative Values")
