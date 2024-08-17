import scrapy
import re

class GamesSpider(scrapy.Spider):
    name = "gamespider"
    
    def __init__(self, start_url=None, days_played=None, *args, **kwargs):
        super(GamesSpider, self).__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("A start_url must be provided to run this spider.")
        if days_played is None:
            raise ValueError("days_played must be provided to run this spider.")
        self.start_url = start_url 
        self.days_played = int(days_played)  
        self.start_urls = [start_url] 

    def parse(self, response):

        url = self.start_url
        days_played = self.days_played

        # Use regex to find and replace the number between '/' and '?'
        pattern = r"(?<=\/)\d+(?=\?)"

        number_range = range(1, days_played+1)

        urls = [re.sub(pattern, str(num), url) for num in number_range]

        for url in urls:
            yield response.follow(url, self.parse_games)

    def parse_games(self, response):
        date = response.xpath("//div[@class='small']/text()").get().strip()
        games = response.xpath('//div[@class="row"]/div[contains(@class, "col-lg-4")]')
        for game in games:
            yield from self.parse_game(response, game, date)

    def parse_game(self, response, game, date):
        # court = game.xpath('.//span[@class="court-name"]/text()').get()
        # gender = game.xpath(".//div[@class='round-name text-right']/small/b/text()").get().strip()
        # round = game.xpath(".//div[@class='round-name text-right']/small/text()").get().strip()

        court = game.xpath('.//span[@class="court-name"]/text()').get() or ''
        gender = (game.xpath(".//div[@class='round-name text-right']/small/b/text()").get() or '').strip()
        round = (game.xpath(".//div[@class='round-name text-right']/small/text()").get() or '').strip()

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
                    'winner_player_name': winner_player_name,
                    'loser_player_name': loser_player_name
                }
            )

    def parse_stats(self, response):

        stats_attributes = {}

        tournament = response.xpath("//div[@class='text-center pt-2']/h1[@class='title1 mb-0 font-weight-bold']/text()").get()
        scores = response.xpath("//div[@class='h3 text-center match-score']/text()").getall()
        cleaned_scores = [score.strip() for score in scores]

        players = response.xpath('//div[@class="row"]//h6[contains(@class, "player-names-stats")]/text()').getall()
        left_players = players[:2]
        right_players = players[2:]

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
            'tournament': tournament,
            'date': response.meta['date'],
            'court': response.meta['court'],
            'gender': response.meta['gender'],
            'round': response.meta['round'],
            'time': time,
            'winner_player_name': response.meta['winner_player_name'],
            'loser_player_name': response.meta['loser_player_name'],
            'left_players': left_players,
            'right_players': right_players,
            'scores': cleaned_scores,
            **stats_attributes
        }