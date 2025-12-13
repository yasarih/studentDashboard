import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np

st.set_page_config(page_title="Student Dashboard", page_icon="🎓", layout="wide")

# ---------------------------------------------------
# 1️⃣ Load Google Credentials
# ---------------------------------------------------
@st.cache_data(show_spinner=False)
def load_credentials():
    try:
        return dict(st.secrets["gcp_service_account"])
    except KeyError:
        st.error("❌ Google credentials not found in Streamlit secrets.")
        return None


# ---------------------------------------------------
# 2️⃣ Fetch Data From Google Sheets
# ---------------------------------------------------
@st.cache_data(show_spinner=True)
def fetch_data(sheet_id, worksheet):
    creds_info = load_credentials()
    if not creds_info:
        return pd.DataFrame()

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        ws = client.open_by_key(sheet_id).worksheet(worksheet)
        data = ws.get_all_values()

        if not data:
            return pd.DataFrame()

        # Process headers safely
        headers = pd.Series(data[0]).fillna("").astype(str).str.strip()
        headers = headers.where(headers != "", other="Unnamed")
        headers = headers + headers.groupby(headers).cumcount().astype(str).replace("0", "")

        df = pd.DataFrame(data[1:], columns=headers)

        df.columns = df.columns.str.strip()
        df.replace("", np.nan, inplace=True)
        df.fillna("", inplace=True)

        # Convert Hr column if exists
        if "Hr" in df.columns:
            df["Hr"] = pd.to_numeric(df["Hr"], errors="coerce").fillna(0)

        return df

    except Exception as e:
        st.error(f"❌ Error loading sheet: {e}")
        return pd.DataFrame()


# ---------------------------------------------------
# 3️⃣ MAIN APP
# ---------------------------------------------------
def main():

    st.title("🎓 Angle Belearn - Student Login Portal")

    # 🔄 Refresh Button (Top Right)
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    sheet_id = "1BdCAPDmW601t2jcAMc-N4vMm3nqSWrm64bFoD7jZQtY"
    class_df = fetch_data(sheet_id, "Student class details")

    # ---------------- LOGIN -----------------
    student_id_input = st.text_input("Enter your Student ID")
    student_name_input = st.text_input("Enter any 4 letters from your Name")

    if st.button("Login"):

        if class_df.empty:
            st.error("❌ Student data not loaded.")
            return

        df = class_df.copy()

        # Normalize columns
        df["Student ID"] = df["Student ID"].astype(str).str.lower().str.strip()
        df["Student"] = df["Student"].astype(str).str.lower().str.strip()

        sid = student_id_input.lower().strip()
        sname = student_name_input.lower().strip()

        if len(sname) < 4:
            st.warning("⚠️ Please enter at least 4 letters from your name.")
            return

        match = df[df["Student ID"] == sid]

        if match.empty:
            st.error("❌ Student ID not found")
            return

        student_row = match.iloc[0]
        name_in_sheet = student_row["Student"]

        if sname not in name_in_sheet:
            st.error("❌ Name mismatch. Enter correct 4 letters from your name.")
            return

        # SUCCESS
        st.success("✅ Login Successful")
        st.session_state.student_id = sid
        st.session_state.student_profile = student_row.to_dict()
        st.rerun()

    # ---------------------------------------------------
    # After Login — Dashboard
    # ---------------------------------------------------
    if "student_id" in st.session_state:

        st.header(
            f"🧑‍🎓 Welcome {st.session_state.student_profile.get('Student', '').title()}"
        )

        tab1, tab2, tab3 = st.tabs(["Profile", "Class Log", "Summary"])

        # ------------------ PROFILE ------------------
        with tab1:
            st.subheader("👤 Student Profile")
            st.write("Will update soon...")

        # ------------------ CLASS LOG ------------------
        with tab2:
            st.subheader("📖 Daily Class Log")

            log_df = class_df.copy()
            log_df["Student ID"] = log_df["Student ID"].astype(str).str.lower()

            student_log = log_df[
                log_df["Student ID"] == st.session_state.student_id
            ]

            if student_log.empty:
                st.info("No class log found.")
            else:
                columns_to_show = [
                    "Date", "Student ID", "Student",
                    "Hr", "Teacher", "Subject"
                ]
                available_cols = [
                    col for col in columns_to_show if col in student_log.columns
                ]

                st.dataframe(
                    student_log[available_cols],
                    use_container_width=True
                )

        # ------------------ SUMMARY ------------------
        with tab3:
            st.subheader("⏱️ Class Hours Summary")
            st.write("Will update soon...")


if __name__ == "__main__":
    main()
