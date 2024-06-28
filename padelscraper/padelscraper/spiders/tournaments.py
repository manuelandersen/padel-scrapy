import scrapy


class TournamentSpider(scrapy.Spider):
    name = "tournamentspider"
    allowed_domains = ["padelfip.com"]
    start_urls = ["https://www.padelfip.com/es/calendario-premier-padel/"]


    def parse(self, response):
        years = [2023, 2024]
        for year in years:
            
            meta = {"year": year}

            url = f"https://www.padelfip.com/es/calendario-premier-padel/?events-year={year}"

            yield response.follow(url, self.parse_year, meta=meta)
        

    def parse_year(self, response):
        year = response.meta['year']
        months = response.css('section.month-section')
        
        for month in months:
            month_name = month.css('h2::text').get()
            events = month.css('article')

            for event in events:
                event_url = event.css('.event-title a::attr(href)').get()
                yield response.follow(event_url, 
                                      self.parse_event, meta={
                                                            'year': year,
                                                            'month': month_name
                                                            }
                )

    def parse_event(self, response):
        year = response.meta['year']
        month = response.meta['month']
        event_name = response.css('h1.event__name::text').get()
        event_place = response.css('span.event__place::text').get()
        event_date = response.css('span.event__date::text').get()
        gender = response.css('.item__gender .section__itemText::text').get()

        qualification_texts = response.xpath('//div[contains(@class, "item__qualification")]//div[@class="section__itemText"]/text()').getall()

        # Extract prize money
        prize_money = response.xpath('//div[contains(@class, "item__priceMoney")]//div[@class="section__itemText"]/text()').get()
        if prize_money:
            prize_money = prize_money.strip()

        # Extract club information
        club_info = response.xpath('//div[contains(@class, "item__club")]//div[@class="section__itemText"]/text()').get()
        if club_info:
            club_info = club_info.strip()

        yield {
                "year": year, 
                "month": month, 
                "event_name": event_name,
                "event_place": event_place,
                "event_date": event_date,
                "gender": gender,
                'qualification_date': qualification_texts,
                "prize_money": prize_money,
                "club_info": club_info,
            }