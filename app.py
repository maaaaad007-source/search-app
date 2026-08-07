import streamlit as st
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import pandas as pd

st.set_page_config(page_title="Executive Name & Email Extractor", layout="wide")

st.title("🏢 Executive Name & Email Extractor")
st.write("Extract real names, designations, generated emails, and LinkedIn links directly into a single table.")

col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("Company Name (e.g., Spotify, Volvo, IKEA):", "")
with col2:
    company_domain = st.text_input("Company Domain (e.g., spotify.com, volvocars.com):", "")

ROLES = [
    ("CEO / Executive", '("CEO" OR "Chief Executive Officer" OR "Managing Director")'),
    ("Design Director", '("Design Director" OR "Head of Design" OR "VP of Design")'),
    ("UX Director", '("UX Director" OR "Head of UX" OR "Director of UX")'),
    ("Product Design Director", '("Product Design Director" OR "Head of Product Design")'),
    ("Head of HR / People", '("Head of HR" OR "Chief People Officer" OR "VP HR")')
]

def clean_title(title):
    """Parses raw search titles into clean Name and Designation."""
    # Remove branding suffixes
    title = re.sub(r' - LinkedIn| \| LinkedIn| - Google News', '', title)
    
    parts = re.split(r' - | – | \| ', title)
    if len(parts) >= 2:
        name = parts[0].strip()
        designation = parts[1].strip()
    else:
        name = parts[0].strip()
        designation = "Executive / Leader"
        
    return name, designation

def make_email(name, domain):
    """Generates standard first.last@domain email format."""
    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip().lower()
    parts = clean_name.split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[-1]}@{domain}"
    elif len(parts) == 1 and parts[0]:
        return f"{parts[0]}@{domain}"
    return f"contact@{domain}"

def fetch_names_via_feed(company, query_term):
    """Fetches public feeds to extract real executive names without API keys."""
    results = []
    search_str = f'"{company}" {query_term} site:linkedin.com/in/'
    encoded_query = urllib.parse.quote(search_str)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    req = urllib.request.Request(
        rss_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            for item in root.findall('.//item')[:2]:
                raw_title = item.find('title').text if item.find('title') is not None else ""
                raw_link = item.find('link').text if item.find('link') is not None else ""
                
                if raw_title:
                    name, designation = clean_title(raw_title)
                    results.append((name, designation, raw_link))
    except Exception:
        pass

    return results

if st.button("Extract Names & Contacts"):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        clean_company = company_name.strip()
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip() if company_domain else f"{clean_company.lower().replace(' ', '')}.com"

        st.info(f"Extracting target names and emails for **{clean_company}**...")

        extracted_rows = []

        for category, role_keywords in ROLES:
            feed_results = fetch_names_via_feed(clean_company, role_keywords)
            
            if feed_results:
                for name, designation, link in feed_results:
                    email = make_email(name, domain)
                    extracted_rows.append({
                        "Category": category,
                        "Full Name": name,
                        "Designation": designation,
                        "Estimated Email": email,
                        "Profile Search": f"https://www.google.com/search?q={urllib.parse.quote(name + ' ' + clean_company + ' LinkedIn')}"
                    })
            else:
                # Fallback if no specific feed items are returned
                fallback_name = f"{category.split('/')[0].strip()} Lead"
                extracted_rows.append({
                    "Category": category,
                    "Full Name": fallback_name,
                    "Designation": f"{category} at {clean_company}",
                    "Estimated Email": f"{category.split('/')[0].lower().replace(' ', '')}@{domain}",
                    "Profile Search": f"https://www.google.com/search?q={urllib.parse.quote('site:linkedin.com/in/ ' + role_keywords + ' ' + clean_company)}"
                })

        df = pd.DataFrame(extracted_rows)

        st.success(f"Generated {len(df)} executive contact profile(s)!")

        st.dataframe(
            df[["Full Name", "Designation", "Estimated Email", "Category", "Profile Search"]],
            column_config={
                "Profile Search": st.column_config.LinkColumn("Verify Profile")
            },
            use_container_width=True,
            hide_index=True
        )
