## padel-scrapy

This is a project to scrap data from the [International Padel Federation](https://www.padelfip.com/es/) page. It collects players, tourneys and games information into JSON files.

## Installation

1)  Clone the repository

``` bash
git clone https://github.com/manuelandersen/padel-scrapy.git
cd padel-scrapy
```

2)  Create a virtual environment (optional but recommended):

``` bash
python3 -m venv venv
source venv/bin/activate
```

3)  Install the dependencies:

``` bash
pip install -r requirements.txt
```

## Running the spiders

``` console
# you need to be inside the padelscraper directory
cd padelscraper

# to run player spider
scrapy crawl playerspider 

# to run tournament spider
scrapy crawl tournamentspider

# to run games spider you need to give it a url and the numbers of days played
# this info can be obtained from the tournamentspider results
scrapy crawl gamespider -a start_url="the_star_url" -a days_played=days_played

# if you want to store the json file 
scrapy crawl playerspider -O path_to_file.json
```

If you dont wanna create a virtual environment you can use Docker:

``` console
# to build the containe
docker build -t scrapy-project .

# to run one of the spiders
docker run scrapy-project scrapy crawl tournamentspider
``` 

## Examples

Examples of the way the data look for each spider can be found in the `examples` folder.

## Contributions

We welcome contributions to improve and expand this project! Whether you're fixing a bug, adding a new feature, or improving documentation, your help is appreciated.