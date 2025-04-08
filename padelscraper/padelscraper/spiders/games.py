import scrapy
import re
from typing import Optional, List, Dict, Any, Iterator, Union

class GamesSpider(scrapy.Spider):
    """
    A Scrapy spider to scrape game data from the URL of the tournament games

    Attributes:
        start_url (str): The initial URL to start scraping from.
        days_played (int): The number of days to scrape game data for.
        start_urls (List[str]): A list of URLs to start scraping from (initialized with `start_url`).
    """

    name: str = "gamespider"
    
    def __init__(self, 
                 start_url: Optional[str] = None, 
                 days_played: Optional[int] = None, 
                 *args: Any, 
                 **kwargs: Any) -> None:
        """
        Initializes the GamesSpider.

        Args:
            start_url (Optional[str]): The URL to start scraping from. Must be provided.
            days_played (Optional[int]): The number of days to scrape game data for. Must be provided.
            *args: Additional positional arguments passed to the parent class.
            **kwargs: Additional keyword arguments passed to the parent class.

        Raises:
            ValueError: If `start_url` or `days_played` is not provided.
        """
        super(GamesSpider, self).__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("A start_url must be provided to run this spider.")
        if days_played is None:
            raise ValueError("days_played must be provided to run this spider.")
        self.start_url: str = start_url 
        self.days_played: int = int(days_played)  
        self.start_urls: List[str] = [start_url] 

    def parse(self, response: scrapy.http.Response) -> Iterator[scrapy.Request]:
        """
        Parses the initial response and generates requests for each day's games.

        Args:
            response (scrapy.http.Response): The response object from the initial request.

        Yields:
            scrapy.Request: A request to follow a URL for a specific day's games.
        """
        url: str = self.start_url
        days_played: int = self.days_played

        # Use regex to find and replace the number between '/' and '?'
        pattern: str = r"(?<=\/)\d+(?=\?)"
        number_range: range = range(1, days_played + 1)
        dates: List[str] = response.xpath('//span[@class="play-day-date"]/text()').getall()
        urls: List[str] = [re.sub(pattern, str(num), url) for num in number_range]

        for url, date in zip(urls, dates):
            yield response.follow(url, self.parse_games, cb_kwargs={'date': date})

    def parse_games(self, 
                    response: scrapy.http.Response, 
                    date: str) -> Iterator[Dict[str, Union[str, None]]]:
        """
        Parses the response for a specific day's games and extracts game data.

        Args:
            response (scrapy.http.Response): The response object for a specific day's games.
            date (str): The date associated with the games being parsed.

        Yields:
            Dict[str, Union[str, None]]: A dictionary containing game data for each game.
        """

        games: scrapy.SelectorList = response.xpath('//div[@class="row"]/div[contains(@class, "col-lg-4")]')
    
        for game in games:
            yield from self.parse_game(response, game, date)

    def parse_game(self, 
                   response,
                   game: scrapy.Selector, 
                   date: str) -> Dict[str, Union[str, None]]:
        """
        Parses an individual game and extracts its data.

        Args:
            game (scrapy.Selector): The selector object representing an individual game.
            date (str): The date associated with the game.
            court_name (Optional[str]): The name of the court where the game is played.

        Returns:
            Dict[str, Union[str, None]]: A dictionary containing the extracted game data.
        """
        court_name = game.xpath('.//span[@class="court-name"]/text()').get() or ''
        match_time: Optional[str] = game.xpath('.//span[@class="mr-4"]/text()').get()
        gender = (game.xpath(".//div[@class='round-name text-right']/small/b/text()").get() or '').strip()  
        round = game.xpath('//div[@class="round-name text-right"]/small/div/text()').get() 

        button = game.css('a.open')
        data_id = button.xpath('@data-id').get()
        data_year = button.xpath('@data-year').get()
        data_tid = button.xpath('@data-tid').get()
        data_org = button.xpath('@data-org').get()

        winner_div = game.xpath('.//div[@class="ml-2 winner line-thin"]')
        winner_player_name_parts = winner_div.xpath('.//span/text()').getall()
        winner_player_name = ' '.join(part.strip() for part in winner_player_name_parts if part.strip())

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
                    'court': court_name,
                    'gender': gender,
                    'round': round,
                    'winner_player_name': winner_player_name,
                    'loser_player_name': loser_player_name
                }
            )

    def parse_stats(self, response: scrapy.http.Response) -> Iterator[Dict[str, Union[str, List[str], Dict[str, Any]]]]:
        """
        Parses the statistics for a specific game.

        Args:
            response (scrapy.http.Response): The response object containing the game statistics.

        Yields:
            Dict[str, Union[str, List[str], Dict[str, Any]]]: A dictionary containing the parsed game statistics.
        """

        player_names = response.xpath('//span[@class="stats-team"]/text()').getall()
        player_names = [name.strip() for name in player_names]
        match_score = response.xpath('//div[@class="stats-score"]/text()').get()
        match_time = response.xpath('//div[@class="stats-matchtime"]/text()').get()
        player_flags = response.xpath('//img[contains(@src, "/images/flags/")]/@src').getall()
        player_flags = [flag.split('/')[-1].replace('.jpg', '') for flag in player_flags]
        set_tabs = response.xpath('//ul[contains(@class, "nav-tabs")]/li[contains(@class, "nav-item")]')
        num_sets = len(set_tabs) - 1  # Subtract 1 to exclude the "Match" tab


        def parse_sets_stats(data: List[str]) -> Dict[str, Dict[str, List[str]]]:
            """
            Parses the statistics data into a structured format.

            Args:
                data (List[str]): A list of raw statistics data.

            Returns:
                Dict[str, Dict[str, List[str]]]: A structured dictionary of statistics.
            """
            
            result = {}
            current_section = None  # To track the current section (e.g., "Serve", "Return", etc.)
            i = 0  

            while i < len(data):
                if isinstance(data[i], str) and not data[i].endswith('%') and not data[i].isdigit():
                    current_section = data[i]
                    result[current_section] = {}  
                    i += 1  
                else:
                    # Process the three-pair chunk within the current section
                    if i + 2 < len(data):  # Ensure there are enough items left for a chunk
                        value1 = data[i]
                        key = data[i + 1]
                        value2 = data[i + 2]

                        if current_section: 
                            result[current_section][key] = [value1, value2]

                        i += 3
                    else:
                        # If there aren't enough items left, break
                        break

            return result

        match_stats_list = response.xpath('//div[@id="period-0"]//text()').getall()
        match_stats_list = [stat.strip() for stat in match_stats_list if stat.strip()]
        match_stats_list = parse_sets_stats(match_stats_list)
    
        set_stats = {}
        for i in range(1, 4):  
            if i <= num_sets:
                set_stats_list = response.xpath(f'//div[@id="period-{i}"]//text()').getall()
                set_stats_list = [stat.strip() for stat in set_stats_list if stat.strip()]
                set_stats[f"Set {i}"] = parse_sets_stats(set_stats_list)

            else:
                # If the set doesn't exist, add an empty list
                set_stats[f"Set {i}"] = {}

        yield {
            'date': response.meta['date'],
            'court': response.meta['court'],
            'gender': response.meta['gender'],
            'round': response.meta['round'],
            'winner_player_name': response.meta['winner_player_name'],
            'loser_player_name': response.meta['loser_player_name'],
            'player_names': player_names,
            'match_score': match_score,
            'match_time': match_time,
            'player_flags': player_flags,
            'num_sets': num_sets,
            'match_stats': match_stats_list,  
            'set_stats': set_stats
        }