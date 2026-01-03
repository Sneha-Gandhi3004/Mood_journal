import streamlit as st
import plotly.express as px
import pandas as pd
import os
import re
from datetime import date


st.set_page_config(
    page_title="Daily Mood Journal",
    layout="wide"
)

st.title("🌿 Daily Mood Journal")
st.caption("A calm space to reflect on your day and notice emotional patterns over time.")


DATA_FILE = "mood_data.csv"


if "mood_data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.mood_data = pd.read_csv(DATA_FILE, parse_dates=["Date"])
    else:
        st.session_state.mood_data = pd.DataFrame(
            columns=["Date", "Positivity", "Stress", "Energy", "Description"]
        )


st.sidebar.header("📝 Log Today")

with st.sidebar.form("mood_form"):
    entry_date = st.date_input("Date", value=date.today())

    positivity = st.slider(
        "Positivity (-5 = very low, +5 = very positive)",
        -5, 5, 0
    )

    stress = st.slider(
        "Stress (0 = calm, 10 = extremely stressed)",
        0, 10, 5
    )

    energy = st.slider(
        "Energy (0 = exhausted, 10 = full of energy)",
        0, 10, 5
    )

    description = st.text_area(
        "What happened today? (Optional)",
        placeholder="Example: Had a tough meeting but felt better later."
    )

    submitted = st.form_submit_button("Save Entry")


if submitted:
    df = st.session_state.mood_data

    # Ensure one entry per date
    df = df[df["Date"] != pd.to_datetime(entry_date)]

    new_entry = pd.DataFrame([{
        "Date": entry_date,
        "Positivity": positivity,
        "Stress": stress,
        "Energy": energy,
        "Description": description
    }])

    df = pd.concat([df, new_entry], ignore_index=True)
    df = df.sort_values("Date")

    st.session_state.mood_data = df
    df.to_csv(DATA_FILE, index=False)

    st.success("Your entry has been saved 🌱")


df = st.session_state.mood_data

if df.empty:
    st.info("No entries yet. Log your first day from the left panel.")
    st.stop()


df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date")

# Normalize values to common emotional scale (-5 to +5)
df["Stress_norm"] = df["Stress"] - 5
df["Energy_norm"] = df["Energy"] - 5


df["Mood_Index"] = (
    df["Positivity"]
    + df["Energy_norm"]
    - df["Stress_norm"]
)


st.subheader("🌊 Overall Mood Over Time")

fig = px.area(
    df,
    x="Date",
    y="Mood_Index",
    markers=True,
    title="Mood Index"
)

fig.update_xaxes(
    type="date",
    tickformat="%b %d",
    rangeslider_visible=True
)

fig.update_yaxes(
    title="Mood Level"
)

fig.add_hline(
    y=0,
    line_dash="dash",
    line_color="gray",
    annotation_text="Neutral"
)

fig.update_traces(
    fillcolor="rgba(120, 180, 160, 0.4)",
    line_color="green"
)

st.plotly_chart(fig, use_container_width=True)


latest = round(df["Mood_Index"].iloc[-1], 1)

if len(df) > 1:
    delta = round(latest - df["Mood_Index"].iloc[-2], 1)
else:
    delta = None

st.metric(
    label="Latest Mood Index",
    value=latest,
    delta=delta
)


st.subheader("💬 Reflection")

latest_desc = str(df.iloc[-1]["Description"]).lower().strip()
latest_desc = re.sub(r"[^\w\s]", "", latest_desc)

positive_words = ["happy", "good", "great", "calm", "relieved", "productive"]
negative_words = ["sad", "tired", "angry", "stress", "stressed", "anxious", "bad"]
negations = ["not", "no", "never"]

score = 0
words = latest_desc.split()

for i, word in enumerate(words):
    context = words[max(0, i - 3):i]
    negated = any(n in context for n in negations)

    if word in positive_words:
        score += -1 if negated else 1
    elif word in negative_words:
        score += 1 if negated else -1

if not latest_desc:
    st.info("You didn’t write anything today — that’s completely okay.")
elif score > 0:
    st.success(
        "Your entry includes **some positive moments** 🌱\n\n"
        "Noticing these moments matters."
    )
elif score < 0:
    st.warning(
        "Your entry includes **some challenging moments** 💛\n\n"
        "Reflecting is already a healthy step."
    )
else:
    st.info(
        "Your day feels **mixed or neutral** ⚖️\n\n"
        "That’s a very normal experience."
    )


with st.expander("📖 View latest journal entry"):
    st.write(df.iloc[-1]["Description"] or "No description added.")

st.caption(
    "🫶 This journal is for awareness, not judgment. Showing up is enough."
)
