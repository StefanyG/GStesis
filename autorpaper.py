import re
import sqlite3
import sys
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium import webdriver
import time
import datetime
import csv
import urllib.parse
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options

session = requests.session()
session.proxies = {'http':  'socks5://127.0.0.1:9050',
                   'https': 'socks5://127.0.0.1:9050'}
print (session.get("http://httpbin.org/ip").text)

URL = "http://api.proxiesapi.com"
auth_key = "9164c25943cea098614a01a123f7c55c_sr98766_ooPq87"
url = "http://httpbin.org/anything"
use_headers = "true"
headers = {'My-Custom-Header': 'MY custom header data',}
PARAMS = {'auth_key': auth_key, 'url': url, 'use_headers': use_headers}
r = requests.get(url=URL, params=PARAMS, headers=headers)

#chrome_path = r"chromedriver.exe"
#driver = webdriver.Chrome(chrome_path)
chrome_options = Options()
chrome_options.add_argument("--headless")
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)
# driver = webdriver.Chrome(executable_path='<path-to-chrome>', options=options)
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--proxy-server='direct://'")
chrome_options.add_argument("--proxy-bypass-list=*")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--allow-running-insecure-content')
wait = W(driver, 1)
papers = []
try:
    conn = sqlite3.connect('scholar.db')
except:
    print("No connection")
    sys.exit(0)

cur = conn.cursor()
cur2 = conn.cursor()

cur2.execute("""ALTER table Autor ADD COLUMN Año_Desde INTEGER""")
cur2.execute("""ALTER table Autor ADD COLUMN Hindex_todo INTEGER """)
cur2.execute("""ALTER table Autor ADD COLUMN Hindex_Desde INTEGER  """)
cur2.execute("""ALTER table Autor ADD COLUMN Todas_Citas INTEGER  """)
cur2.execute("""ALTER table Autor ADD COLUMN Citas_Desde INTEGER """)
cur2.execute("""ALTER table Autor ADD COLUMN Id_Institucion TEXT """)

cur.execute("""CREATE TABLE IF NOT EXISTS Autor_Paper (
                                 A_id INTEGER PRIMARY KEY,
                                 Paper_Id TEXT NOT NULL,
                                 AutorPaper_Id TEXT NOT NULL,
                                 Autor_Id TEXT NOT NULL,                                                               
                                 Titulo_Paper TEXT NOT NULL,
                                 Autores_Paper TEXT NOT NULL,
                                 Revista TEXT NOT NULL,
                                 Revista_sp TEXT NOT NULL,
                                 Revista_m TEXT NOT NULL,          
                                 Citado_Por TEXT NOT NULL,
                                 Año TEXT NOT NULL,                                                  
                                 Link_Paper TEXT NOT NULL
                                 )""")
cur.execute("""CREATE TABLE IF NOT EXISTS Coautores (
                                 Id INTEGER PRIMARY KEY,
                                 Coautor_Id TEXT,
                                 Coautor TEXT,
                                 Institucion TEXT,                               
                                 Dominio TEXT,
                                 A_Id TEXT
                                 )""")
cur.execute("""CREATE TABLE IF NOT EXISTS Citas (
                                 id INTEGER PRIMARY KEY,    
                                 Autor_Id TEXT,
                                 Year_hist TEXT,
                                 Citas_hist TEXT
                                 )""")
# cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_citas ON Citas (Autor_Id)""")
# cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_coautores ON Coautores (A_Id)""")
conn.commit()

urls = []
with open(r'Autor.csv', 'r') as f:
    for line in f:
        urls.append(line)

for url in urls:
    try:
        driver.get(url)
        more = driver.find_element_by_class_name('gs_btnPD')
        for _ in range(0, 5):
            ActionChains(driver).click(more).perform()
            time.sleep(1)
    except:
        continue
    start_timing = datetime.datetime.now()
    start_time = time.time()

    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        citation_indices = soup.find('table', attrs={'id': 'gsc_rsb_st'})
        research_article = soup.find_all('tr', {'class': 'gsc_a_tr'})
        author_details = soup.find('div', {'id': 'gsc_prf_i'})
        article = soup.find('tr', {'class': 'gsc_a_tr'})
        coauthors = soup.find('ul', class_='gsc_rsb_a')
        yearshist = soup.findAll('span', class_='gsc_g_t')
        citashist = soup.findAll('span', class_='gsc_g_al')
        time.sleep(1)
        try:
            for coautho in coauthors:
                nameco = coautho.find('a', attrs={'tabindex': '-1'})
                coautor = nameco.text or ''
                l = nameco.get('href')
                c = l.split('=')[1]
                idco = c.split('&')[-2] or ''
                inst = coautho.find('span', attrs={'class': 'gsc_rsb_a_ext'}).text or ''
                dom = coautho.find(class_='gsc_rsb_a_ext gsc_rsb_a_ext2').get_text()
                verified, emai, at, univ = dom.split() or ''
                idpaper = article.find('a', attrs={'class': 'gsc_a_at'})
                d = idpaper.get('data-href')
                linkpaper = urllib.parse.urljoin("https://scholar.google.com", d)
                parsed = urllib.parse.urlparse(d)
                idp = linkpaper.split(':')[-1]  # id paper
                idp_a = linkpaper.split('=')[-1]  # id paper-autor
                id_a = idp_a.split(':')[-2]
                coa = [idco, coautor, inst, univ, id_a]
                print(id_a)
                print(coautor)
                cur.execute('''INSERT OR IGNORE INTO Coautores (Coautor_Id, Coautor,Institucion, Dominio, A_Id) VALUES 
                (?, ?, ?, ?, ?)''',coa)
        except:
            pass
        try:
            for yearh, citah in zip(yearshist, citashist):
                idpaper = article.find('a', attrs={'class': 'gsc_a_at'})
                d = idpaper.get('data-href')
                linkpaper = urllib.parse.urljoin("https://scholar.google.com", d)
                parsed = urllib.parse.urlparse(d)
                idp = linkpaper.split(':')[-1]  # id paper
                idp_a = linkpaper.split('=')[-1]  # id paper-autor
                id_a = idp_a.split(':')[-2]
                yh = yearh.text or ''
                ch = citah.text or ''
                print(yh, ch)
                cur.execute(
                    '''INSERT OR IGNORE INTO Citas (Autor_Id, Year_hist, Citas_hist) VALUES (?, ?, ?)''',
                    (id_a, yh, ch))
            conn.commit()
        except:
            pass
        try:
            for i, research in enumerate(research_article, 1):
                # nombre perfil
                link = author_details.find('a', attrs={'class': 'gsc_prf_ila'})
                l = link.get('href')
                # li = urllib.parse.urljoin("https://scholar.google.com", l)
                id_u = l.split('=')[-1] or ''
                name = author_details.find('div', attrs={'id': 'gsc_prf_in'}).text
                name_attributes = author_details.find_all('div', attrs={'class': 'gsc_prf_il'})
                affiliation = name_attributes[0].text or ''
                interests = name_attributes[2].text or ''
                email = name_attributes[1].text or ''
                # print(name, affiliation, interests, email)

                # tabla citaciones
                year_since_text = citation_indices.find_all('tr')[0]
                citations = citation_indices.find_all('tr')[1]
                h_index = citation_indices.find_all('tr')[2]
                year_since = re.sub('Since ', '', year_since_text.find_all('th')[-1].text) or 0
                h_index_all = h_index.find_all('td')[1].text or 0
                h_index_since = h_index.find_all('td')[2].text or 0
                citation_all = citations.find_all('td')[1].text or 0
                citation_since = citations.find_all('td')[2].text or 0
                # print(year_since, h_index_all, h_index_since, citation_all, citation_since)

                # tabla con papers
                pub_details = research.find('td', attrs={'class': 'gsc_a_t'})
                pub_ref = pub_details.a['href']
                pub_meta = pub_details.find_all('div')
                title = pub_details.a.text or ''
                authors = pub_meta[0].text or ''
                journal = pub_meta[1].text or ''
                j = re.sub(r'([^a-zA-Z ]+?)', '', journal)
                nj = j.lower() or ''
                cited_by = research.find('a', attrs={'class': 'gsc_a_ac'}).text or ''
                year = research.find('span', attrs={'class': 'gsc_a_h'}).text or ''
                idpaper = research.find('a', attrs={'class': 'gsc_a_at'})
                d = idpaper.get('data-href')
                linkpaper = urllib.parse.urljoin("https://scholar.google.com", d)
                parsed = urllib.parse.urlparse(d)
                idp = linkpaper.split(':')[-1] or ''  # id paper
                idp_a = linkpaper.split('=')[-1] or ''  # id paper-autor
                # id_a = url.split('=')[-1]  # id autor
                id_a = idp_a.split(':')[-2] or ''
                print(title)

                mydata = ([idp, idp_a, id_a, title, authors, j, journal, nj, cited_by, year, linkpaper])


                cur.execute("""INSERT OR IGNORE INTO Autor_Paper (Paper_Id, AutorPaper_Id, Autor_Id, Titulo_Paper, 
                Autores_Paper, Revista, Revista_sp, Revista_m, Citado_Por, Año, Link_Paper) VALUES (?, ?, ?, ?, ?, ?, ?,
                 ?, ?, ?, ?)""", mydata)

                cur2 = conn.cursor()
                for row in cur.execute('SELECT * FROM Autor'):
                    cur2.execute('''UPDATE Autor SET Año_Desde=?, Hindex_todo=?, Hindex_Desde=?, Todas_Citas=?, 
                                                    Citas_Desde=?, Id_Institucion=? WHERE Id_A= ?''',
                                 (year_since, h_index_all, h_index_since,
                                  citation_all, citation_since, id_u, id_a))
                    

                conn.commit()
                # print(f'Data inserted: {title}')

        except AssertionError:
            raise Exception("Incorrect arguments were parsed to the function; please revisit your inputs")
        except requests.HTTPError:
            raise Exception("Google may have blocked the search; try running the search from a different IP address,"
                            "connecting to a different network, or using a VPN")
        except requests.RequestException:
            raise Exception("Connection issue detected; please check your internet connection")
        except:
            pass

        if len(research_article) != 0:
            print(f'Page {url} scraped')
            break

    end_time = time.time()
    print("This page took: " + str(end_time - start_time) + " seconds!")

    with open('resultadosperfil.txt', 'a', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow(
            [f'Página {url} empezó a las: ' + str(time.strftime('%H:%M - %d/%m/%Y')) + "" + " y el scrape tomó: " + str(
                end_time - start_time) + " segundos"])

print("*** {} urls scraped ***".format(len(urls)))
driver.quit()
