import streamlit as st
import requests
import urllib.parse
import re
import pandas as pd

st.set_page_config(page_title="Executive Contact Finder", layout="wide")

st.title("🏢 Executive Contact Finder")
st.write("Extract real executive names, exact designations, emails, and direct LinkedIn profile links.")

col1, col2, col3 = st.columns([2, 2, 1.5])
with col1:
    company_name = st.text_input("Company Name (e.g., IKEA, Spotify, Volvo):", "")
with col2:
    company_domain = st.text_input("Company Domain (e.g., ikea.com, spotify.com):", "")
with col3:
    country_name = st.text_input("Country (e.g., Sweden, UK, USA):", "")

ROLES = [
    ("CEO / Executive", ["CEO", "Chief Executive Officer", "Managing Director", "President"]),
    ("Design Director", ["Design Director", "Head of Design", "VP of Design"]),
    ("UX Director", ["UX Director", "Head of UX", "Director of User Experience"]),
    ("Product Design Director", ["Product Design Director", "Head of Product Design"]),
    ("Head of HR / People", ["Chief People Officer", "Head of HR", "VP HR", "HR Director"])
]

def parse_linkedin_title(raw_title, default_role, company):
    """Parses titles like 'Jesper Brodin - Chief Executive Officer - IKEA | LinkedIn' into real names and exact job titles."""
    # Strip common site footers
    cleaned = re.sub(r'\s*[\|-]\s*LinkedIn.*$', '', raw_title, flags=re.IGNORECASE).strip()
    
    # Split by standard separators
    parts = re.split(r'\s*[-–|]\s*', cleaned)
    
    if len(parts) >= 2:
        name = parts[0].strip()
        designation = " - ".join(parts[1:]).strip()
    elif len(parts) == 1 and parts[0]:
        name = parts[0].strip()
        designation = f"{default_role} at {company}"
    else:
        name = "Unknown"
        designation = default_role
        
    return name, designation

def generate_email(name, domain):
    """Formats a full name into standard corporate first.last@domain.com pattern."""
    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip().lower()
    parts = clean_name.split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[-1]}@{domain}"
    elif len(parts) == 1 and parts[0]:
        return f"{parts[0]}@{domain}"
    return f"info@{domain}"

def search_real_person(company, role_list, country=""):
    """Queries live search indexes for real person profiles matching company, role, and country."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for kw in role_list:
        query_str = f'site:linkedin.com/in/ "{company}" "{kw}" {country}'.strip()
        
        # Query DuckDuckGo JSON Lite API
        api_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query_str)}"
        
        try:
            res = requests.get(api_url, headers=headers, timeout=6)
            if res.status_code == 200:
                # Extract profile URLs and titles from html response
                matches = re.findall(r'<a class="result__url" href="([^"]+)".*?><a class="result__title"[^>]*>(.*?)</a>', res.text, re.DOTALL)
                
                if not matches:
                    # Alternative regex for result parsing
                    titles = re.findall(r'class="result__title"[^>]*>(.*?)</a>', res.text, re.DOTALL)
                    links = re.findall(r'uddg=([^&"]+)', res.text)
                    if titles and links:
                        matches = list(zip(links, titles))

                for link, raw_title in matches:
                    clean_link = urllib.parse.unquote(link.replace('/l/?uddg=', ''))
                    clean_raw_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                    
                    if 'linkedin.com/in/' in clean_link and clean_raw_title:
                        name, designation = parse_linkedin_title(clean_raw_title, kw, company)
                        
                        # Validate that name is a real person name (minimum two words, not generic site text)
                        if len(name.split()) >= 2 and not any(x in name.lower() for x in ['linkedin', 'profile', 'jobs', 'directory', 'top']):
                            return name, designation, clean_link
        except Exception:
            pass

    return None, None, None

if st.button("Extract Real Executive Contacts"):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        clean_company = company_name.strip()
        clean_country = country_name.strip()
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip() if company_domain else f"{clean_company.lower().replace(' ', '')}.com"

        target_info = f"**{clean_company}** ({clean_country})" if clean_country else f"**{clean_company}**"
        st.info(f"Extracting real person names and profiles for {target_info}...")

        extracted_data = []

        for category, role_keywords in ROLES:
            name, designation, profile_url = search_real_person(clean_company, role_keywords, clean_country)
            
            if name and profile_url:
                email = generate_email(name, domain)
                extracted_data.append({
                    "Full Name": name,
                    "Designation": designation,
                    "Estimated Email": email,
                    "Country": clean_country if clean_country else "Global",
                    "Category": category,
                    "LinkedIn Profile": profile_url
                })
            else:
                # Direct fallback query URL to manually view matching profiles
                fallback_query = f'"{clean_company}" "{role_keywords[0]}" {clean_country} site:linkedin.com/in/'
                fallback_url = f"https://www.google.com/search?q={urllib.parse.quote(fallback_query)}"
                extracted_data.append({
                    "Full Name": f"Search: {role_keywords[0]}",
                    "Designation": f"{role_keywords[0]} at {clean_company}",
                    "Estimated Email": f"{role_keywords[0].lower().replace(' ', '')}@{domain}",
                    "Country": clean_country if clean_country else "Global",
                    "Category": category,
                    "LinkedIn Profile": fallback_url
                })

        df = pd.DataFrame(extracted_data)

        st.success("Executive extraction completed!")

        st.dataframe(
            df[["Full Name", "Designation", "Estimated Email", "Country", "Category", "LinkedIn Profile"]],
            column_config={
                "LinkedIn Profile": st.column_config.LinkColumn("LinkedIn Profile", display_text="Open Profile")
            },
            use_container_width=True,
            hide_index=True
        )
