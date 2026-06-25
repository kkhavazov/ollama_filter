
from datetime import datetime
import sqlite3

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_PATH = "data/emails.db"
TABLE_NAME = "emails"

st.set_page_config(
    page_title="Email Filter Dashboard",
    page_icon="📧",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)  # re-read the DB at most once a minute
def load_data(db_path: str) -> pd.DataFrame:
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
        conn.close()
    except Exception as e:
        st.error(f"Could not read database '{db_path}': {e}")
        return pd.DataFrame()

    if "is_customer_request" in df.columns:
        # SQLite stores BOOLEAN as 0/1 — make it readable
        df["is_customer_request"] = df["is_customer_request"].astype(bool)

    return df


df = load_data(DB_PATH)

# Manual refresh button (bypasses the cache)
col_title, col_refresh = st.columns([6, 1])
with col_title:
    st.title("📧 Email Filter Dashboard")
with col_refresh:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

if df.empty:
    st.warning(
        f"No data found in '{DB_PATH}'. Make sure the filtering script has "
        f"run at least once and the table '{TABLE_NAME}' exists."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")



urgencies = sorted(df["urgency"].dropna().unique().tolist())
selected_urgencies = st.sidebar.multiselect(
    "Urgency", options=urgencies, default=urgencies
)

customer_search = st.sidebar.text_input("Customer name contains")
subject_search = st.sidebar.text_input("Subject contains")
summary_search = st.sidebar.text_input("Summary contains")

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
filtered = df.copy()



if selected_urgencies:
    filtered = filtered[filtered["urgency"].isin(selected_urgencies)]

if customer_search:
    filtered = filtered[
        filtered["customer_name"].str.contains(customer_search, case=False, na=False)
    ]

if subject_search:
    filtered = filtered[
        filtered["subject"].str.contains(subject_search, case=False, na=False)
    ]

if summary_search:
    filtered = filtered[
        filtered["summary"].str.contains(summary_search, case=False, na=False)
    ]

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------
st.subheader("Overview")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total emails (filtered view)", len(filtered))
m2.metric("Total emails (all time)", len(df))
m3.metric("Customer requests (all time)", int(df["is_customer_request"].sum()))

if "urgency" in df.columns and not df["urgency"].dropna().empty:
    most_common_urgency = df["urgency"].value_counts().idxmax()
    m4.metric("Most common urgency", most_common_urgency)
else:
    m4.metric("Most common urgency", "n/a")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Emails by urgency**")
    if not filtered.empty:
        st.bar_chart(filtered["urgency"].value_counts())
    else:
        st.info("No data matches the current filters.")

with chart_col2:
    st.markdown("**Customer requests vs. other emails**")
    if not filtered.empty:
        request_counts = filtered["is_customer_request"].map(
            {True: "Customer request", False: "Other"}
        ).value_counts()
        st.bar_chart(request_counts)
    else:
        st.info("No data matches the current filters.")

# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------
st.subheader(f"Emails ({len(filtered)})")

display_cols = [
    c for c in
    ["id", "customer_name", "subject", "is_customer_request", "urgency", "summary"]
    if c in filtered.columns
]

st.dataframe(
    filtered[display_cols].sort_values(by="id", ascending=False),
    width='stretch',
    height=200,
)

# ---------------------------------------------------------------------------
# Detail view (includes full body, which we don't want crowding the table)
# ---------------------------------------------------------------------------
if not filtered.empty:
    st.subheader("Inspect a single email")
    selected_id = st.selectbox(
        "Select an email ID to view full details",
        options=filtered["id"].tolist(),
    )
    if selected_id is not None:
        row = filtered[filtered["id"] == selected_id].iloc[0]
        with st.expander("Details", expanded=True):
            st.write(f"**Subject:** {row['subject']}")
            st.write(f"**Customer:** {row['customer_name']}")
            st.write(f"**Customer request:** {'Yes' if row['is_customer_request'] else 'No'}")
            st.write(f"**Urgency:** {row['urgency']}")
            st.write(f"**Summary:** {row['summary']}")
            st.write("**Full body:**")
            st.text_area("Body", row["body"], height=200, label_visibility="collapsed")

# ---------------------------------------------------------------------------
# Download filtered results
# ---------------------------------------------------------------------------
st.download_button(
    label="Download filtered results as CSV",
    data=filtered[display_cols].to_csv(index=False),
    file_name=f"emails_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)