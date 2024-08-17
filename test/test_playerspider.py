import pytest
import scrapy
import json
from scrapy.http import HtmlResponse, Request, TextResponse
from padelscraper.padelscraper.spiders.players import PlayerSpider
import json

@pytest.fixture
def spider():
    return PlayerSpider()

def test_parse(spider):
    html = """
    <div class="slider__item">
        <h2 class="slider__name"><a href="/player1">Player 1</a></h2>
    </div>
    <div class="playerGrid__item">
        <div class="playerGrid__name"><a href="/player2">Player 2</a></div>
    </div>
    <div class="data-body-row">
        <td class="data-body-cell data-player-img-name">
            <div class="data-title-container"><a href="/player3">Player 3</a></div>
        </td>
    </div>
    <div class="loadMoreRanking" data-total-post="50" data-posts-per-page="10" data-offset="0" data-gender="male" data-category="pro"></div>
    """
    request = Request(url="https://www.padelfip.com/es/ranking-masculino/")
    response = HtmlResponse(url=request.url, body=html.encode('utf-8'), request=request)

    requests = list(spider.parse(response))

    # Check initial player URLs
    player_urls = [req.url for req in requests if isinstance(req, Request)]

    # Adjust assertions to check full URLs
    assert "https://www.padelfip.com/player1" in player_urls
    assert "https://www.padelfip.com/player2" in player_urls
    assert "https://www.padelfip.com/player3" in player_urls

    # Check if load more request is generated
    assert any(isinstance(req, scrapy.FormRequest) for req in requests)

def test_parse_more(spider):
    # Mock JSON response for the load more functionality
    json_data = {
        "html": """
        <div class="data-body-row">
            <td class="data-body-cell data-player-img-name">
                <div class="data-title-container"><a href="/player4">Player 4</a></div>
            </td>
        </div>
        """
    }
    
    # Create a Request for the AJAX endpoint
    request = Request(
        url="https://www.padelfip.com/wp-admin/admin-ajax.php",
        method="POST",
        body=json.dumps(json_data),
        headers={'Content-Type': 'application/json'},
        meta={'params': {'action': 'post_type_infinite', 'paged': '1', 
                         'post_type': 'player', 'posts_per_page': '10', 
                         'meta_key': 'ranking', 'taxonomy': 'country', 
                         'offset': '0', 'total_post': '50', 'term': 'gender,player_category', 
                         'termValue': 'male,pro'}, 'total_posts': 50}
    )
    
    # Encode the JSON data to bytes
    response_body = json.dumps(json_data).encode('utf-8')
    
    # Create a TextResponse with the encoded JSON body
    response = TextResponse(
        url=request.url,
        body=response_body,
        request=request,
        headers={'Content-Type': 'application/json'}
    )

    # Call the method with the mock response
    requests = list(spider.parse_more(response))

    # Check if player URLs are correctly followed
    player_urls = [req.url for req in requests if isinstance(req, Request)]

    assert "https://www.padelfip.com/player4" in player_urls

def test_parse_player_url(spider):
    # Mock HTML response for player URL
    html = """
    <html>
        <span class="slider__number player__number">5</span>
        <h2 class="slider__name player__name">Player 1</h2>
        <p class="slider__country player__country">Country</p>
        <span class="slider__pointTNumber player__pointTNumber">1000</span>
        <span class="content"><a href="/teammate">Teammate</a></span>
        <div class="additionalInfo__hand"><span class="content">Right</span></div>
        <div class="additionalInfo__birth"><span class="additionalInfo__data">01-01-1990</span></div>
        <div class="additionalInfo__height"><span class="additionalInfo__data">180 cm</span></div>
        <div class="additionalInfo__born"><span class="additionalInfo__data">City</span></div>
        <div class="additionalInfo__lives"><span class="additionalInfo__data">Country</span></div>
        <div class="matchPlayer__played"><span>50</span></div>
        <div class="matchPlayer__won"><span>30</span></div>
        <div class="lost"><span>20</span></div>
        <div class="matchPlayer__victories"><span>10</span></div>
        <div class="matchPlayer__effective"><span>80%</span></div>
        <span class="oldPosition down">5</span>
    </html>
    """
    
    # Create a Request for the player URL
    request = Request(
        url="https://www.padelfip.com/player1",
        meta={'some_meta_data': {'key': 'value'}}  # Example meta data
    )
    
    # Create an HtmlResponse with the mock HTML
    response = HtmlResponse(
        url=request.url,
        body=html.encode('utf-8'),
        request=request
    )

    # Call the method with the mock response
    results = list(spider.parse_player_url(response))

    # Check if the player data is correctly extracted
    assert results[0]['ranking'] == '5'
    assert results[0]['name'] == 'Player 1'
    assert results[0]['country'] == 'Country'
    assert results[0]['points'] == '1000'
    assert results[0]['paired_with'] == 'Teammate'
    assert results[0]['position'] == 'Right'
    assert results[0]['birth_date'] == '01-01-1990'
    assert results[0]['height'] == '180 cm'
    assert results[0]['place_of_birth'] == 'City'
    assert results[0]['residence'] == 'Country'
    assert results[0]['matches_played'] == '50'
    assert results[0]['matches_won'] == '30'
    assert results[0]['matches_lost'] == '20'
    assert results[0]['consecutive_victories'] == '10'
    assert results[0]['effectiveness'] == '80%'
    assert results[0]['old_position'] == '-5'
