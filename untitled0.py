import xmlrpc.client
import requests

url = 'http://localhost:8069'
db = 'denemedb'
username = 'ertugruloney96@gmail.com'
password = 'deneme'

# Oturum açma
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

# Nesneye erişim
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
# 'res.partner' modelinden bazı verileri alın
partners = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[]], {'fields': ['name', 'country_id', 'comment'], 'limit': 5})

partner_id = models.execute_kw(db, uid, password, 'tax.office', 'create', [{
    'name': "deneme2",
    'country_name':224,
}])
print("New partner ID:", partner_id)