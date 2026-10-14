from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


TEAM_NAME = "QueueWise"
WAIT_THRESHOLD = 60
MIN_DATES = 14
SNAPSHOT_START = pd.Timestamp("2022-06-20").date()

st.set_page_config(
    page_title=f"{TEAM_NAME} — Theme Park Queue Dashboard",
    layout="wide",
)


@st.cache_data
def load_data():
    path = Path(__file__).parent / "data" / "park_queue_snapshot.csv"

    return pd.read_csv(
        path,
        parse_dates=["date", "interval_start"],
    )


# Title, audience, decision and data freshness.
st.title(f"{TEAM_NAME} — Theme Park Queue Operations")

st.caption(
    "For the PortAventura World operations manager: "
    "prioritize attraction checks and identify recurring high-wait periods."
)

try:
    data = load_data()
except FileNotFoundError:
    st.error("Place park_queue_snapshot.csv in the data folder.")
    st.stop()

if data.empty:
    st.error("The data file contains no records.")
    st.stop()

first_record = data["date"].min().date()
last_record = data["date"].max().date()

st.caption(
    f"Data: {first_record:%d %b %Y}–{last_record:%d %b %Y}, "
    "Kaggle snapshot. Intended production refresh: nightly; "
    "management review: weekly."
)


# Date filter affects both KPIs and both charts.
st.sidebar.header("Analysis filters")

date_range = st.sidebar.date_input(
    "Analysis period",
    value=(SNAPSHOT_START, last_record),
    min_value=SNAPSHOT_START,
    max_value=last_record,
)

st.sidebar.caption(
    "60 minutes is a classroom review threshold, "
    "not an official park service standard."
)

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Select both a start date and an end date.")
    st.stop()

start_date, end_date = date_range

if start_date > end_date:
    st.info("The start date must be on or before the end date.")
    st.stop()

st.caption(
    f"Selected analysis period: {start_date:%d %b %Y} "
    f"to {end_date:%d %b %Y}. "
    "The date filter applies to both KPIs and both charts."
)

filtered = data.loc[
    data["date"].between(
        pd.Timestamp(start_date),
        pd.Timestamp(end_date),
    )
].copy()

if filtered.empty:
    st.info(
        "No retained operating records in this period. "
        "Missing records are not treated as zero wait."
    )
    st.stop()

filtered["above_threshold"] = (
    filtered["wait_minutes"].gt(WAIT_THRESHOLD)
)


# Headline metrics: park overview.
st.subheader("Park overview")

col1, col2 = st.columns(2)

col1.metric(
    "Median interval maximum wait",
    f"{filtered['wait_minutes'].median():.0f} min",
    help=(
        "Median of the maximum waiting times recorded within "
        "15-minute operating intervals. "
        "This is not the median wait of individual visitors."
    ),
)

col2.metric(
    "Operating records above 60 min",
    f"{filtered['above_threshold'].mean() * 100:.2f}%",
    help=(
        "Percentage of valid operating records whose interval "
        "maximum wait is strictly greater than 60 minutes."
    ),
)

calendar_days = (end_date - start_date).days + 1

st.caption(
    f"{len(filtered):,} valid records across "
    f"{filtered['attraction'].nunique()} attractions. "
    f"Records occur on {filtered['date'].nunique()} of "
    f"{calendar_days} selected calendar dates. "
    "Missing dates are not treated as zero wait."
)


# Chart 1: prioritize facilities for closer inspection.
summary = (
    filtered.groupby("attraction")
    .agg(
        records=("wait_minutes", "size"),
        observed_dates=("date", "nunique"),
        above_count=("above_threshold", "sum"),
    )
)

summary["above_pct"] = (
    summary["above_count"] / summary["records"] * 100
)

eligible = (
    summary.loc[summary["observed_dates"].ge(MIN_DATES)]
    .sort_values("above_pct", ascending=False)
)

st.subheader("1. Attractions to inspect first")

if eligible.empty:
    st.info(
        "No attraction has at least 14 observed dates in this period. "
        "Choose a longer period to show the ranking."
    )
else:
    top5 = eligible.head(5).sort_values("above_pct")

    fig, ax = plt.subplots(figsize=(9, 2.5))

    top5["above_pct"].plot.barh(
        ax=ax,
        color="steelblue",
    )

    ax.bar_label(
        ax.containers[0],
        fmt="%.1f%%",
        padding=4,
    )

    ax.set(
        xlabel="Share of operating records above 60 minutes (%)",
        ylabel="",
        xlim=(0, 110),
    )
    ax.set_xticks([0, 20, 40, 60, 80, 100])

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "Top 5 by high-wait share; each has at least 14 observed dates. "
        "Different operating hours and date coverage may affect comparisons."
    )


# Facility selection affects only the detail chart.
st.subheader("2. High-wait periods for the selected attraction")

options = summary.sort_values(
    "above_pct", ascending=False
).index.tolist()

selected_attraction = st.selectbox(
    "Attraction detail — park overview remains unchanged",
    options,
)

detail = filtered.loc[
    filtered["attraction"].eq(selected_attraction)
].copy()

detail["weekday"] = detail["date"].dt.weekday
detail["hour"] = detail["interval_start"].dt.hour

slots = (
    detail.groupby(["weekday", "hour"])
    .agg(
        records=("wait_minutes", "size"),
        observed_dates=("date", "nunique"),
        above_count=("above_threshold", "sum"),
    )
    .reset_index()
)

slots["above_pct"] = (
    slots["above_count"] / slots["records"] * 100
)

slots["plot_pct"] = slots["above_pct"].where(
    slots["observed_dates"].ge(4)
    & slots["records"].ge(16)
)

# Show the observed hour range, preserving missing cells within it.
display_hours = range(
    int(detail["hour"].min()),
    int(detail["hour"].max()) + 1,
)

heatmap = (
    slots.pivot(
        index="weekday",
        columns="hour",
        values="plot_pct",
    )
    .reindex(index=range(7), columns=display_hours)
)

if heatmap.isna().all().all():
    st.info(
        "Insufficient coverage for this heatmap. "
        "Choose a longer period or another attraction."
    )
else:
    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("lightgray")

    fig, ax = plt.subplots(figsize=(11, 3.5))

    im = ax.imshow(
        heatmap.to_numpy(),
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=100,
    )

    ax.set_xticks(range(len(heatmap.columns)))
    ax.set_xticklabels(heatmap.columns)

    ax.set_yticks(range(7))
    ax.set_yticklabels(
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )

    ax.set(
        title=selected_attraction,
        xlabel="Hour of interval start",
        ylabel="",
    )

    fig.colorbar(
        im,
        ax=ax,
        label="Records above 60 minutes (%)",
    )

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "Gray: no data, fewer than 4 observed dates, "
        "or fewer than 16 records in the weekday-hour cell. "
        "Only the selected attraction's observed hour range is shown."
    )

st.caption(
    f"Selected attraction coverage: {len(detail):,} records "
    f"on {detail['date'].nunique()} dates."
)


# Supporting definitions remain available without crowding the page.
with st.expander("Definitions and data limitations"):
    st.write(
        "Each row represents one attraction's 15-minute interval. "
        "Wait time is the maximum within that interval, "
        "not an individual visitor's wait. "
        "High-wait share counts records strictly above 60 minutes."
    )

    st.write(
        "The export window is 20 June–14 August 2022. "
        "Retained records start on 21 June; 20 June has no retained records. "
        "Missing dates and hours are not filled with zero."
    )

    st.write(
        "Zero opening-time records and invalid operating records "
        "were excluded before export. Valid zero waits were retained. "
        "The 14-date ranking rule and the heatmap coverage rules "
        "are classroom design assumptions."
    )

    st.write(
        "Long waits identify where further investigation is needed. "
        "They do not establish whether the cause is demand, "
        "staffing, available capacity or downtime."
    )

    st.write(
        "The Kaggle title refers to Disneyland, but the supplied "
        "mapping identifies PortAventura World and Tivoli Gardens. "
        "The original provenance and real/synthetic status remain unverified."
    )

    st.markdown(
        "[Kaggle dataset]"
        "(https://www.kaggle.com/datasets/ayushtankha/hackathon)"
    )