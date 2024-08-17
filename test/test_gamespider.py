import pytest
from scrapy.http import HtmlResponse
from unittest.mock import patch, MagicMock, Mock
from padelscraper.padelscraper.spiders.games import GamesSpider

def test_spider_initialization():
    with pytest.raises(ValueError):
        GamesSpider()

    spider = GamesSpider(start_url="https://www.example.com", days_played=10)
    assert spider.start_url == "https://www.example.com"
    assert spider.days_played == 10

    with pytest.raises(ValueError):
        GamesSpider(start_url="https://www.example.com")

def test_url_generation():
    spider = GamesSpider(start_url="https://www.example.com/1?whatever", days_played=3)
    
    # Create a mock response object
    mock_response = Mock()
    mock_response.follow = Mock()

    # Call the parse method with the mock response
    urls = list(spider.parse(mock_response))

    # Define the expected URLs based on the start_url and days_played
    expected_urls = [
        "https://www.example.com/1?whatever",
        "https://www.example.com/2?whatever",
        "https://www.example.com/3?whatever"
    ]

    # Check if the URLs generated match the expected URLs
    assert all(url in expected_urls for url in [call_args[0][0] for call_args in mock_response.follow.call_args_list])

@pytest.fixture
def mock_response():
    html = """
    <html>
        <body>
            <div class="small">2024-08-16</div>
            <div class="row">
                <div class="col-lg-4">
                    <div class="game">
                        <span class="court-name">Court A</span>
                        <div class="round-name text-right">
                            <small><b>Men's Singles</b></small>
                        </div>
                        <h3>Game 1</h3>
                        <p>Details for game 1.</p>
                        <a class="open" data-id="1" data-year="2024" data-tid="100" data-org="org1"></a>
                        <div class="ml-2 winner line-thin"><span>Winner A</span></div>
                        <div class="ml-2 line-thin"><span>Loser A</span></div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="game">
                        <span class="court-name">Court B</span>
                        <div class="round-name text-right">
                            <small><b>Women's Doubles</b></small>
                        </div>
                        <h3>Game 2</h3>
                        <p>Details for game 2.</p>
                        <a class="open" data-id="2" data-year="2024" data-tid="200" data-org="org2"></a>
                        <div class="ml-2 winner line-thin"><span>Winner B</span></div>
                        <div class="ml-2 line-thin"><span>Loser B</span></div>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """
    return HtmlResponse(url="http://example.com", body=html, encoding='utf-8')

@patch('padelscraper.padelscraper.spiders.games.scrapy.FormRequest')
def test_parse_games(mock_form_request, mock_response):
    mock_form_request.return_value = MagicMock()  # Mock the FormRequest
    
    spider = GamesSpider(start_url="http://example.com/page/1?days=5", days_played=5)
    results = list(spider.parse_games(mock_response))
    
    # Check that FormRequest was called correctly
    assert mock_form_request.call_count == 2  # There should be two FormRequest calls

    # Extract call arguments
    call_args_list = mock_form_request.call_args_list
    for call in call_args_list:
        # Each call is a tuple with one element containing kwargs
        kwargs = call[1]  # kwargs is the dictionary of arguments
        print("Call arguments:", kwargs)
    
    # Check that FormRequest was called with the correct parameters
    assert all("screen/getmatchstats?t=tol" in call[1]['url'] for call in call_args_list)  # Ensure URLs contain the expected path
    
    # Extract the meta data passed to FormRequest
    meta_calls = [call[1]['meta'] for call in call_args_list]
    assert any(meta['date'] == '2024-08-16' for meta in meta_calls)
    assert any(meta['court'] == 'Court A' for meta in meta_calls)
    assert any(meta['gender'] == "Men's Singles" for meta in meta_calls)