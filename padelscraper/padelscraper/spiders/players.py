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

        # Players from 1 to 10 in ranking
#        ranks = response.xpath('//span[@class="slider__number"]/text()')
#        for i in range(0,10):
#            yield {
#                'ranking' : ranks[i].get().strip()
#            }

        players_1_10 = response.xpath('//div[@class="slider__item"]')

        for player in players_1_10:
            yield {
                'ranking': player.xpath('.//span[@class="slider__number"]/text()').get().strip(),
                'name': player.xpath('.//h2[@class="slider__name"]/a/@title').get(),
                'url': player.xpath('.//h2[@class="slider__name"]/a/@href').get(),
                'country': player.xpath('.//p[@class="slider__country"]/text()').get().strip(),
                'points': player.xpath('.//span[@class="slider__pointTNumber"]/text()').get()
            }

        # Players from 11 to 20 in ranking
        players_11_20 = response.css('.playerGrid__item')
        
        for player in players_11_20:
            yield {
                'ranking' : player.css('.playerGrid__number::text').get().strip(),
                'name' : player.css('.playerGrid__name a::attr(title)').get(),
                'url' : player.css('.playerGrid__name a::attr(href)').get(),
                'country' : player.css('.playerGrid__country::text').get(),
                'points' : player.css('.playerGrid__pointTNumber::text').get()
            }

         # Players from 21 to last in ranking
        players_21_60 = response.css('.data-body-row')

        for player in players_21_60:
            yield {
                'ranking' : player.css('td.data-body-cell.data-rank-cell p::text').get().strip(),
                'name' : player.css('td.data-body-cell.data-player-img-name .data-title-container a::text').get(),
                'url' : player.css('td.data-body-cell.data-player-img-name .data-title-container a::attr(href)').get(),
                'country' : player.css('td.data-body-cell.flag-country .country-name::text').get(),
                'points' : player.css('td.data-body-cell.data-points p::text').get() 
            }

