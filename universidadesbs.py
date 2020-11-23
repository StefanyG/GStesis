import sqlite3
import sys
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import datetime
import csv
import urllib.parse
from selenium.common import exceptions as SE
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC
from csv import writer

USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/61.0.3163.100 Safari/537.36'}

# Se abre el navegador Chrome en modo headless (fantasma)
chrome_options = Options()
chrome_options.add_argument("--headless")
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(executable_path='<path-to-chrome>', options=options)

results = []
button_locators = "//button[@class='gs_btnPR gs_in_ib gs_btn_half gs_btn_lsb gs_btn_srt gsc_pgn_pnx']"
wait = W(driver, 2)

# Se abren las urls que se encuentran almacenadas en un archivo csv
urls = []
with open(r'urlspages.csv', 'r') as f:
    for line in f:
        urls.append(line)

# Se crea un loop y con Selenium se obtiene la url y se encuentra el boton para avanzar a la siguiente página
for url in urls:
    data = {}
    driver.get(url)
    button_link = wait.until(EC.element_to_be_clickable((By.XPATH, button_locators)))
    start_time = time.time()
    start_timing = datetime.datetime.now()
    response = requests.get(url, headers=USER_AGENT)
    response.raise_for_status()

    while button_link:
        try:
            wait.until(EC.visibility_of_element_located((By.ID, 'gsc_sa_ccl')))
            # Se analiza y prepara el HTML
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            posts = soup.find_all('div', attrs={'class': 'gsc_1usr'})
            time.sleep(2)
            
            # Se crea un archivo csv para guardar las urls de los perfiles 
            with open('Autor.csv', 'a', encoding="utf-8", newline='') as s:
                csv_writer = writer(s)
                
            # Se crea la conexión a la base de datos
            try:
                conn = sqlite3.connect('scholar.db')
                
            except:
                print("No connection")
                sys.exit(0)
            # Se crea si no existe, la tabla de autor en la base de datos
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS Autor (
                                 Id_A TEXT PRIMARY KEY,
                                 Nombre_Autor TEXT NOT NULL,
                                 Cargo TEXT NOT NULL,
                                 Email TEXT NOT NULL,
                                 Citaciones TEXT NOT NULL,
                                 Intereses TEXT NOT NULL,
                                 Links TEXT NOT NULL
                                 )""")
             # Se obtienen los datos del autor 
            for post in posts:
                linkfoto = post.find('a', attrs={'class': 'gs_ai_pho'})
                l = linkfoto.get('href')
                link = urllib.parse.urljoin("https://scholar.google.com", l)
                idautor = link.split('=')[-1]
                nombre = post.find(class_='gs_ai_name').get_text().replace('\n', '')
                uni = post.find(class_='gs_ai_aff').get_text().replace('\n', '')
                try:
                    mail = post.find(class_='gs_ai_eml').get_text().replace('\n', '')
                    verified, email, at, univ = mail.split()
                    cite = post.find(class_='gs_ai_cby').get_text().replace('\n', '')
                    cited, by, citas = cite.split()
                except:
                    citas = 0
                    univ = ''
                tags = post.find(class_='gs_ai_int').get_text().replace('\n', '')            
                mydata = ([idautor, nombre, uni, univ, citas, tags, link])
                # Se guarda el link del autor en el csv
                csv_writer.writerow([link])

                results.append(mydata)
                # Se guardan los datos en la base de datos 
                cursor.executemany("""INSERT OR IGNORE INTO Autor (Id_A, Nombre_Autor, Cargo, Email, 
                Citaciones, Intereses, Links) VALUES (?, ?, ?, ?, ?, ?,?)""", [mydata])
                conn.commit()
                

            button_link = wait.until(EC.element_to_be_clickable((By.XPATH, button_locators)))
            button_link.click()
            time.sleep(2)

        except SE.TimeoutException:
            print(f'Página parseada {url}')
            break
    end_time = time.time()
    print("This page took: " + str(end_time - start_time) + " seconds!")

    with open('resultadosuniversidades.txt', 'a', newline='') as fd:
        writer = csv.writer(fd)
        writer.writerow([f'Página {url} empezó a las: ' + str(time.strftime('%H:%M - %d/%m/%Y')) +
                         " y el scrape tomó: " + str(end_time - start_time) + " segundos"])

print("*** {} urls scraped ***".format(len(urls)))
driver.quit()
