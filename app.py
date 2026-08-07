import streamlit as st
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import pandas as pd

st.set_page_config(page_title="Executive Name & Email Extractor", layout="wide")

st.title("🏢 Executive Name & Email Extractor")
st.write("Extract real names, designations, emails, and direct LinkedIn profile links targeted by company and country.")

# User Inputs
col1, col2, col3 = st.columns([2, 2, 1.5])
with col1:
    company_name = st.text_input("Company Name (e.g., Spotify, Volvo, IKEA):", "")
with col2:
    company_domain = st.text_input("Company Domain (e.g., spotify.com, volvocars.com):", "")
with col3:
    country_name = st.text_input("Country (e.g., Sweden, USA, UK):", "")

ROLES = [
    ("CEO / Executive", '("CEO" OR "Chief Executive Officer" OR "Managing Director")'),
    ("Design Director", '("Design Director" OR "Head of Design" OR "VP of Design")'),
    ("UX Director", '("UX Director" OR "Head of UX" OR "Director of UX")'),
    ("Product Design Director", '("Product Design Director" OR "Head of Product Design")'),
    ("Head of HR / People", '("Head of HR" OR "Chief People Officer" OR "VP HR")')
]

def clean_title(title):
    """Parses raw search titles into clean Name and Designation."""
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

def get_direct_linkedin_url(name, company, country=""):
    """Generates direct targeted LinkedIn profile search link for exact name match."""
    location_str = f'"{country}"' if country else ""
    query = f'"{name}" "{company}" {location_str} site:linkedin.com/in/'
    encoded_query = urllib.parse.quote(query)
    return f"https://www.google.com/search?q={encoded_query}"

def fetch_names_via_feed(company, query_term, country=""):
    """Fetches public feeds to extract real executive names based on country criteria."""
    results = []
    location_str = f'"{country}"' if country else ""
    search_str = f'"{company}" {query_term} {location_str} site:linkedin.com/in/'
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
                
                if raw_title:
                    name, designation = clean_title(raw_title)
                    direct_linkedin = get_direct_linkedin_url(name, company, country)
                    results.append((name, designation, direct_linkedin))
    except Exception:
        pass

    return results

if st.button("Extract Names & Contacts"):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        clean_company = company_name.strip()
        clean_country = country_name.strip()
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip() if company_domain else f"{clean_company.lower().replace(' ', '')}.com"

        target_info = f"**{clean_company}** ({clean_country})" if clean_country else f"**{clean_company}**"
        st.info(f"Extracting target names and direct LinkedIn links for {target_info}...")

        extracted_rows = []

        for category, role_keywords in ROLES:
            feed_results = fetch_names_via_feed(clean_company, role_keywords, clean_country)
            
            if feed_results:
                for name, designation, link in feed_results:
                    email = make_email(name, domain)
                    extracted_rows.append({
                        "Category": category,
                        "Full Name": name,
                        "Designation": designation,
                        "Estimated Email": email,
                        "Country": clean_country if clean_country else "Global / Specified",
                        "LinkedIn Profile": link
                    })
            else:
                fallback_name = f"{category.split('/')[0].strip()} Lead"
                search_keywords = f"{clean_company} {clean_country} {role_keywords}".strip()
                linkedin_fallback = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(search_keywords)}"
                extracted_rows.append({
                    "Category": category,
                    "Full Name": fallback_name,
                    "Designation": f"{category} at {clean_company}",
                    "Estimated Email": f"{category.split('/')[0].lower().replace(' ', '')}@{domain}",
                    "Country": clean_country if clean_country else "Global / Specified",
                    "LinkedIn Profile": linkedin_fallback
                })

        df = pd.DataFrame(extracted_rows)

        st.success(f"Generated {len(df)} executive contact profile(s)!")

        st.dataframe(
            df[["Full Name", "Designation", "Estimated Email", "Country", "Category", "LinkedIn Profile"]],
            column_config={
                "LinkedIn Profile": st.column_config.LinkColumn("LinkedIn Profile", display_text="Open LinkedIn")
            },
            use_container_width=True,
            hide_index=True
        )
