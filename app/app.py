import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# page config
st.set_page_config(
    page_title="remote salary benchmark",
    page_icon="💰",
    layout="wide"
)

# load data
@st.cache_data
def load_data():
    df_levels = pd.read_csv('data/cleaned_data/levels_cleaned.csv')
    df_h1b = pd.read_csv('data/cleaned_data/h1b_cleaned.csv')
    return df_levels, df_h1b

df_levels, df_h1b = load_data()

# country name mapping
country_names = {
    'US': 'United States',
    'IN': 'India',
    'GB': 'United Kingdom',
    'DE': 'Germany',
    'NL': 'Netherlands'
}
df_levels['country_name'] = df_levels['employee_residence'].map(country_names)

# header
st.title("💰 remote salary benchmark")
st.markdown("### are remote tech workers in india being underpaid vs their US and European counterparts?")
st.markdown("---")

# sidebar filters
st.sidebar.header("filters")
selected_countries = st.sidebar.multiselect(
    "select countries",
    options=list(country_names.values()),
    default=list(country_names.values())
)
selected_experience = st.sidebar.multiselect(
    "experience level",
    options=['EN', 'MI', 'SE', 'EX'],
    default=['EN', 'MI', 'SE', 'EX'],
    format_func=lambda x: {'EN': 'Entry', 'MI': 'Mid', 'SE': 'Senior', 'EX': 'Executive'}[x]
)

# filter data
filtered = df_levels[
    (df_levels['country_name'].isin(selected_countries)) &
    (df_levels['experience_level'].isin(selected_experience))
]

# metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("US median salary", f"${df_levels[df_levels['employee_residence']=='US']['salary_in_usd'].median():,.0f}")
col2.metric("India median salary", f"${df_levels[df_levels['employee_residence']=='IN']['salary_in_usd'].median():,.0f}")
col3.metric("salary gap", f"{((df_levels[df_levels['employee_residence']=='US']['salary_in_usd'].median() - df_levels[df_levels['employee_residence']=='IN']['salary_in_usd'].median()) / df_levels[df_levels['employee_residence']=='US']['salary_in_usd'].median() * 100):.1f}%")
col4.metric("total records", f"{len(filtered):,}")

st.markdown("---")

# chart 1 — median salary by country
col1, col2 = st.columns(2)

with col1:
    st.subheader("median salary by country")
    chart_data = filtered.groupby('country_name')['salary_in_usd'].median().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ['#E53935' if c == 'India' else '#1565C0' for c in chart_data.index]
    ax.barh(chart_data.index, chart_data.values, color=colors)
    ax.set_xlabel('median salary (USD)')
    for i, v in enumerate(chart_data.values):
        ax.text(v + 500, i, f'${v:,.0f}', va='center')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with col2:
    st.subheader("salary by experience level")
    exp_data = filtered.groupby(['country_name', 'experience_level'])['salary_in_usd'].median().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(data=exp_data, x='experience_level', y='salary_in_usd', hue='country_name', ax=ax)
    ax.set_xlabel('experience level')
    ax.set_ylabel('median salary (USD)')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

st.markdown("---")

# salary calculator
st.subheader("💡 salary gap calculator")
st.markdown("see how your salary compares to the US median for your role")

calc_col1, calc_col2, calc_col3 = st.columns(3)
with calc_col1:
    your_salary = st.number_input("your annual salary (USD)", min_value=0, value=50000, step=1000)
with calc_col2:
    your_country = st.selectbox("your country", list(country_names.values()))
with calc_col3:
    your_role = st.selectbox("your job title", sorted(df_levels['job_title'].unique()))

us_median_role = df_levels[
    (df_levels['employee_residence'] == 'US') & 
    (df_levels['job_title'] == your_role)
]['salary_in_usd'].median()

if pd.notna(us_median_role):
    gap = ((us_median_role - your_salary) / us_median_role * 100)
    if gap > 0:
        st.error(f"you earn **{gap:.1f}% less** than the US median for {your_role} (${us_median_role:,.0f})")
    else:
        st.success(f"you earn **{abs(gap):.1f}% more** than the US median for {your_role} (${us_median_role:,.0f})")
else:
    st.info("not enough US data for this role — try another job title")

st.markdown("---")
st.markdown("**data sources:** levels.fyi, DOL H-1B disclosures, World Bank PPP 2024 | **built by:** kunal verma")