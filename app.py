import streamlit as st
import urllib.parse
import pandas as pd

st.set_page_config(page_title="Executive Sourcing Portal", layout="wide")

st.title("🏢 Automated Executive Sourcing Portal")
st.write("Generate instant target search links for key decision-makers across any company (No API Key Required).")

# User Input
company_input = st.text_input("Enter Company Name or Domain (e.g., IKEA, Spotify, volvocars.com):", "")

# Roles configuration
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

if st.button("Generate Executive Search Links"):
    if not company_input:
        st.warning("Please enter a company name or domain.")
    else:
        # Clean company name input
        clean_company = company_input.lower().replace("https://", "").replace("http://", "").replace("www.", "").split(".")[0].capitalize()
        
        st.subheader(f"Direct Search Results for: **{clean_company}**")
        
        search_data = []

        for role_info in ROLES:
            role_name = role_info["Role"]
            keywords = role_info["Keywords"]
            
            # Construct Google X-Ray Search String
            google_query = f'site:linkedin.com/in/ {keywords} AND "{clean_company}"'
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(google_query)}"
            
            # Construct Direct LinkedIn Search Link
            linkedin_query = f'{keywords} AND "{clean_company}"'
            linkedin_url = f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(linkedin_query)}"

            search_data.append({
                "Target Executive Role": role_name,
                "Google X-Ray Link": google_url,
                "LinkedIn Direct Link": linkedin_url,
                "Boolean Query String": google_query
            })

        df = pd.DataFrame(search_data)

        # Render clickable links in table
        st.dataframe(
            df[["Target Executive Role", "Google X-Ray Link", "LinkedIn Direct Link", "Boolean Query String"]],
            column_config={
                "Google X-Ray Link": st.column_config.LinkColumn("Search on Google"),
                "LinkedIn Direct Link": st.column_config.LinkColumn("Search on LinkedIn")
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("💡 Bulk Export / Automation String")
        st.code(
            f'site:linkedin.com/in/ ("CEO" OR "Design Director" OR "UX Director" OR "Product Design Director" OR "Head of HR") AND "{clean_company}"',
            language="text"
        )
