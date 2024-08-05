import scrapy

class GamesSpider(scrapy.Spider):
    name = "gamespider1"
    start_urls = ["https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/1?t=tol",
                #"https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/2?t=tol",
                "https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/3?t=tol"]

    def parse(self, response):

        urls = ["https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/1?t=tol",
                #"https://widget.matchscorerlive.com/screen/resultsbyday/FIP-2024-902/2?t=tol"
                ]
        
        for url in urls:
            yield response.follow(url, self.parse_games)

    def parse_games(self, response):
        date = response.xpath("//div[@class='small']/text()").get().strip()
        games = response.xpath('//div[@class="row"]/div[contains(@class, "col-lg-4")]')
        for game in games:
            yield from self.parse_game(response, game, date)

    def parse_game(self, response, game, date):
        court = game.xpath('.//span[@class="court-name"]/text()').get()
        gender = game.xpath("//small/b/text()").get()
        round = game.xpath("//small/text()").get() 

        button = game.css('a.open')
        data_id = button.xpath('@data-id').get()
        data_year = button.xpath('@data-year').get()
        data_tid = button.xpath('@data-tid').get()
        data_org = button.xpath('@data-org').get()

        # Extract winner player names
        winner_div = game.xpath('.//div[@class="ml-2 winner line-thin"]')
        winner_player_name_parts = winner_div.xpath('.//span/text()').getall()
        winner_player_name = ' '.join(part.strip() for part in winner_player_name_parts if part.strip())

        # Extract loser player names
        loser_div = game.xpath('.//div[@class="ml-2  line-thin"]')
        loser_player_name_parts = loser_div.xpath('.//span/text()').getall()
        loser_player_name = ' '.join(part.strip() for part in loser_player_name_parts if part.strip())


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
                    'data_org': data_org,
                    'winner_player_name': winner_player_name,
                    'loser_player_name': loser_player_name
                }
            )

    def parse_stats(self, response):

        stats_attributes = {}

        # TODO: fix numbers. This number are the numbers version of the percentages, is not scraping the pure numbers.
        percentages = response.css('p.text2.withPercentage .percentage::text').getall()
        pctgs_numbers = response.css('p.text2.withPercentage .text3::text').getall()  
        numbers = response.xpath('//div[@class="col-md-4 col-3"][1]//p[@class="text2"]/text()').getall()

        total_stats = len(percentages) // 2 

        list_of_pctg_stats = ["total_points_won", 
                         "break_points_converted", 
                         "first_serve_point_won",
                         "second_serve_point_won",
                         "first_return_points_won",
                         "second_return_points",
                         "total_serve_points_won",
                         "total_return_points_won"]
        
        list_of_number_stats = [
                            #   "total_points_won",
                            #    "break_points_converted", 
                                "longest_points_won_streak",
                                "average_point_duration_in_seconds",
                                "aces",
                                "double_faults",
                            #    "first_serve_point_won",
                            #    "second_serve_point_won",
                                "services_games_played",
                            #    "first_return_points_won",
                            #    "second_return_points",
                                "return_games_played",
                                "total_serve_points_won",
                                "total_return_points_won"]

        print("#####################################")
        print(f"{numbers}")
        print("#####################################")


        if total_stats < 16:
            raise Exception
        
        elif total_stats <= 32: # just match stats and 1st set stats
            pctg_stat_counter = 0
            number_stat_counter = 0

            for i, stat in enumerate(2*list_of_pctg_stats): # 2 sets of stats
                if i*2+1 < len(percentages):  # Make sure we don't go out of bounds
                    winner_stat = percentages[i*2]
                    looser_stat = percentages[i*2+1]

                    if pctg_stat_counter == 0:

                        stats_attributes[f'right_match_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_match_pctg_{stat}'] = looser_stat

                    elif pctg_stat_counter == 1:
                        stats_attributes[f'right_1_set_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_1_set_pctg_{stat}'] = looser_stat

                if stat == 'total_return_points_won': # for switching to the next set of stats
                    pctg_stat_counter += 1

            # TODO: big BUG here: the numbers stats are being scraped like this: first all the stats from one couple, going from match
            # stats, 1 set stats, etc., and then switching to collect the second couple stats

            for i, stat in enumerate(2*list_of_number_stats): # 2 sets of stats
                if i*2+1 < len(numbers):  # Make sure we don't go out of bounds
                    winner_stat = numbers[i*2]
                    looser_stat = numbers[i*2+1]

                    if number_stat_counter == 0:

                        stats_attributes[f'right_match_number_{stat}'] = winner_stat
                        stats_attributes[f'left_match_number_{stat}'] = looser_stat

                    elif number_stat_counter == 1:
                        stats_attributes[f'right_1_set_number_{stat}'] = winner_stat
                        stats_attributes[f'left_1_set_number_{stat}'] = looser_stat

                if stat == 'return_games_played': # for switching to the next set of stats
                    number_stat_counter += 1

        elif total_stats <= 48: # match stats, 1st set stats and 2nd stats

            for i, stat in enumerate(3*list_of_pctg_stats): # 3 sets of stats
                if i*2+1 < len(percentages):  # Make sure we don't go out of bounds
                    winner_stat = percentages[i*2]
                    looser_stat = percentages[i*2+1]
        
        #elif total_stats <= 64:

        yield {
            'date': response.meta['date'],
            'court': response.meta['court'],
            'gender': response.meta['gender'],
            'round': response.meta['round'],
            'winner_player_name': response.meta['winner_player_name'],
            'loser_player_name': response.meta['loser_player_name'],
            #'total_points_won_percentages': percentages,
            #'total_points_won_numbers': numbers,
            **stats_attributes
        }