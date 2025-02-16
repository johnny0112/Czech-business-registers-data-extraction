from bs4 import BeautifulSoup
import requests
import streamlit as st
import json
import re
import datetime
from deep_translator import GoogleTranslator



st.sidebar.title("Navigace")
page = st.sidebar.radio("Vyberte stránku", ["Text", "Soubory", "Analýza"])

translator = GoogleTranslator(source='auto', target='en')

def business_register_soup_physical_person(name, surname, dob):
    response = requests.get(
        f"https://or.justice.cz/ias/ui/rejstrik-$osoba?p%3A%3Asubmit=x&.%2Frejstrik-%24osoba=&prijmeni={surname}&jmeno={name}&narozeni={dob}&obec=&angazma=&soud=&polozek=500&jenPlatne=PLATNE&typHledaniSpolku=ALL")
    business_register_soup = BeautifulSoup(response.text, "html.parser")
    return business_register_soup

def business_register_soup_company(ico):
    response = requests.get(f"https://or.justice.cz/ias/ui/rejstrik-$spolecnici?p%3A%3Asubmit=x&.%2Frejstrik-%24spolecnici=&nazev=&ico={ico}&obec=&ulice=&polozek=500&typHledani=STARTS_WITH&jenPlatne=PLATNE&typHledaniSpolku=ALL")
    business_register_soup_comp = BeautifulSoup(response.text, "html.parser")
    return business_register_soup_comp

def get_ico_list(soup):
    ico_list = []
    ico = soup.findAll('span', {'class': 'nowrap'})
    for one_ico in ico:
        if one_ico.getText() not in ico_list:
            ico_list.append(one_ico.getText())
    return ico_list

def get_company_list(soup1, ico_list):
    company_list = []
    names = soup1.findAll(class_="left")
    for i, one_name in enumerate(names):
        if i % 2 == 0 and one_name.getText() not in company_list:
            company_list.append(one_name.getText())
    for one_ico in ico_list:
        soup2 = business_register_soup_company(one_ico)
        names2 = soup2.findAll(class_="left")
        for one_name in names2:
            if one_name.getText() not in company_list:
                company_list.append(one_name.getText())
    return company_list

def get_activities(ico_list):
    activity_list = []
    for ico in ico_list:
        response = requests.get(f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty-vr/{ico}")
        data = response.json()
        for one_record in data.get('zaznamy', []):
            activity = one_record.get('cinnosti', {})
            record = activity.get('predmetPodnikani', [])
            for one_record in record:
                one_record = one_record.get('hodnota')
                translated_record = translator.translate(one_record)
                activity_list.append(translated_record)
    return activity_list

def get_link_list(ico_List):
    link_list = []
    for ico in ico_List:
        response=requests.get(f"https://or.justice.cz/ias/ui/rejstrik-$firma?p%3A%3Asubmit=x&.%2Frejstrik-%24firma=&nazev=&ico={ico}&obec=&ulice=&forma=&oddil=&vlozka=&soud=&polozek=50&typHledani=STARTS_WITH&jenPlatne=PLATNE&typHledaniSpolku=ALL")
        soup=BeautifulSoup(response.text,"html.parser")
        a=soup.find_all("a")
        base_url="https://or.justice.cz/ias/ui/"
        for one_a in a:
            if "Úplný výpis" in one_a.text:
                one_a=one_a.get("href")
                one_a=base_url+one_a
                one_a=one_a.replace("/.","")
                link_list.append(one_a)
    return link_list


def get_engagement_date(name,link_list):
    name = name.upper()
    date_list=[]

    for url in link_list:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            spans = soup.find_all("span")
            span = soup.find_all("span",string = name)
            result = []
            for index, span in enumerate(spans):
                if name in span.text:
                    result.append(spans[index+8].text)

            month_mapping = {
                " ledna ": "1.",
                " leden ": "1.",
                " únor ": "2.",
                " února ": "2.",
                " březen ": "3.",
                " března ": "3.",
                " duben ": "4.",
                " dubna ": "4.",
                " květen ": "5.",
                " května ": "5.",
                " červen ": "6.",
                " června ": "6.",
                " červenec ": "7.",
                " července ": "7.",
                " srpen ": "8.",
                " srpna ": "8.",
                " září ": "9.",
                " říjen ": "10.",
                " října ": "10.",
                " listopad ": "11.",
                " listopadu ": "11.",
                " prosinec ": "12.",
                " prosince ": "12."
            }

            # Nahrazení názvů měsíců pomocí slovníku
            for i, span in enumerate(result):
                for month_name, month_number in month_mapping.items():
                    if month_name in span:
                        result[i] = span.replace(month_name, month_number)
                        break


            string = "".join(result)

            dates = re.findall(r"\d{1,2}\.\d{1,2}\.\d{4}", string)
            if dates:
                dates = [datetime.datetime.strptime(date, "%d.%m.%Y") for date in dates]
                min_date = min(dates)
                date = min_date.strftime("%d.%m.%Y")
            else:
                date="unknown date"
            date_list.append(date)
        except(AttributeError,IndexError):
            date="unknown date"
            date_list.append(date)
    return date_list

if page == "Text":
    st.title("Business Register Automation")

    st.subheader("Zadejte údaje pro vyhledávání")
    name = st.text_input("Křestní jméno")
    surname = st.text_input("Příjmení")
    full_name = name + " " + surname
    dob = st.text_input("Datum narození", placeholder="dd.mm.rrrr")


    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            display: block;
            margin: 0 auto; /* Zarovnání na střed */
        }
        div.stButton > button:hover {
            background-color: #45a049;
        }
        </style>
    """, unsafe_allow_html=True)

    # Zobrazení tlačítka
    if st.button("Odeslat"):
        business_register_soup = business_register_soup_physical_person(name, surname, dob)
        ico_list = get_ico_list(business_register_soup)
        company_list = get_company_list(business_register_soup, ico_list)
        activity_list = get_activities(ico_list)
        link_list = get_link_list(ico_list)
        date_list = get_engagement_date(full_name,link_list)

        if company_list:
            st.success(f"{len(company_list)} records found:")
            i=0
            for one_name, one_ico,one_activity,one_date in zip(company_list, ico_list,activity_list,date_list):
                i=i+1
                st.write(f"{i}\\) The person is active at {one_name} (IČO: {one_ico}) since {one_date}.")
                st.write(f"The company is active at {one_activity}.")
        else:
            st.warning("No record found.")

elif page == "Soubory":
    st.title("Správa souborů")
    st.subheader("Zde můžete nahrávat a spravovat své soubory.")
    uploaded_files = st.file_uploader("Nahrajte soubor", accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"Nahraný soubor: {uploaded_file.name}")

elif page == "Analýza":
    st.title("Analýza klienta")
    st.subheader("V této sekci můžete analyzovat údaje o klientech.")
    st.write("Tato sekce je zatím ve vývoji.")


st.markdown("""
<style>
    .stRadio label {
        display: flex;
        align-items: center;
        padding: 8px;
        border-radius: 8px;
        transition: background-color 0.3s ease;
    }

    .stRadio label:hover {
        background-color: #f0f0f0;
    }

    .stRadio label div[role="radiogroup"] {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
    }

    .stRadio label div[role="radiogroup"] svg {
        width: 24px;
        height: 24px;
    }

    .stRadio div[data-baseweb="radio"] input[type="radio"] {
        transform: scale(1.3);
        margin-right: 10px;
    }

    .stRadio div[data-baseweb="radio"] input[type="radio"]:checked {
        background-color: #4CAF50;
        border-color: #4CAF50;
    }

    .stRadio div[data-baseweb="radio"] input[type="radio"]:checked + div {
        background-color: #4CAF50;
        border-color: #4CAF50;
    }

    .stRadio div[data-baseweb="radio"] input[type="radio"]:checked + div::before {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)
