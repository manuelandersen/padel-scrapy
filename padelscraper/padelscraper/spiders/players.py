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
        players_1_10 = response.xpath('//div[@class="slider__item"]')
        players_1_10_urls = players_1_10.xpath('.//h2[@class="slider__name"]/a/@href').getall()
        
        # Players from 11 to 20 in ranking
        players_11_20 = response.css('.playerGrid__item')
        players_11_20_url = players_11_20.css('.playerGrid__name a::attr(href)').getall() 

        # Players from 21 to 40 in ranking
        players_21_40 = response.css('.data-body-row')
        players_21_40_url = players_21_40.css('td.data-body-cell.data-player-img-name .data-title-container a::attr(href)').getall()


        players_url = players_1_10_urls + players_11_20_url + players_21_40_url
        
        for player_url in players_url:

            yield response.follow(player_url, self.parse_player_url)


    def parse_player_url(self, response):

        attributes = {}

        attributes["ranking"] = response.xpath('//span[@class="slider__number player__number"]/text()').get().strip()
        attributes["name"] = response.xpath('//h2[@class="slider__name player__name"]/text()').get()
        attributes["country"] = response.xpath('//p[@class="slider__country player__country"]/text()').get()
        attributes["points"] = response.xpath('//span[@class="slider__pointTNumber player__pointTNumber"]/text()').get()

        yield {
            **attributes
        }