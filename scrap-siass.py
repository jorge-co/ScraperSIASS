#!/usr/bin/env python
# coding: utf-8

# # Scrapper para SIASS.UNAM.MX

# ## Dependencias

import pandas as pd
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
pd.set_option('display.max_colwidth',None)

# ## Funciones auxiliares

def get_soup(url):
    response = urlopen(url)
    html_doc = response.read()
    soup=BeautifulSoup(html_doc, 'html.parser')
    return soup

def get_results(tag):
    result=''
    for col in columns:
        if col == tag.get_text():
            result=tag.find_next_sibling('td').get_text()
            return result

# ## Carga de páginas

with open('credenciales.json') as json_file:
    data = json.load(json_file)
# working on Matemáticas Aplicadas y Computación, FES Acatlán
carrera_id = data['carrera_id']
facultad_id =  data['facultad_id']
numero_cuenta = data['numero_cuenta']

main_page = 'http://www.siass.unam.mx/consulta?nombre=&estado_id=0&municipio_id=0&sector=&or=&eje_tematico_id=0&apoyo=&ubicacion=&asistencia=&horario=&carrera_id='+carrera_id+'&facultad_id='+facultad_id+'&numero_cuenta='+numero_cuenta+'&page='

# get pages from pagination 
pages=[]
for page in range(15):
    pages.append(main_page+str(page+1))


# ## Scrapping

columns = ['Institución','Dependencia','Eje de acción','Objetivo','Lugares disponibles',
        'Lista de actividades','Entidad federativa','Delegación / Municipio','Colonia / Localidad',
        'Ubicación del prestador','Notas adicionales','Monto total:']
df = pd.DataFrame(columns = ['Título']+columns+['Apoyos'])

# scrap for each page
for page in range(len(pages)):
    urls=[]
    actual_page = get_soup(pages[page])
    # search for <a> tags in html
    soup_urls = actual_page.find_all('a', {'class':"btn btn-default btn-sm"})
    for url in soup_urls:
        urls.append(url.get_attribute_list('href')[0])
    soups = []
    # look for each subpage
    for url in urls:
        soups.append(get_soup(url))
    # search for each tag in the subpage
    for i in range(len(soups)):
        titulo=soups[i].h3.get_text()
        tags=[]
        row=[]
        apoyos= []
        for tag in soups[i].find_all('th'):
            if tag.get_text() in columns:
                tags.append(tag)
        monto = False
        for tag in tags:
            if tag.get_text() == 'Monto total:':
                monto = True
            if get_results(tag):
                row.append(get_results(tag))
            else:
                row.append('')
        if not monto:
            row.append('')
        for apoyo in soups[i].find_all('h4')[-1].find_next_siblings('p'):
            apoyos.append(apoyo.get_text())
        apoyos=', '.join(apoyos)
        df.loc[len(df)]=[titulo]+row+[apoyos]


# ## Feature engineering

df=df.replace(to_replace=r'\s*[\n]+\s*', value=' ', regex=True)
df['Direccion'] = df['Entidad federativa']+', '+df['Delegación / Municipio']+', '+df['Colonia / Localidad']+', '+df['Ubicación del prestador']
df['Institución']+=', '+df['Dependencia']
df=df.drop(columns=['Entidad federativa','Delegación / Municipio','Colonia / Localidad','Ubicación del prestador','Dependencia'])
df.columns = df.columns.str.replace('Lugares disponibles', '#')
df.rename(columns = {'Lugares disponibles':'#', 'Notas adicionales':'Notas', 'Eje de acción':'Eje'}, inplace = True)
df


# ## Generación de TAD

path = '/home/jorge/Documentos/siass.csv'
df.to_csv(path)