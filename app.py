import streamlit as st
import urllib.parse
import pandas as pd

st.set_page_config(page_title="Executive Sourcing Portal", layout="wide")

st.title("⚡ Executive Sourcing Portal")
st.write("Fast-track your executive sourcing across target companies.")

# Inputs
col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("Company Name (e.g., Spotify, Volvo, IKEA):", "")
with col2:
    company_domain = st.text_input("Company Domain (e.g., spotify.com, volvocars.com):", "")

# Key Sourcing Targets
ROLES = [
    ("CEO / Managing Director", '("CEO" OR "Chief Executive Officer" OR "Managing Director")'),
    ("Design Director / VP", '("Design Director" OR "Head of Design" OR "VP of Design")'),
    ("UX Director / VP", '("UX Director" OR "Head of UX" OR "Director of UX")'),
    ("Product Design Director", '("Product Design Director" OR "Head of Product Design")'),
    ("Head of HR / Chief People Officer", '("Head of HR" OR "Chief People Officer" OR "VP HR")')
]

if st.button("Generate Executive Contacts & Links"):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        clean_company = company_name.strip()
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip() if company_domain else f"{clean_company.lower().replace(' ', '')}.com"

        st.subheader(f"1. Key Decision-Makers for **{clean_company}**")

        results = []
        for role_title, keywords in ROLES:
            # Google X-Ray Search Link
            google_q = f'site:linkedin.com/in/ {keywords} AND "{clean_company}"'
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(google_q)}"

            # LinkedIn Direct Link
            linkedin_q = f'{keywords} AND "{clean_company}"'
            linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(linkedin_q)}"

            # Public Email Search Link
            email_q = f'"{clean_company}" {keywords} "@{domain}"'
            email_url = f"https://www.google.com/search?q={urllib.parse.quote(email_q)}"

            results.append({
                "Target Role": role_title,
                "LinkedIn Direct Search": linkedin_url,
                "Google Profile X-Ray": google_url,
                "Extract Web Emails": email_url
            })

        df = pd.DataFrame(results)

        st.dataframe(
            df,
            column_config={
                "LinkedIn Direct Search": st.column_config.LinkColumn("Open LinkedIn"),
                "Google Profile X-Ray": st.column_config.LinkColumn("Open Google Profiles"),
                "Extract Web Emails": st.column_config.LinkColumn("Search Indexed Emails")
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader(f"2. Email Formula Builder (`@{domain}`)")
        st.write("Once you tap a profile link above and grab an executive's name, use these exact patterns:")

        patterns = [
            {"Pattern": "First . Last", "Example Email": f"first.last@{domain}"},
            {"Pattern": "First Initial + Last", "Example Email": f"f.last@{domain} or flast@{domain}"},
            {"Pattern": "First Name Only", "Example Email": f"first@{domain}"},
            {"Pattern": "First + Last Initial", "Example Email": f"firstl@{domain}"}
        ]

        st.table(pd.DataFrame(patterns))
