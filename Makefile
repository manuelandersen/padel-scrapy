.PHONY: extract

SPIDER = gamespider

extract: 
	cd padelscraper/padelscraper && scrapy crawl $(SPIDER) -a start_url="https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/1?t=tol" -a days_played=8 -O test.json

