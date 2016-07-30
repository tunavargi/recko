# Reko

Calculates distance between articles and recommend new articles to read


- Teach some article url's to reko
- Calculates the distance between teached articles according to keywords extracted
- Then get closest neighbors of given articles

## Setup
    
- copy the `config.py.copy` as `config.py`
- change inside according to your config details
- run app.py for flask web server 
- run calculate.py for distance calculating worker

## USAGE
 
 
- For teaching urls
 `GET /teach?url=<path-to-url>`
 
- For getting one of the closest neighbors of given url
 `GET /neighbor?url=<url-id>`

## Needs

- numpy
- scipy
- mongodb
- redis
- embedly account for extracting kw's