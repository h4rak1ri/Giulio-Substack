import requests
from readability import Document  # pip install readability-lxml
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import time  # Import the time module for tracking elapsed time
import os  # To check if the TimeReport.json file exists

###############################################################
# Creazione delle funzioni necessarie
def remove_indent(text):
    text = text.replace(r"\n", " ").replace(r"\r", " ").replace(r"\'", "'").replace(r"\t", " ").replace(r"\"", "'")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def remove_refuses(base_text, start, end):
    text = re.sub(r'^.*?' + re.escape(start), start, base_text, flags=re.DOTALL)
    text = re.sub(r'(' + re.escape(end) + r').*', r'\1', text, flags=re.DOTALL)
    return text

def scraping(link):
    try:
        # Estrae il codice HTML dal sito
        response = requests.get(link)
        response.raise_for_status()  # Raise an error for bad HTTP status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {link}: {e}")
        return None  # Handle error appropriately

    doc = Document(response.content)
    rawText = doc.content()
    title = doc.short_title()

    # Estrazione della data (current date)
    date = datetime.now().strftime("%Y-%m-%d")

    # Rimuove tutti gli elementi HTML
    soup = BeautifulSoup(rawText, 'html.parser')
    text_only = soup.get_text()

    # Sostituisce le indentazioni e i caratteri non conformi
    text_only = remove_indent(text_only)
    title = remove_indent(title)

    # If the content indicates a subscription requirement, stop
    if "Abbonati per leggere anche" in text_only:
        return None

    popUpStart = "minuti di lettura"
    popUpEnd = "Leggi i commenti"
    start_index = text_only.find(popUpStart)
    end_index = text_only.find(popUpEnd)

    if start_index != -1 and end_index != -1:
        news = text_only[start_index + len(popUpStart):end_index]
    else:
        news = text_only  # Fallback if popUpStart or popUpEnd are not found

    last_dot_index = news.rfind(".")
    if last_dot_index != -1:
        news = news[:last_dot_index + 1]

    # Crea un dizionario contenente le informazioni principali
    news_dict = {
        "Title": title,
        "Source": "Repubblica",
        "Date": date,
        "Link": link,
        "Content": news.strip()
    }

    if "b' Abbonati Menu" in news_dict["Content"][:20]:
        return None

    print("estrazione contenuto")

    return news_dict

###############################################################
# Funzione per registrare e stampare messaggi con il tempo trascorso
def record_time(message, last_time, dTime, source, start_time, controllo_start_time=None):
    current_time = time.perf_counter()
    elapsed_time = current_time - last_time

    if message == "fine script":
        # Calcola il tempo totale dall'inizio dello script
        total_elapsed = current_time - start_time
        dTime[source]["Fine"].append(total_elapsed)
    elif message == "fine estrazione link":
        # Tempo per l'estrazione dei link
        dTime[source]["Estrazione"].append(elapsed_time)
    elif message == "fine controllo link":
        # Tempo totale per il controllo dei link
        if controllo_start_time is not None:
            controllo_total_time = current_time - controllo_start_time
            dTime[source]["Controllo totale"].append(controllo_total_time)
        else:
            dTime[source]["Controllo totale"].append(elapsed_time)
    elif message == "link controllato":
        # Tempo per il controllo di ogni singolo link
        dTime[source]["Singolo controllo"].append(elapsed_time)
    elif message == "count":
        # Numero di link controllati
        dTime[source]["Count"].append(int(elapsed_time))
    else:
        # Altri messaggi (se presenti)
        pass

    print(message)
    print(f"Time since last checkpoint: {elapsed_time:.6f} seconds\n")
    return current_time

###############################################################
# Inizializza il timer e il dizionario per i tempi
start_time = time.perf_counter()
last_checkpoint = start_time  # Tieni traccia dell'ultimo checkpoint

# Nome del sito corrente
current_site = "Repubblica"

# Carica o inizializza il dizionario dei tempi
time_report_file = "TimeReport.json"

if os.path.exists(time_report_file):
    with open(time_report_file, "r", encoding="utf-8") as f:
        try:
            time_data = json.load(f)
        except json.JSONDecodeError:
            # Se il file esiste ma non è un JSON valido, inizializza un nuovo dizionario
            time_data = {}
else:
    time_data = {}

# Inizializza la sezione per il sito corrente se non esiste
if current_site not in time_data:
    time_data[current_site] = {
        "Estrazione": [],
        "Singolo controllo": [],
        "Controllo totale": [],
        "Fine": [],
        "Count": []
    }

dTime = time_data  # Alias per comodità

###############################################################
# Estrazione dei link dalla homepage

# variabili esterne
filtered_links = []
lTag = ["esteri", "politica", "economia", "sport", "cronaca", "scuola", "salute"]  
for tag in lTag:
    sito = "https://www.repubblica.it"
    root_link = sito + "/" + tag + "/"
    file_path = "Repubblica/Repubblica.json"

    # Accesso al contenuto HTML della homepage per la sezione corrente
    try:
        response = requests.get(root_link)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching homepage {root_link}: {e}")
        continue  # Skip to the next tag

    homepage = Document(response.content)
    rawText = homepage.content()

    # Sostituzione caratteri non conformi
    home_text_only = remove_indent(rawText)

    # Mantiene solo gli elementi cliccabili
    soup = BeautifulSoup(home_text_only, 'html.parser')
    home_links = soup.find_all('a')
    hrefs = [link.get('href') for link in home_links if link.get('href')]

    # Regex per cercare gli elementi dentro i due slash
    tags_pattern = '|'.join(lTag)
    pattern = rf'^https?://[^/]+/({tags_pattern})/'

    for link in hrefs:
        match = re.search(pattern, link)
        if match:
            temp_tag = match.group(1)
            if temp_tag == tag:
                filtered_links.append(link)

filtered_links = list(set(filtered_links))

# Filter out links that do not end with '/'
filtered_links = [link for link in filtered_links if link.endswith('/')]

# Stampa e registra il tempo dopo l'estrazione dei link
last_checkpoint = record_time("fine estrazione link", last_checkpoint, dTime, current_site, start_time)

###############################################################
# Controllo errori nel link

# Inizia a misurare il tempo totale per il controllo dei link
controllo_start_time = time.perf_counter()

# Inizializza il contatore dei link controllati
links_checked = 0

for i in range(len(filtered_links) - 1, -1, -1):
    link = filtered_links[i]
    
    try:
        response = requests.get(link)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching link {link}: {e}")
        del filtered_links[i]
        continue

    if "/diretta/" in link or "/video/" in link:
        del filtered_links[i]
        continue

    doc = Document(response.content)
    rawTitle = remove_indent(doc.short_title())
    
    try:
        with open("Repubblica/Repubblica.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {"news": []}
    
    if any(link_item["Link"] == link or link_item["Title"] == rawTitle for link_item in data.get("news", [])):
        del filtered_links[i]
        continue

    # Incrementa il contatore dei link controllati
    links_checked += 1

    # Stampa e registra il tempo dopo il controllo di ogni link
    last_checkpoint = record_time("link controllato", last_checkpoint, dTime, current_site, start_time)

# Calcola e registra il tempo totale per il controllo dei link
last_checkpoint = record_time("fine controllo link", controllo_start_time, dTime, current_site, start_time)

# Appende il numero di link controllati
dTime[current_site]["Count"].append(links_checked)

print(f"Numero di link controllati: {links_checked}\n")

###############################################################
# Crea il dizionario con le informazioni

for link in filtered_links:
    news_dict = scraping(link)
    if news_dict is None:
        continue  # Skip if scraping returned None

    try:
        with open("Repubblica/Repubblica.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {"news": []}

    # Ensure the "news" key exists and append the new item
    data.setdefault("news", []).append(news_dict)

    # Write back to the file
    with open("Repubblica/Repubblica.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

filtered_links = []

# Stampa e registra il tempo alla fine dello script
last_checkpoint = record_time("fine script", last_checkpoint, dTime, current_site, start_time)

###############################################################
# Salva il dizionario dei tempi in un file JSON
with open("TimeReport.json", "w", encoding="utf-8") as f:
    json.dump(time_data, f, ensure_ascii=False, indent=4)

# (Opzionale) Stampa il dizionario dei tempi
print("Dizionario dei tempi:", json.dumps(time_data, indent=4))
