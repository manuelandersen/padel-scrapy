import scrapy
import json

class PlayerSpider(scrapy.Spider):
    name = "playerspider"
    allowed_domains = ["padelfip.com"]
    start_urls = ["https://www.padelfip.com/es/ranking-masculino/"]


    """
    There is like a 3 part rankings in the page:

    1. section_sliderHomeWrap : this looks like is only for the first 10 players.
    2. section_playerGridWrap : this for the player 11 to 20.
    3. player-table : and this one for 21 to 40, and then you can load more players.

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
        
        # Players from 41 to last in ranking
        # Find initial "load more" button parameters
        load_more_button = response.css('.loadMoreRanking')
        if load_more_button:
            total_posts = int(load_more_button.attrib['data-total-post'])
            posts_per_page = int(load_more_button.attrib['data-posts-per-page'])
            offset = int(load_more_button.attrib['data-offset'])
            gender = load_more_button.attrib['data-gender']
            category = load_more_button.attrib['data-category']

            # Prepare initial request parameters
            params = {
                'action': 'post_type_infinite',
                'paged': '1',
                'post_type': 'player',
                'posts_per_page': str(posts_per_page),
                'meta_key': 'ranking',
                'taxonomy': 'country',
                'offset': str(offset),
                'total_post': str(total_posts),
                'term': 'gender,player_category',
                'termValue': f'{gender},{category}'
            }

            # Send request to load more data
            yield scrapy.FormRequest(
                url='https://www.padelfip.com/wp-admin/admin-ajax.php',
                formdata=params,
                callback=self.parse_more,
                meta={'params': params, 'total_posts': total_posts}
            )
    
    def parse_more(self, response):
        data = json.loads(response.text)
        # Check if the 'html' key exists and has content
        if 'html' in data and data['html']:
            # Parse the HTML string within the JSON response
            row_selector = scrapy.Selector(text=data['html'])
            player_rows = row_selector.css('.data-body-row')
            for row in player_rows:
                player_url = row.css('td.data-body-cell.data-player-img-name .data-title-container a::attr(href)').get()
                if player_url:
                    yield response.follow(player_url, self.parse_player_url)

        # Check if there are more rows to load
        params = response.meta['params']
        total_posts = response.meta['total_posts']
        offset = int(params['offset']) + int(params['posts_per_page'])
        paged = int(params['paged']) + 1
        if offset < total_posts:
            params['offset'] = str(offset)
            params['paged'] = str(paged)
            yield scrapy.FormRequest(
                url='https://www.padelfip.com/wp-admin/admin-ajax.php',
                formdata=params,
                callback=self.parse_more,
                meta={'params': params, 'total_posts': total_posts}
            )

    def parse_player_url(self, response):

        attributes = {}

        attributes["ranking"] = response.xpath('//span[@class="slider__number player__number"]/text()').get().strip()
        attributes["name"] = response.xpath('//h2[@class="slider__name player__name"]/text()').get()
        attributes["country"] = response.xpath('//p[@class="slider__country player__country"]/text()').get()
        attributes["points"] = response.xpath('//span[@class="slider__pointTNumber player__pointTNumber"]/text()').get()
        attributes["paired_with"] = response.xpath('//span[@class="content"]/a/text()').get()
        attributes["position"] = response.xpath('//div[@class="additionalInfo__hand"]/span[@class="content"]/text()').get()
        attributes["birth_date"] = response.xpath('//div[@class="additionalInfo__birth"]/span[@class="additionalInfo__data"]/text()').get()
        attributes["height"] = response.xpath('//div[@class="additionalInfo__height"]/span[@class="additionalInfo__data"]/text()').get()
        attributes["place_of_birth"] = response.xpath('//div[@class="additionalInfo__born"]/span[@class="additionalInfo__data"]/text()').get().strip()

        residence = response.xpath('//div[@class="additionalInfo__lives"]/span[@class="additionalInfo__data"]/text()').get()
        if residence == "--":
            attributes["residence"] = None
        else:
            attributes["residence"] = residence

        matches_played = response.xpath('//div[@class="matchPlayer__played"]/span/text()').get()
        if matches_played == "--":
            attributes["matches_played"] = None
        else:
            attributes["matches_played"] = matches_played


        matches_won = response.xpath('//div[@class="matchPlayer__won"]/span/text()').get()
        if matches_won == "--":
            attributes["matches_won"] = None
        else:
            attributes["matches_won"] = matches_won

        matches_lost = response.xpath('//div[@class="lost"]/span/text()').get()
        if matches_lost == "--":
            attributes["matches_lost"] = None
        else:
            attributes["matches_lost"] = matches_lost

        consecutive_victories = response.xpath('//div[@class="matchPlayer__victories"]/span/text()').get()
        if consecutive_victories == "--":
            attributes["consecutive_victories"] = None
        else:
            attributes["consecutive_victories"] = consecutive_victories

        effectiveness = response.xpath('//div[@class="matchPlayer__effective"]/span/text()').get()
        if effectiveness == "--":
            attributes["effectiveness"] = None
        else:
            attributes["effectiveness"] = effectiveness
        
        old_position = None
        # Check for oldPosition down
        number_down = response.xpath('//span[contains(@class, "oldPosition down")]/text()').get()
        if number_down:
            old_position = f"-{number_down}"
        # Check for oldPosition up if old_position is not set
        elif old_position is None:
            number_up = response.xpath('//span[contains(@class, "oldPosition up")]/text()').get()
            if number_up:
                old_position = f"+{number_up}"

        attributes["old_position"] = old_position

        # Tournament points
        attributes["points_per_tournament"] = list(self.parse_tournaments_points(response))

        yield {
            **attributes
        }

    def parse_tournaments_points(self, response):
        
        for row in response.css('#data-tournament-table tbody tr'):
            yield self.parse_tournament_points(row)

    def parse_tournament_points(self, row):
        
        tournament = {}

        tournament["tournament_name"] = row.css('.tb-name::text').get()
        tournament["category"] = row.css('.tb-type::text').get()
        tournament["date"] = row.css('.tb-date::text').get()

        round_reached = row.css('.tb-roundName::text').get()
        if round_reached == "-":
            tournament["round_reached"] = None
        else:
            tournament["round_reached"] = round_reached
        
        tournament["points"] = row.css('.tb-points::text').get()

        return tournament