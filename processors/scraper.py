import requests
myurl = ("https://learning.oreilly.com/api/v2/search/?formats=book&query="
         "\"Coldfusion MX 7 Web Application Construction Kit\"")
page = requests.get(myurl).text
print(page)