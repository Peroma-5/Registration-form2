import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(page_title="Event Registration", page_icon="📋", layout="centered")

DATA_FILE = "registrations.csv"


def get_secret(key, default=""):
    """Checks environment variables first (for Render/hosted deploys),
    then falls back to .streamlit/secrets.toml (for local runs)."""
    if key in os.environ:
        return os.environ[key]
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

# ----------------------------------------------------------------------
# HEADER / EVENT DESCRIPTION
# ----------------------------------------------------------------------
st.title("📋 Online Tutoring Registration")
st.markdown("### Design of RC Building — Using PROTA Structure Software (Code: BS 8110)")
st.info(
    "**Professional Training: Design of RC Building**\n\n"
    "📅 Dates: 26–31 August 2026  |  🕗 Time: 20:00 – 21:30 (EAT)  |  💻 Venue: Online\n\n"
    "Facilitators: Eng. Mahumanga & Eng. Icheki\n\n"
    "You will learn: Introduction to RC Design, Building Modeling, Loading & Load Combination, "
    "Analysis & Design, and Detailing & Reporting.\n\n"
    "💰 Fees: Students — TZS 75,000  |  Others — TZS 100,000"
)

st.divider()

# ----------------------------------------------------------------------
# LOAD EXISTING REGISTRATIONS (so the counter/table persists across visits)
# ----------------------------------------------------------------------
if os.path.exists(DATA_FILE):
    existing = pd.read_csv(DATA_FILE)
else:
    existing = pd.DataFrame(columns=[
        "Timestamp", "First Name", "Middle Name", "Last Name",
        "Phone Number", "Occupation", "Fee (TZS)", "Payment Status", "Transaction ID",
    ])

# ----------------------------------------------------------------------
# REGISTRATION FORM
# ----------------------------------------------------------------------
st.subheader("Register")

with st.form("registration_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        first_name = st.text_input("First Name")
    with col2:
        middle_name = st.text_input("Middle Name")
    with col3:
        last_name = st.text_input("Last Name")

    occupation = st.radio("Occupation", ["Student", "Other"], horizontal=True)
    occupation_other = ""
    if occupation == "Other":
        occupation_other = st.text_input("Please specify")

    phone_number = st.text_input("Phone Number (used to confirm your payment later)")

    submitted = st.form_submit_button("Save", type="primary", use_container_width=True)

    if submitted:
        if not first_name or not last_name:
            st.error("Please enter at least your first and last name.")
        elif not phone_number.strip():
            st.error("Please enter your phone number — it's used to match your payment afterward.")
        else:
            final_occupation = occupation_other.strip() if occupation == "Other" and occupation_other.strip() else occupation
            fee_amount = 75000 if occupation == "Student" else 100000

            new_row = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "First Name": first_name.strip(),
                "Middle Name": middle_name.strip(),
                "Last Name": last_name.strip(),
                "Phone Number": phone_number.strip(),
                "Occupation": final_occupation,
                "Fee (TZS)": fee_amount,
                "Payment Status": "Pending",
                "Transaction ID": "",
            }])

            updated = pd.concat([existing, new_row], ignore_index=True)
            updated.to_csv(DATA_FILE, index=False)

            st.success("✅ Your submission is successful! You are registered for the tutoring sessions.")
            fee = f"TZS {fee_amount:,}"
            st.info(
                f"📌 Your fee: **{fee}**\n\n"
                "**Payment Details:**\n"
                "Account No: 0152564153000\n"
                "M-Pesa: +255 754 414 723\n"
                "Name: Emmanuel Mahumanga\n\n"
                "For questions, contact: +255 754 414 723\n\n"
                "After paying, scroll down to **Confirm Your Payment** and enter your phone number "
                "and M-Pesa transaction ID so it's logged against your registration.\n\n"
                "Thank you for registering — see you in the sessions!"
            )

st.divider()

# ----------------------------------------------------------------------
# CONFIRM PAYMENT (participant returns after paying to log their transaction)
# ----------------------------------------------------------------------
st.subheader("💳 Confirm Your Payment")
st.caption("Already registered and paid? Enter your details below to mark your payment as received.")

with st.form("payment_form", clear_on_submit=True):
    pay_phone = st.text_input("Phone Number (same one used to register)")
    txn_id = st.text_input("M-Pesa Transaction ID")
    pay_submitted = st.form_submit_button("Confirm Payment", use_container_width=True)

    if pay_submitted:
        if not pay_phone.strip() or not txn_id.strip():
            st.error("Please enter both your phone number and transaction ID.")
        else:
            current = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame()
            matches = current.index[current["Phone Number"].astype(str) == pay_phone.strip()].tolist()
            if not matches:
                st.error("No registration found with that phone number. Please register first.")
            else:
                row_idx = matches[-1]  # most recent matching registration
                current.loc[row_idx, "Payment Status"] = "Paid"
                current.loc[row_idx, "Transaction ID"] = txn_id.strip()
                current.to_csv(DATA_FILE, index=False)
                st.success("✅ Payment confirmed and logged. Thank you!")

st.divider()

# ----------------------------------------------------------------------
# LIVE REGISTRATION COUNT (visible to participants; remove if you'd rather keep it private)
# ----------------------------------------------------------------------
current_count = len(pd.read_csv(DATA_FILE)) if os.path.exists(DATA_FILE) else 0
st.caption(f"👥 {current_count} participant(s) registered so far.")

st.divider()

# ----------------------------------------------------------------------
# ADMIN VIEW (password protected — for the organizer to see who has paid)
# ----------------------------------------------------------------------
with st.expander("🔒 Organizer View"):
    admin_password = st.text_input("Admin password", type="password", key="admin_pw")
    if admin_password:
        if admin_password == get_secret("ADMIN_PASSWORD", ""):
            admin_data = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame()
            if admin_data.empty:
                st.write("No registrations yet.")
            else:
                paid_count = (admin_data["Payment Status"] == "Paid").sum()
                pending_count = (admin_data["Payment Status"] == "Pending").sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Registered", len(admin_data))
                c2.metric("Paid", int(paid_count))
                c3.metric("Pending", int(pending_count))
                st.dataframe(admin_data, use_container_width=True)
                st.download_button(
                    "Download full registration list (CSV)",
                    data=admin_data.to_csv(index=False).encode("utf-8"),
                    file_name="registrations_export.csv",
                    mime="text/csv",
                )
        else:
            st.error("Incorrect admin password.")
