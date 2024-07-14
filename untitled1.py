import pandas as pd
import numpy as np
import json

# Excel dosyasının yolunu belirtin
excel_path = 'table.xlsx'

# Excel dosyasını okuyun
excel_file = pd.ExcelFile(excel_path)

# Tüm sayfaları bir listeye yükleyin
dfs = [pd.read_excel(excel_file, sheet_name=sheet,header=None) for sheet in excel_file.sheet_names]
combined_df = pd.concat(dfs, axis=0, ignore_index=True)
datas=combined_df.values.tolist()
newdatas=[]
for i in datas:
    ccode=i[1].split(' ')[0]
    newdatas.append([0,ccode,i[4],224])
import xmlrpc.client
import requests
#%%

url = 'http://localhost:8069'
db = 'denemedbbb'
username = 'ertugruloney96@gmail.com'
password = 'deneme'

# Oturum açma
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

# Nesneye erişim
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
partners = models.execute_kw(db, uid, password, 'res.country.state', 'search_read', [[]], {'fields': ['name', 'code','country_id']})

newdatas2=[]
for i in newdatas:
    for j in partners:
        if i[3]==j['country_id'][0]:
            if i[1]==j['code']:
                i[0]=j['id']
                newdatas2.append(i)
            
        



for i in newdatas2:
    partner_id = models.execute_kw(db, uid, password, 'tax.office', 'create', [{
        'name': i[2],
        'country_name':224,
        'state_id':int(i[0])
    }])

'''
# Tüm tax.office kayıtlarını bul
office_ids = models.execute_kw(db, uid, password, 'tax.office', 'search', [[]])

if office_ids:
    # Tüm tax.office kayıtlarını sil
    result = models.execute_kw(db, uid, password, 'tax.office', 'unlink', [office_ids])
    print(f"{len(office_ids)} records deleted.")
else:
    print("No records found to delete.")
'''