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

## Usage
 
 
- For teaching urls
 `GET /teach?url=<path-to-url>`
 
- For getting one of the closest neighbors of given url
 `GET /neighbor?url=<url-id>`

- Authenticate a new client
 `POST /authenticate {}`
 `returns {token: <access token>}`

- Get a suggestion
 `GET /next?token=<access_token>`
 `returns a response according to your likes`

- Like an article
 `POST /like?token=<access_token> {id: <article_id>}`


## Needs

- numpy
- scipy
- mongodb
- redis
- embedly account for extracting kw's