# padel-scrapy

This is a project to scrap data the [International Padel Federation](https://www.padelfip.com/es/) page. It collects players, tourneys and games information into JSON files.

# Installation

1)  Clone the repository

``` bash
git clone https://github.com/manuelandersen/padel-scrapy.git
cd your-repository
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

4)  Run spiders:

``` bash
# you need to be inside the padelscraper directory
cd padelscraper

# to run player spider
scrapy crawl playerspider 

# to run tournament spider
scrapy crawl tournamentspider

# to run games spider you need to give it a url and the numbers of days played
# this info can be obtained from the tournamentspider results
scrapy crawl gamespider -a start_url -a days_played

# if you want to store the json file 
scrapy crawl playerspider -O path_to_file.json
```

# Running the spiders