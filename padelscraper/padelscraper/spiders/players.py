import scrapy


class PlayerSpider(scrapy.Spider):
    name = "playerspider"
    allowed_domains = ["padelfip.com"]
    start_urls = ["https://www.padelfip.com/es/ranking-masculino/"]


    """
    There is like a 3 part rankings in the page:

    1. section_sliderHomeWrap : this looks like is only for the first 10 players.
    2. section_playerGridWrap : this for the player 11 to 20.
    3. player-table : and this one for 21 to 60, and then you can load more players.

    """

    def parse(self, response):

        players_11_20 = response.css('.playerGrid__item')
        
        for player in players_11_20:
            yield {
                'ranking' : player.css('.playerGrid__number::text').get().strip(),
                'name' : player.css('.playerGrid__name a::attr(title)').get(),
                'url' : player.css('.playerGrid__name a::attr(href)').get(),
                'country' : player.css('.playerGrid__country::text').get(),
                'points' : player.css('.playerGrid__pointTNumber::text').get()
            }

        players_21_60 = response.css('.data-body-row')

        print("****************")
        print(len(players_21_60))
        print("****************")

        for player in players_21_60:
            yield {
                'ranking' : player.css('td.data-body-cell.data-rank-cell p::text').get().strip(),
                'name' : player.css('td.data-body-cell.data-player-img-name .data-title-container a::text').get(),
                'url' : player.css('td.data-body-cell.data-player-img-name .data-title-container a::attr(href)').get(),
                'country' : player.css('td.data-body-cell.flag-country .country-name::text').get(),
                'points' : player.css('td.data-body-cell.data-points p::text').get() 
            }

