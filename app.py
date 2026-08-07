import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Executive Contact Extractor", layout="wide")

st.title("🏢 Executive Contact Extractor")
st.write("Extract names, exact designations, emails, and LinkedIn links into a structured table.")

# API Credentials
google_api_key = st.text_input("Google API Key:", type="password")
search_engine_id = st.text_input("Google Search Engine ID (CX):")

# Inputs
col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("Company Name (e.g., Spotify, Volvo, IKEA):")
with col2:
    company_domain = st.text_input("Company Domain (e.g., spotify.com, volvocars.com, ikea.com):")

ROLES = [
    ("CEO / Executive", '("CEO" OR "Chief Executive Officer" OR "Managing Director")'),
    ("Design Director", '("Design Director" OR "Head of Design" OR "VP of Design")'),
    ("UX Director", '("UX Director" OR "Head of UX" OR "Director of UX")'),
    ("Product Design Director", '("Product Design Director" OR "Head of Product Design")'),
    ("Head of HR / People", '("Head of HR" OR "Chief People Officer" OR "VP of HR")')
]

def parse_linkedin_title(raw_title):
    """Splits LinkedIn title format: 'John Doe - Chief Executive Officer - Spotify | LinkedIn'"""
    cleaned = raw_title.replace(" | LinkedIn", "").replace(" - LinkedIn", "").strip()
    
    # Common LinkedIn separator patterns
    parts = re.split(r' - | – | \| ', cleaned)
    
    if len(parts) >= 2:
        name = parts[0].strip()
        designation = parts[1].strip()
    elif len(parts) == 1:
        name = parts[0].strip()
        designation = "Executive"
    else:
        name = "Unknown"
        designation = "Unknown"
        
    return name, designation

def generate_email_pattern(name, domain):
    """Generates standard corporate email address (first.last@domain.com) from name."""
    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip().lower()
    name_parts = clean_name.split()
    
    if len(name_parts) >= 2:
        first = name_parts[0]
        last = name_parts[-1]
        return f"{first}.{last}@{domain}"
    elif len(name_parts) == 1:
        return f"{name_parts[0]}@{domain}"
    return f"info@{domain}"

if st.button("Extract Executive Contacts"):
    if not google_api_key or not search_engine_id:
        st.warning("Please enter your Google API Key and Search Engine ID.")
    elif not company_name or not company_domain:
        st.warning("Please enter both Company Name and Domain.")
    else:
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip()
        clean_company = company_name.strip()

        st.info(f"Extracting executive contacts for **{clean_company}**...")

        extracted_data = []

        for category, role_query in ROLES:
            query = f'site:linkedin.com/in/ "{clean_company}" {role_query}'
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={google_api_key.strip()}&cx={search_engine_id.strip()}"

            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])

                    for item in items:
                        raw_title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        link = item.get("link", "")

                        # Parse name and job designation
                        name, designation = parse_linkedin_title(raw_title)

                        # Look for raw emails in web snippet
                        email_pattern = rf'[a-zA-Z0-9._%+-]+@{re.escape(domain)}'
                        emails_found = re.findall(email_pattern, snippet, re.IGNORECASE)

                        if emails_found:
                            email = emails_found[0].lower()
                            email_status = "Verified Public"
                        else:
                            email = generate_email_pattern(name, domain)
                            email_status = "Pattern Match"

                        extracted_data.append({
                            "Category": category,
                            "Full Name": name,
                            "Designation": designation,
                            "Email Address": email,
                            "Email Type": email_status,
                            "LinkedIn Profile": link
                        })
                else:
                    st.error(f"API Error {res.status_code}: {res.text}")
                    break
            except Exception as e:
                st.error(f"Error fetching data: {e}")

        if extracted_data:
            st.success(f"Successfully extracted {len(extracted_data)} executive record(s)!")
            df = pd.DataFrame(extracted_data)

            # Display clean result table
            st.dataframe(
                df[["Full Name", "Designation", "Email Address", "Email Type", "Category", "LinkedIn Profile"]],
                column_config={
                    "LinkedIn Profile": st.column_config.LinkColumn("LinkedIn")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No profiles retrieved. Double check your Search Engine ID and API Key.")
