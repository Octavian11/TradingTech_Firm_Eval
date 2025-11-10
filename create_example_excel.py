#!/usr/bin/env python3
"""
Creates an example Excel file for the investment screening agent.
"""

import pandas as pd

# Sample company data
companies = [
    {
        "Name": "Acme Software Solutions",
        "Location": "San Francisco, CA",
        "Website": "https://acmesoftware.example.com",
        "Revenue": "$5M ARR",
        "Deep Research": "B2B SaaS, 50 employees, YoY growth 40%",
        "Notes": "Strong customer retention",
        "Verdict": "",
        "Rationale": "",
        "Processed?": "No"
    },
    {
        "Name": "TechFlow Analytics",
        "Location": "Austin, TX",
        "Website": "https://techflow.example.com",
        "Revenue": "$12M ARR",
        "Deep Research": "AI-powered analytics platform, 120 employees",
        "Notes": "Recently secured Series B funding",
        "Verdict": "",
        "Rationale": "",
        "Processed?": "No"
    },
    {
        "Name": "CloudOps Pro",
        "Location": "Seattle, WA",
        "Website": "https://cloudops.example.com",
        "Revenue": "$3M ARR",
        "Deep Research": "DevOps automation, 25 employees",
        "Notes": "Profitable, bootstrapped",
        "Verdict": "",
        "Rationale": "",
        "Processed?": "No"
    },
    {
        "Name": "DataBridge Inc",
        "Location": "Boston, MA",
        "Website": "https://databridge.example.com",
        "Revenue": "$8M ARR",
        "Deep Research": "Data integration platform, 75 employees",
        "Notes": "Enterprise clients include Fortune 500",
        "Verdict": "",
        "Rationale": "",
        "Processed?": "No"
    },
    {
        "Name": "SecureNet Systems",
        "Location": "Palo Alto, CA",
        "Website": "https://securenet.example.com",
        "Revenue": "$15M ARR",
        "Deep Research": "Cybersecurity solutions, 200 employees",
        "Notes": "High burn rate, needs capital",
        "Verdict": "",
        "Rationale": "",
        "Processed?": "No"
    }
]

# Create DataFrame
df = pd.DataFrame(companies)

# Save to Excel
output_file = "companies_to_screen.xlsx"
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"Created example Excel file: {output_file}")
print(f"Contains {len(companies)} sample companies")
print("\nColumns:")
for col in df.columns:
    print(f"  - {col}")
