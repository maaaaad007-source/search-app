import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
import pandas as pd

st.set_page_config(page_title="Free Unlimited Executive Sourcing", layout="wide")

st.title("🏢 Automated Executive & Email Scraper (100% Free & Unlimited)")
st.write("Extract public email addresses and generate decision-maker search links using web scraping.")

company_name = st.text_input("Company Name (e.g., Spotify, Volvo, IKEA):", "")
company_domain = st.text_input("Company Domain (e.g., spotify.com, volvocars.com, ikea.com):", "")

def scrape_public_emails(domain):
    """Scrapes public search results to extract indexed emails ending with @domain."""
    found_emails = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }

    # Search queries aimed at uncovering public emails
    queries = [
        f'"{domain}" contact email',
        f'"{domain}" executive email "@ {domain}"',
        f'site:linkedin.com/in/ "{domain}" email'
    ]

    for q in queries:
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = soup.get_text()

                # Regex pattern matching any email belonging to the domain
                pattern = rf'[a-zA-Z0-9._%+-]+@{re.escape(domain)}'
                matches = re.findall(pattern, text, re.IGNORECASE)
                for m in matches:
                    found_emails.add(m.lower())
        except Exception:
            pass

    return list(found_emails)

if st.button("Run Scraper & Search"):
    if not company_name or not company_domain:
        st.warning("Please enter both the company name and domain.")
    else:
        clean_company = company_name.strip()
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip()

        st.markdown("---")
        st.subheader(f"1. Automatically Scraped Emails for `@{domain}`")
        
        with st.spinner("Scraping public search indexes for live emails..."):
            scraped_emails = scrape_public_emails(domain)

        if scraped_emails:
            st.success(f"Found {len(scraped_emails)} publicly indexed email address(es)!")
            email_df = pd.DataFrame({"Public Email Address": scraped_emails})
            st.table(email_df)
        else:
            st.info("No raw email addresses were directly exposed in public snippets. Use the target search links below to identify executive names.")

        st.markdown("---")
        st.subheader("2. Targeted Decision-Maker Links")

        roles = [
            ("CEO / Managing Director", '("CEO" OR "Chief Executive Officer" OR "Managing Director")'),
            ("Design Director", '("Design Director" OR "Head of Design" OR "VP of Design")'),
            ("UX Director", '("UX Director" OR "Head of UX" OR "Director of UX")'),
            ("Product Design Director", '("Product Design Director" OR "Head of Product Design")'),
            ("Head of HR / People", '("Head of HR" OR "Chief People Officer" OR "VP HR")')
        ]

        search_data = []
        for role_name, keywords in roles:
            google_query = f'site:linkedin.com/in/ {keywords} AND "{clean_company}"'
            linkedin_query = f'{keywords} AND "{clean_company}"'
            
            search_data.append({
                "Target Role": role_name,
                "Google X-Ray Link": f"https://www.google.com/search?q={urllib.parse.quote(google_query)}",
                "LinkedIn Link": f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(linkedin_query)}"
            })

        st.dataframe(
            pd.DataFrame(search_data),
            column_config={
                "Google X-Ray Link": st.column_config.LinkColumn("Google Profile Search"),
                "LinkedIn Link": st.column_config.LinkColumn("LinkedIn Search")
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("3. Recommended Email Formula")
        st.write(f"Once you find an executive's name on LinkedIn, apply these common pattern formats for `@{domain}`:")
        
        st.table(pd.DataFrame([
            {"Pattern": "First . Last", "Example": f"first.last@{domain}"},
            {"Pattern": "First Initial + Last", "Example": f"f.last@{domain} or flast@{domain}"},
            {"Pattern": "First Name Only", "Example": f"first@{domain}"}
        ]))
