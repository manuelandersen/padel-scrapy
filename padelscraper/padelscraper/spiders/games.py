import scrapy
import json

class GamesSpider(scrapy.Spider):
    name = "gamespider"
    start_urls = ["https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/1?t=tol",
                #"https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/2?t=tol",
                "https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/3?t=tol"]

    def parse(self, response):

        urls = ["https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/1?t=tol",
                "https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/2?t=tol"]
        
        for url in urls:
            yield response.follow(url, self.parse_games)

    def parse_games(self, response):
        date = response.xpath("//div[@class='small']/text()").get().strip()
        games = response.xpath('//div[@class="row"]/div[contains(@class, "col-lg-4")]')
        for game in games:

            court = game.xpath('.//span[@class="court-name"]/text()').get()
            gender = game.xpath("//small/b/text()").get()
            round = game.xpath("//small/text()").get() 

            button = game.css('a.open')
            data_id = button.xpath('@data-id').get()
            data_year = button.xpath('@data-year').get()
            data_tid = button.xpath('@data-tid').get()
            data_org = button.xpath('@data-org').get()

            if data_id and data_year and data_tid and data_org:
                ajax_url = response.urljoin("/screen/getmatchstats?t=tol")
                formdata = {
                        'matchId': data_id,
                        'year': data_year,
                        'tournamentId': data_tid,
                        'organization': data_org,
                }

                yield scrapy.FormRequest(
                        url=ajax_url,
                        method="POST",
                        formdata=formdata,
                        callback=self.parse_stats,
                        meta={
                        'date': date,
                        'court': court,
                        'gender': gender,
                        'round': round,
                        'data_id': data_id,
                        'data_year': data_year,
                        'data_tid': data_tid,
                        'data_org': data_org
                    }
                )

    def parse_stats(self, response):

        total_points_won_percentages = response.css('p.text2.withPercentage .percentage::text').getall()
        total_points_won_numbers = response.css('p.text2.withPercentage .text3::text').getall()

        yield {
            'date': response.meta['date'],
            'court': response.meta['court'],
            'gender': response.meta['gender'],
            'round': response.meta['round'],
            'data_id': response.meta['data_id'],
            'data_year': response.meta['data_year'],
            'data_tid': response.meta['data_tid'],
            'data_org': response.meta['data_org'],
            'total_points_won_percentages': total_points_won_percentages,
            'total_points_won_numbers': total_points_won_numbers
        }




""" TODO: 
        
# extract couples:
        
1)  esto devuelve todos los nombres de los dos jugadores ganadores de sus partidos 
    games[0].xpath('//div[@class="ml-2 winner line-thin"]/span/text()')

2)  esto devuelve todos los nombres de los dos jugadores perderos de sus partidos 
    games[0].xpath('//div[contains(@class, "ml-2") and contains(@class, "line-thin")]/span/text()')

3)  esto devuelve los resultados en formato: los juegos de los que ganaron, los juegos de los que perdieron
    algunos tienen 3 sets, otros 2, y eventualmente si alguien se retira podria haber solo 1...
    games[0].xpath('//td[contains(@class, "set set-completed")]/text()')

4)  esto devuelve el tiempo que tomo en terminar el partido 
    games[0].xpath('//div[span[1]="🕑" and span[3]="Completed"]/span[2]/text()')    

IDEA: hay que si o si ir scrapeando partido por partido, y 

"""
