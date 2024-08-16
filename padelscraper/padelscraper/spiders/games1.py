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

        #time = game.xpath('//div[span[1]="🕑" and span[3]="Completed"]/span[2]/text()')    


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
                    #'time': time,
                    'winner_player_name': winner_player_name,
                    'loser_player_name': loser_player_name
                }
            )

    def parse_stats(self, response):

        stats_attributes = {}

        # TODO: fix numbers. This number are the numbers version of the percentages, is not scraping the pure numbers.
        percentages = response.css('p.text2.withPercentage .percentage::text').getall()
        pctgs_numbers = response.css('p.text2.withPercentage .text3::text').getall()  
        numbers_left = response.xpath('//div[@class="col-md-4 col-3"][1]//p[@class="text2"]/text()').getall()
        numbers_right = response.xpath('//div[@class="col-md-4 col-3 text-right"][1]//p[@class="text2"]/text()').getall()
        time = response.xpath('//h5[@class="text-center text-uppercase m-3"]/span[2]/text()').get()

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
                                "longest_points_won_streak",
                                "average_point_duration_in_seconds",
                                "aces",
                                "double_faults",
                                "services_games_played",
                                "return_games_played"]  

        if total_stats < 16:
            raise Exception
        
        elif total_stats == 16: # just match stats and 1st set stats
            pctg_stat_counter = 0

            for i, stat in enumerate(2*list_of_pctg_stats): # 2 sets of stats
                if i*2+1 < len(percentages):  # Make sure we don't go out of bounds
                    winner_stat = percentages[i*2]
                    winner_n_stat = pctgs_numbers[i*2]

                    looser_stat = percentages[i*2+1]
                    looser_n_stat = pctgs_numbers[i*2+1]

                    if pctg_stat_counter == 0:

                        stats_attributes[f'left_match_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_match_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_match_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_match_pctg_numbers_{stat}'] = looser_n_stat

                    elif pctg_stat_counter == 1:
                        stats_attributes[f'left_1_set_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_1_set_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_1_set_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_1_set_pctg_numbers_{stat}'] = looser_n_stat

                if stat == 'total_return_points_won': # for switching to the next set of stats
                    pctg_stat_counter += 1

            number_stat_counter = 0

            for i, stat in enumerate(2*list_of_number_stats):
                if i < len(numbers_left): 
                    left_number_stat = numbers_left[i]
                    right_number_stat = numbers_right[i]

                    if number_stat_counter == 0:
                        stats_attributes[f'left_match_{stat}'] = left_number_stat
                        stats_attributes[f'right_match_{stat}'] = right_number_stat

                    if number_stat_counter == 1:
                        stats_attributes[f'left_{number_stat_counter}_set_{stat}'] = left_number_stat
                        stats_attributes[f'right_{number_stat_counter}_set_{stat}'] = right_number_stat

                    if stat == 'return_games_played':
                        number_stat_counter += 1

        elif total_stats == 24: # match stats, 1st set stats and 2nd stats

            pctg_stat_counter = 0

            for i, stat in enumerate(3*list_of_pctg_stats): # 3 sets of stats
                if i*2+1 < len(percentages):  # Make sure we don't go out of bounds
                    winner_stat = percentages[i*2]
                    winner_n_stat = pctgs_numbers[i*2]

                    looser_stat = percentages[i*2+1]
                    looser_n_stat = pctgs_numbers[i*2+1]

                    if pctg_stat_counter == 0:

                        stats_attributes[f'left_match_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_match_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_match_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_match_pctg_numbers_{stat}'] = looser_n_stat

                    elif pctg_stat_counter == 1:
                        stats_attributes[f'left_1_set_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_1_set_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_1_set_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_1_set_pctg_numbers_{stat}'] = looser_n_stat

                    elif pctg_stat_counter == 2:
                        stats_attributes[f'left_2_set_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_2_set_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_2_set_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_2_set_pctg_numbers_{stat}'] = looser_n_stat

                if stat == 'total_return_points_won': # for switching to the next set of stats
                    pctg_stat_counter += 1

            number_stat_counter = 0

            for i, stat in enumerate(3*list_of_number_stats):
                if i < len(numbers_left): 
                    left_number_stat = numbers_left[i]
                    right_number_stat = numbers_right[i]

                    if number_stat_counter == 0:
                        stats_attributes[f'left_match_{stat}'] = left_number_stat
                        stats_attributes[f'right_match_{stat}'] = right_number_stat

                    if number_stat_counter in [1,2]:
                        stats_attributes[f'left_{number_stat_counter}_set_{stat}'] = left_number_stat
                        stats_attributes[f'right_{number_stat_counter}_set_{stat}'] = right_number_stat

                    if stat == 'return_games_played':
                        number_stat_counter += 1
        
        elif total_stats == 32: # match stats, 1st set stats, 2nd set stats and 3rd set stats

            pctg_stat_counter = 0

            for i, stat in enumerate(4*list_of_pctg_stats): # 4 sets of stats
                if i*2+1 < len(percentages):  # Make sure we don't go out of bounds
                    winner_stat = percentages[i*2]
                    winner_n_stat = pctgs_numbers[i*2]

                    looser_stat = percentages[i*2+1]
                    looser_n_stat = pctgs_numbers[i*2+1]

                    if pctg_stat_counter == 0:

                        stats_attributes[f'left_match_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_match_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_match_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_match_pctg_numbers_{stat}'] = looser_n_stat

                    elif pctg_stat_counter == 1:
                        stats_attributes[f'left_1_set_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_1_set_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_1_set_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_1_set_pctg_numbers_{stat}'] = looser_n_stat

                    elif pctg_stat_counter == 2:
                        stats_attributes[f'left_2_set_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_2_set_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_2_set_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_2_set_pctg_numbers_{stat}'] = looser_n_stat

                    elif pctg_stat_counter == 3:
                        stats_attributes[f'left_3_set_pctg_{stat}'] = winner_stat
                        stats_attributes[f'left_3_set_pctg_numbers_{stat}'] = winner_n_stat

                        stats_attributes[f'right_3_set_pctg_{stat}'] = looser_stat
                        stats_attributes[f'right_3_set_pctg_numbers_{stat}'] = looser_n_stat

                if stat == 'total_return_points_won': # for switching to the next set of stats
                    pctg_stat_counter += 1

            number_stat_counter = 0

            for i, stat in enumerate(4*list_of_number_stats):
                if i < len(numbers_left): 
                    left_number_stat = numbers_left[i]
                    right_number_stat = numbers_right[i]

                    if number_stat_counter == 0:
                        stats_attributes[f'left_match_{stat}'] = left_number_stat
                        stats_attributes[f'right_match_{stat}'] = right_number_stat

                    if number_stat_counter in [1,2,3]:
                        stats_attributes[f'left_{number_stat_counter}_set_{stat}'] = left_number_stat
                        stats_attributes[f'right_{number_stat_counter}_set_{stat}'] = right_number_stat

                    if stat == 'return_games_played':
                        number_stat_counter += 1

        yield {
            'date': response.meta['date'],
            'court': response.meta['court'],
            'gender': response.meta['gender'],
            'round': response.meta['round'],
            'time': time,
            'winner_player_name': response.meta['winner_player_name'],
            'loser_player_name': response.meta['loser_player_name'],
            **stats_attributes
        }