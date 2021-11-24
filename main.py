import os
import datetime
import json
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from mlxtend.frequent_patterns import apriori, association_rules

# SET PAGE LAYOUT TO WIDE
st.set_page_config(
    page_title="Open Source - PmDARM", layout="wide")
# , layout="wide"
st.title('Open Source Product Monitoring Dashboard with Association Rule Mining - PmDARM')
checker = False

header = st.container()
metrics_1, metrics_2 = st.columns(2)
main_contents = st.container()
a_priori = st.container()
tester = st.container()
QvM1, QvM2 = st.columns(2)
sidebar = st.sidebar.container()


# Hot encode function for suitability of the dataframe
def hot_encode(x):
    if(x <= 0):
        return 0
    if(x >= 1):
        return 1

# MAKE AD-HOC FUNCTION TO REMOVE UNRELATED WORDS (UN-JARGONIZER)


def removeJargon(sentence):
    new_str = ''
    for char in sentence:
        if char not in (',', '{', '}', '(', ')', '\'',):
            new_str += char
    new_str = new_str.replace('frozenset', '')
    return new_str

# MAKE AD-HOC FUNCTION TO CALL F-SET RELATED DATASET TO UN-JARGONIZE (UN-JARGONIZER BY DATASET AND COL-NAME)


def fSets_remove(dataset, colName):
    # MAKE NEW LIST TO STORE ALL P-W-B COLUMN FOR REPLACE LATER
    gotStr = []
    for i in range(len(dataset)):
        gotStr.append(removeJargon(
            str(dataset[colName][i])).replace(' ', ' and '))

    # REPLACE ALL P-W-B COLUMN INTO NEW STRING FROM PREVIOUS LIST
    dataset[colName] = dataset[colName].replace(
        dataset[colName].tolist(), gotStr)
    return dataset


# SIDEBAR
# TO INPUT RELEVANT DATASET
with sidebar:
    try:
        # Upload a file to the csv uploader
        data_file = st.file_uploader("Upload CSV", type=["csv"])
        if data_file is not None:

            # when no entry is inserted
            checker = True
            file_details = {"filename": data_file.name,
                            "filetype": data_file.type, "filesize": data_file.size}

            # Caching dataset
            @st.cache(allow_output_mutation=True)
            def load_csv():
                dataset = pd.read_csv(data_file)
                return dataset
            dataset = load_csv()

            if dataset.columns[0] == "Unnamed: 0":
                dataset.drop('Unnamed: 0', inplace=True, axis=1)

            # set "Order Date" to datetime format in python
            dataset["Order Date"] = pd.to_datetime(dataset["Order Date"])
        else:
            st.empty()

    except FileNotFoundError:
        # st.error('File specification error')
        with header:
            st.caption("Error")
            st.text('Please specify valid dataset(s) in the sidebar')

if checker == False:
    with header:
        st.caption("Error")
        st.text('No dataset specified.')
        st.text('Please specify valid dataset(s) in the sidebar.')

# SUCCESS DATASET RETRIEVAL
# TOP HEADER
with header:
    try:
        # Preparing plots for DATE vs Quantity (bar and line)
        fig1 = px.bar(
            dataset,
            x=dataset["Order Date"].dt.strftime("%Y-%m").unique(),
            y=dataset.groupby(dataset["Order Date"].dt.strftime(
                "%Y-%m")).Quantity.sum(),
            labels={'x': 'Date', 'y': 'Quantity'},
            title="Date vs Quantity (bar)")
        fig2 = px.line(
            dataset,
            x=dataset["Order Date"].dt.strftime("%Y-%m").unique(),
            y=dataset.groupby(dataset["Order Date"].dt.strftime(
                "%Y-%m")).Quantity.sum(),
            labels={'x': 'Date', 'y': 'Quantity'},
            title="Date vs Quantity (line)")

        # Expander to show dataset
        with st.expander("See dataset"):
            st.write(dataset)

        # Header and prepare charts for DATE vs Quantity (bar and line)
        st.header("Monthly Sales (Quantity)")
        st.markdown('Over here it shows the monthly sales by **quantity** from {} to {}.'.format(
            dataset["Order Date"].dt.year.min(), dataset["Order Date"].dt.year.max()))
        QxM1, QxM2 = st.columns(2)
        QxM1.plotly_chart(fig1, use_container_width=True)
        QxM2.plotly_chart(fig2, use_container_width=True)

        # Expander to explore on the states purchases by year-month
        with st.expander("Show more details"):
            st.markdown(''' 
                > #### State Purchase Ranking             
                > Over here, we can see transactions of participating states over the fiscal year.''')
            choice_col, show_table_col = st.columns([1, 3])
            with choice_col:
                time_choice = dataset["Order Date"].dt.strftime(
                    "%Y-%m").unique().tolist()
                selected_datetime = st.selectbox(
                    "Choose date (YYYY-mm):", options=time_choice, index=0)
            with show_table_col:
                rank_state = dataset.groupby([dataset["Order Date"].dt.strftime(
                    "%Y-%m"), "State"])["Order ID"].count().to_frame().reset_index()
                rank_state["Order Date"] = pd.to_datetime(
                    rank_state["Order Date"])
                table_df = rank_state[rank_state["Order Date"].dt.strftime(
                    "%Y-%m") == selected_datetime].sort_values('Order ID', ascending=False)
                table_df = table_df.rename(columns={'Order ID': 'Count'})
                st.write(table_df)

    except:
        # do nothing
        st.text("")

# METRIC DATA 1
with metrics_1:

    try:
        labels = dataset.Category.unique()
        perc_val = dataset.groupby(
            dataset["Category"]).Quantity.sum() / dataset.Quantity.sum()

        fig = go.Figure(
            data=[go.Pie(labels=labels, values=perc_val, hole=.65)])
        fig.update_layout(
            title="Top Sales (Category)",
            # width=500, height=500,
            # margin=dict(l=5, r=5, t=5, b=5),
            template="presentation")
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.empty()


# METRIC DATA 2
with metrics_2:

    try:
        sc_quant_table = pd.DataFrame()
        sc_quant_table["Sub-Category"] = sorted(
            dataset["Sub-Category"].unique())
        sc_quant_table["Quantity"] = dataset.groupby(
            dataset["Sub-Category"]).Quantity.sum().tolist()
        sc_quant_table = sc_quant_table.sort_values(
            by="Quantity", ascending=False)

        # labels for Sub-Category
        sc_labels = sc_quant_table["Sub-Category"].head(5)
        sc_perc_val = sc_quant_table["Quantity"].head(
            5)/sc_quant_table["Quantity"].head(5).sum()

        # Use `hole` to create a donut-like pie chart
        fig = go.Figure(
            data=[go.Pie(labels=sc_labels, values=sc_perc_val, hole=.65)])
        fig.update_layout(
            title="Top 5 Sales (Items)",
            # width=500, height=500,
            # margin=dict(l=5, r=5, t=5, b=5),
            template="presentation"
        )
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.empty()


with st.expander("More details about Category and Sub-Category"):
    try:
        catCol, itemCol = st.columns(2)
        subCol1, subCol2, subCol3 = st.columns(3)
        category = sorted(dataset["Category"].unique().tolist())
        items = sorted(dataset["Sub-Category"].unique().tolist())
        clothing = sorted(dataset.loc[dataset["Category"]
                                      == "Clothing"]["Sub-Category"].unique().tolist())
        electronics = sorted(
            dataset.loc[dataset["Category"] == "Electronics"]["Sub-Category"].unique().tolist())
        furniture = sorted(
            dataset.loc[dataset["Category"] == "Furniture"]["Sub-Category"].unique().tolist())
        with catCol:
            st.markdown(' #### List of Categories.')
            st.table(category)

            with subCol1:
                st.markdown(' **Clothing** ')
                st.table(clothing)
            with subCol2:
                st.markdown(' **Electronics** ')
                st.table(electronics)
            with subCol3:
                st.markdown(' **Furniture** ')
                st.table(furniture)

        with itemCol:
            st.markdown(' #### List of Sub-Categories.')
            st.table(items)
    except:
        st.empty()

with st.spinner('Coloring map... wait for it...'):
    try:
        # GETTING JSON FILE AND LOAD INTO "indian_states"
        indian_states = json.load(open('states_india.geojson'))

        # MAKING NEW FEATURE IN JSON AS ID FROM STATE CODE FOR DATASET LATER
        state_id_map = {}
        for feature in indian_states['features']:
            feature['id'] = feature['properties']['state_code']
            state_id_map[feature['properties']['st_nm']] = feature['id']

        # MAP ID WITH STATE (DATASET) FROM THE JSON FILE
        dataset['id'] = dataset['State'].apply(lambda x: state_id_map[x])

        # MAKING NEW DF FOR PURPOSE OF CHORO-MAP
        for_map = pd.DataFrame()
        for_map["State"] = sorted(dataset["State"].unique())
        for_map["Quantity"] = dataset.groupby(
            dataset["State"]).Quantity.sum().tolist()
        for_map['id'] = for_map['State'].apply(lambda x: state_id_map[x])

        # MAKING CHOROPLETH MAP
        fig = px.choropleth(for_map, locations='id',
                            geojson=indian_states,
                            color='Quantity',
                            hover_name='State',
                            scope='asia',
                            height=750)
        fig.update_geos(fitbounds="locations", visible=True)
        st.header("Quantity of Sales by State")
        st.markdown('''
        Over here you have the **states** depicted in chorepleth/thematic map based on the **quantity of sales**.
        ''')
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.empty()


with st.spinner('Baking rules...'):

    try:
        st.header("Market Basket Recommendation List")
        st.markdown('''
            Over here are the recommendation lists of item(s) from the selected **city** of the **state**.
        ''')

        # Make 2 columns
        customization_col, show_col = st.columns([1, 3])
        defaultState = dataset['State'].unique()
        # defaultCity = dataset['State'==defaultState].City.unique()

        with customization_col:
            count = 1

            # choose State
            stateName = st.selectbox(
                "Choose State:", options=sorted(defaultState), index=0)

            # Choose City Box
            chosen_cityName = st.selectbox(
                "Choose City:", options=dataset[dataset["State"] == stateName].City.unique().tolist(), index=0)

        with show_col:

            # Setting metrics for ARM (with defaultilizer)
            set_cityName = chosen_cityName
            minSPval = 0
            set_metric = ""
            set_min_threshold = 0

            try:
                if set_cityName == "":
                    set_cityName = dataset["State"].City.unique().tolist()[
                        0]
                if minSPval == 0:
                    minSPval = 0.1
                if set_metric == "":
                    set_metric = "lift"
                if set_min_threshold == 0:
                    set_min_threshold = 1
            except:
                default_cityName = dataset["State"].City.unique().tolist()[
                    0]
                minSPval = 0.1
                set_metric = "lift"
                set_min_threshold = 1

            # Making raw rules for ARM with frozensets
            basket = (dataset[dataset['City'] == set_cityName]
                      .groupby(['Order ID', 'Sub-Category'])['Quantity']
                      .sum().unstack().reset_index().fillna(0)
                      .set_index('Order ID')
                      )
            # Apply OHE into MHT df
            basket_encoded = basket.applymap(hot_encode)
            basket = basket_encoded

            # Building the model
            frq_items_basket = apriori(
                basket, min_support=0.1, use_colnames=True)

            # Collecting inferred rules in df
            rules_basket = association_rules(
                frq_items_basket, metric=set_metric, min_threshold=1)
            rules_basket = rules_basket.sort_values(
                ['confidence', 'lift'], ascending=[False, False])

            # Generated Rules (unjargonizer and user-friendly)
            # MAKE NEW DF WITH USER FRIENDLY TERMS
            report_df = pd.DataFrame()
            report_df["People who buy"] = rules_basket.antecedents.tolist()
            report_df["Will buy"] = rules_basket.consequents.tolist()
            report_df["Cross-selling metric"] = rules_basket.lift.tolist()

            # CALL AD-HOC UNJARGONIZER
            fSets_remove(report_df, "People who buy")
            fSets_remove(report_df, "Will buy")
            report_df = report_df.sort_values(
                ["Cross-selling metric"], ascending=False)
            report_df = report_df.style.hide_index()
            st.write(report_df)

        with st.expander("More details"):

            # math columns - mCol
            mCol1, mCol2, mCol3 = st.columns(3)

            with mCol1:
                st.latex(r'''
                    \large Support = \dfrac{ freq(A,B) }{N}
                ''')
                st.markdown('''
                    *Frequency of item/itemsets over the entire dataset.*
                ''')
            with mCol2:
                st.latex(r'''
                    \large Confidence = \dfrac{ freq(A,B) }{ freq(A)}
                ''')
                st.markdown('''
                    *Frequency of itemsets given the antecedent item is purchased.* 
                    > Think of it as Bayes' theorem of Probability!
                ''')
            with mCol3:
                st.latex(r'''
                    \large Lift = \dfrac{ Supp (A,B) }{ Supp(A) \bullet Supp(B) }
                ''')
                st.markdown('''
                    *The correlation between both items/itemsets.* 
                    > As stated in the Market Recommendation List, it's the value of cross-selling opportunity!
                ''')

            report = rules_basket
            fSets_remove(report, "antecedents")
            fSets_remove(report, "consequents")
            report.drop('leverage', inplace=True, axis=1)
            report.drop('conviction', inplace=True, axis=1)
            st.write(report)
    except:
        st.empty()
