import streamlit as st
import urllib.parse
import pandas as pd

st.set_page_config(page_title="Executive Sourcing & Email Portal", layout="wide")

st.title("🏢 Automated Executive Sourcing & Email Portal")
st.write("Generate targeted search links, email pattern guesses, and Google email extraction queries (No Paid API Required).")

# Inputs
company_name = st.text_input("Company Name (e.g., Spotify, Volvo, IKEA):", "")
company_domain = st.text_input("Company Domain (e.g., spotify.com, volvocars.com, ikea.com):", "")

# Roles Configuration
ROLES = [
    {
        "Role": "CEO / Managing Director",
        "Keywords": '("CEO" OR "Chief Executive Officer" OR "President & CEO" OR "Managing Director")'
    },
    {
        "Role": "Design Director",
        "Keywords": '("Design Director" OR "Head of Design" OR "VP of Design" OR "Director of Design")'
    },
    {
        "Role": "UX Director",
        "Keywords": '("UX Director" OR "Director of UX" OR "Head of UX" OR "User Experience Director")'
    },
    {
        "Role": "Product Design Director",
        "Keywords": '("Product Design Director" OR "Head of Product Design" OR "Director of Product Design")'
    },
    {
        "Role": "Head of HR / Chief People Officer",
        "Keywords": '("Head of HR" OR "Chief People Officer" OR "VP HR" OR "Director of Human Resources" OR "Head of People")'
    }
]

if st.button("Find Executives & Email Queries"):
    if not company_name:
        st.warning("Please enter a company name.")
    else:
        clean_company = company_name.strip()
        domain = company_domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip() if company_domain else f"{clean_company.lower().replace(' ', '')}.com"
        
        st.subheader(f"1. Executive Profile Search Links ({clean_company})")
        
        search_data = []
        for role_info in ROLES:
            role_name = role_info["Role"]
            keywords = role_info["Keywords"]
            
            # Google X-Ray Search Link
            google_query = f'site:linkedin.com/in/ {keywords} AND "{clean_company}"'
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(google_query)}"
            
            # LinkedIn Direct Link
            linkedin_query = f'{keywords} AND "{clean_company}"'
            linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(linkedin_query)}"

            # Google Public Email Finder Query
            email_query = f'"{clean_company}" {keywords} "@{domain}"'
            email_search_url = f"https://www.google.com/search?q={urllib.parse.quote(email_query)}"

            search_data.append({
                "Role": role_name,
                "Find Profile (Google)": google_url,
                "Find Profile (LinkedIn)": linkedin_url,
                "Search Public Emails": email_search_url
            })

        df = pd.DataFrame(search_data)

        st.dataframe(
            df,
            column_config={
                "Find Profile (Google)": st.column_config.LinkColumn("Google Profile Search"),
                "Find Profile (LinkedIn)": st.column_config.LinkColumn("LinkedIn Search"),
                "Search Public Emails": st.column_config.LinkColumn("Find Email on Web")
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader(f"2. Likely Corporate Email Formats (`@{domain}`)")
        
        st.write("Most corporate email structures follow standard corporate conventions. Test these patterns once you find an executive's full name:")

        email_patterns = [
            {"Format": "First . Last", "Example": f"john.doe@{domain}"},
            {"Format": "First initial + Last", "Example": f"jdoe@{domain}"},
            {"Format": "First Name Only", "Example": f"john@{domain}"},
            {"Format": "First + Last initial", "Example": f"johnd@{domain}"},
            {"Format": "First _ Last", "Example": f"john_doe@{domain}"}
        ]
        
        st.table(pd.DataFrame(email_patterns))

        st.markdown("---")
        st.subheader("3. Free Public Email Extractor Strings")
        st.write("Copy and paste these queries into Google to uncover raw email addresses published on documents, press releases, or speaker listings:")
        
        st.code(f'"{domain}" AND ("@ {domain}" OR "@{domain}") AND ("CEO" OR "Design" OR "HR")', language="text")
