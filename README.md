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
 
## Needs

- numpy
- scipy
- mongodb
- redis