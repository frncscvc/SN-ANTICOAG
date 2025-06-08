
import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import rispy
import io

def parse_pubmed_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    records = []
    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle", default="")
        abstract = article.findtext(".//AbstractText", default="")
        journal = article.findtext(".//Title", default="")
        year = article.findtext(".//PubDate/Year") or "ND"
        authors = ", ".join(
            f"{a.findtext('LastName')} {a.findtext('Initials')}"
            for a in article.findall(".//Author") if a.find("LastName") is not None
        )
        records.append({
            "Título": title,
            "Resumen": abstract,
            "Revista": journal,
            "Año": year,
            "Autores": authors
        })
    return pd.DataFrame(records)

def parse_ris(file):
    entries = rispy.load(file)
    records = []
    for entry in entries:
        records.append({
            "Título": entry.get("title", ""),
            "Resumen": entry.get("abstract", ""),
            "Revista": entry.get("journal_name", ""),
            "Año": entry.get("year", ""),
            "Autores": ", ".join(entry.get("authors", []))
        })
    return pd.DataFrame(records)

st.title("SN-ANTICOAG - Importador de Estudios")

uploaded_file = st.file_uploader("Sube tu archivo (.xml, .ris, .csv)", type=["xml", "ris", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".xml"):
        df = parse_pubmed_xml(uploaded_file)
    elif uploaded_file.name.endswith(".ris"):
        df = parse_ris(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        st.error("Formato no reconocido.")
        df = None

    if df is not None:
        st.success(f"{len(df)} registros cargados.")
        st.dataframe(df)
