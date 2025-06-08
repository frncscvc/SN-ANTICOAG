import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import rispy
import io
import uuid
from datetime import datetime

st.set_page_config(page_title="SN-ANTICOAG Screening", layout="wide")
st.title("📚 SN-ANTICOAG - Revisión Sistemática")

# Función para leer archivos RIS
def load_ris(file):
    entries = rispy.load(file)
    return pd.DataFrame(entries)

# Función para leer archivos XML (PubMed)
def load_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    articles = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        title = article.findtext(".//ArticleTitle")
        abstract = article.findtext(".//Abstract/AbstractText")
        journal = article.findtext(".//Journal/Title")
        year = article.findtext(".//Journal/JournalIssue/PubDate/Year")
        authors = article.findall(".//Author")
        author_list = []
        for a in authors:
            last = a.findtext("LastName")
            fore = a.findtext("ForeName")
            if last and fore:
                author_list.append(f"{fore} {last}")
        articles.append({
            "PMID": pmid,
            "Título": title,
            "Resumen": abstract,
            "Autores": ", ".join(author_list),
            "Revista": journal,
            "Año": year
        })
    return pd.DataFrame(articles)

# Función para leer archivos TXT estilo PubMed MEDLINE
def load_txt_medline(file):
    content = file.read().decode("utf-8")
    records = content.split("\n\n")
    data = []
    for record in records:
        lines = record.strip().split("\n")
        entry = {"PMID": "", "Título": "", "Resumen": "", "Autores": "", "Revista": "", "Año": ""}
        authors = []
        for line in lines:
            if line.startswith("PMID-"):
                entry["PMID"] = line.replace("PMID- ", "").strip()
            elif line.startswith("TI  -"):
                entry["Título"] += line.replace("TI  - ", "").strip() + " "
            elif line.startswith("AB  -"):
                entry["Resumen"] += line.replace("AB  - ", "").strip() + " "
            elif line.startswith("AU  -"):
                authors.append(line.replace("AU  - ", "").strip())
            elif line.startswith("TA  -") or line.startswith("JT  -"):
                entry["Revista"] = line[6:].strip()
            elif line.startswith("DP  -"):
                entry["Año"] = line.replace("DP  - ", "").strip().split(" ")[0]
        entry["Autores"] = ", ".join(authors)
        data.append(entry)
    return pd.DataFrame(data)

# Subida de archivo
st.sidebar.header("Carga de datos")
file = st.sidebar.file_uploader("Sube un archivo (.xml, .ris, .csv, .txt MEDLINE)", type=["xml", "ris", "csv", "txt"])

if file:
    if file.name.endswith(".xml"):
        df = load_xml(file)
    elif file.name.endswith(".ris"):
        df = load_ris(file)
    elif file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith(".txt"):
        df = load_txt_medline(file)
    else:
        st.error("Formato de archivo no reconocido.")
        st.stop()

    df = df.dropna(subset=["Título", "Resumen"]).reset_index(drop=True)
    st.success(f"{len(df)} estudios cargados.")
    st.session_state.df = df

# Identificación de revisor
st.sidebar.header("Identificación del revisor")
user_email = st.sidebar.text_input("Correo electrónico")
user_name = st.sidebar.text_input("Nombre de pila")

if "df" in st.session_state and user_email and user_name:
    df = st.session_state.df
    idx = st.session_state.get("study_index", 0)

    if idx < len(df):
        st.markdown(f"""### Estudio {idx + 1} de {len(df)}""")
        st.write(f"**Título:** {df.loc[idx, 'Título']}")
        st.write(f"**Resumen:** {df.loc[idx, 'Resumen']}")
        st.write(f"**Autores:** {df.loc[idx, 'Autores']}")
        st.write(f"**Revista:** {df.loc[idx, 'Revista']}")
        st.write(f"**Año:** {df.loc[idx, 'Año']}")

        decision = st.radio("Decisión:", ["Incluir", "Excluir", "Duda"], horizontal=True)
        criterios = []
        if decision == "Excluir":
            criterios = st.multiselect("Criterios de exclusión:", ["No es en adultos", "No es síndrome nefrótico", "No trata anticoagulación", "No es prospectivo/randomizado"])
        comentario = st.text_area("Comentario (opcional)")

        if st.button("Guardar y siguiente"):
            st.session_state.decisions.append({
                "Revisor": user_name,
                "Email": user_email,
                "PMID": df.loc[idx, "PMID"],
                "Título": df.loc[idx, "Título"],
                "Decisión": decision,
                "Criterios": "; ".join(criterios),
                "Comentario": comentario,
                "Fecha": datetime.now().isoformat()
            })
            st.session_state.study_index += 1
            st.experimental_rerun()
    else:
        st.success("✅ Has revisado todos los estudios.")
        if st.download_button("Descargar decisiones en Excel", data=pd.DataFrame(st.session_state.decisions).to_csv(index=False).encode("utf-8"), file_name="decisiones.csv"):
            st.balloons()