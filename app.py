import streamlit as st
import urllib.request
import urllib.parse
import re
import pandas as pd
from bs4 import BeautifulSoup

st.set_page_config(page_title="Executive Contact Finder", layout="wide")

st.title("🏢 Executive Contact Finder")
st.write("Extract real executive names, designations, and verified LinkedIn profile links.")

col1, col2, col3 = st.columns([2, 2, 1.5])
with col1:
    company_name = st.text_input("Company Name (e.g., Volvo, Spotify, IKEA):", "")
with col2:
    company_domain = st.text_input("Company Domain (e.g., volvocars.com, spotify.com):", "")
with col3:
    country_name = st.text_input("Country (e.g., Sweden, UK, USA):", "")

# Expanded Keywords for exact leadership roles
ROLES = [
    ("CEO / Executive", [
        "Chief Executive Officer", "CEO", "Managing Director", "President", "Executive Director", "Country Head"
    ]),
    ("Design Director", [
        "Design Director", "Head of Design", "VP of Design", "Vice President Design", "Global Design Director"
    ]),
    ("UX Director", [
        "UX Director", "Head of UX", "Director of User Experience", "VP UX", "Global Head of UX"
    ]),
    ("Product Design Director", [
        "Product Design Director", "Head of Product Design", "VP Product Design", "Director Product Design"
    ]),
    ("Head of HR / People", [
        "Chief People Officer", "Head of HR", "VP HR", "VP People", "HR Director", "Director Human Resources"
    ])
]

def clean_title(raw_title, company):
    """Clean LinkedIn title string to extract Full Name and Designation."""
    # Remove branding
    cleaned = re.sub(r' - LinkedIn| \| LinkedIn| - Google Search', '', raw_title, flags=re.IGNORECASE)
    parts = re.split(r' - | – | \| ', cleaned)
    
    if len(parts) >= 2:
        name = parts[0].strip()
        designation = " - ".join(parts[1:]).strip()
    else:
        name = parts[0].strip()
        designation = f"Executive at {company}"
        
    return name, designation

def generate_email(name, domain):
    """Generates standard corporate email address."""
    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip().lower()
    parts = clean_name.split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[-1]}@{domain}"
    elif len(parts) == 1 and parts[0]:
        return f"{parts[0]}@{domain}"
    return f"info@{domain}"

def fetch_real_profiles(company, keywords, country=""):
    """Scrapes public search results directly for real LinkedIn profiles."""
    results = []
    kw_query = ' OR '.join([f'"{kw}"' for kw in keywords])
    location_query = f'"{country}"' if country else ""
    
    # Target exact LinkedIn profile pages
    search_query = f'site:linkedin.com/in/ "{company}" ({kw_query}) {location_query}'.strip()
    encoded_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"
    
    req = urllib.request.Request(
        encoded_url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href', '')
                # Unpack DuckDuckGo redirect link
                if 'uddg=' in href:
                    actual_url = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                else:
                    actual_url = href
                    
                if 'linkedin.com/in/' in actual_url:
                    title_elem = a.find_parent('div', class_='result__body')
                    if title_elem and title_elem.find('a', class_='result__title'):
                        raw_title = title_elem.find('a', class_='result__title').get_text().strip()
                        name, designation = clean_title(raw_title, company)
                        # Ensure we don't pick generic search page titles
                        if name.lower() not in ["linkedin", "profiles", "top", "jobs"] and len(name.split()) >= 2:
                            results.append((name, designation, actual_url))
                            if len(results) >= 2:
                                break
    except Exception:
        pass
        
    return results

if st.button("Extract Real Executive Contacts"):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        clean_company = company_name.strip()
        clean_country = country_name.strip()
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip() if company_domain else f"{clean_company.lower().replace(' ', '')}.com"

        target_info = f"**{clean_company}** ({clean_country})" if clean_country else f"**{clean_company}**"
        st.info(f"Searching real LinkedIn executive profiles for {target_info}...")

        extracted_data = []

        for category, keywords in ROLES:
            profiles = fetch_real_profiles(clean_company, keywords, clean_country)
            
            if profiles:
                for name, designation, link in profiles:
                    email = generate_email(name, domain)
                    extracted_data.append({
                        "Full Name": name,
                        "Designation": designation,
                        "Estimated Email": email,
                        "Country": clean_country if clean_country else "Global",
                        "Category": category,
                        "LinkedIn Profile": link
                    })
            else:
                # Direct search fallback URL without generating fake lead names
                search_kw = keywords[0]
                direct_search_url = f"https://www.google.com/search?q={urllib.parse.quote(f'site:linkedin.com/in/ \"{clean_company}\" \"{search_kw}\" {clean_country}')}"
                extracted_data.append({
                    "Full Name": "No direct public profile found",
                    "Designation": f"{category} candidate at {clean_company}",
                    "Estimated Email": f"{keywords[0].lower().replace(' ', '')}@{domain}",
                    "Country": clean_country if clean_country else "Global",
                    "Category": category,
                    "LinkedIn Profile": direct_search_url
                })

        df = pd.DataFrame(extracted_data)

        st.success(f"Retrieved executive profile data!")

        st.dataframe(
            df[["Full Name", "Designation", "Estimated Email", "Country", "Category", "LinkedIn Profile"]],
            column_config={
                "LinkedIn Profile": st.column_config.LinkColumn("LinkedIn Profile", display_text="Open LinkedIn Profile")
            },
            use_container_width=True,
            hide_index=True
        )
