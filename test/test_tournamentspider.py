import pytest
from scrapy.http import HtmlResponse, Request
from padelscraper.padelscraper.spiders.tournaments import TournamentSpider

@pytest.fixture
def spider():
    return TournamentSpider()

def test_parse(spider):
    response = HtmlResponse(url="https://www.padelfip.com/es/calendario-premier-padel/",
                            body=b"<html></html>")
    requests = list(spider.parse(response))
    
    assert len(requests) == 2
    assert requests[0].url == "https://www.padelfip.com/es/calendario-premier-padel/?events-year=2023"
    assert requests[1].url == "https://www.padelfip.com/es/calendario-premier-padel/?events-year=2024"

def test_parse_year(spider):
    html = """
    <section class="month-section">
        <h2>January</h2>
        <article>
            <div class="event-title"><a href="/event-url">Event 1</a></div>
        </article>
    </section>
    """
    request = Request(url="https://www.padelfip.com/es/calendario-premier-padel/?events-year=2023", meta={"year": 2023})
    response = HtmlResponse(url=request.url, body=html.encode('utf-8'), request=request)

    results = list(spider.parse_year(response))

    assert len(results) == 1
    assert results[0].url == "https://www.padelfip.com/event-url"
    assert results[0].meta['year'] == 2023
    assert results[0].meta['month'] == "January"

def test_parse_games_orders(spider):
    html = """
    <iframe class="iframe-score" data-src="/scores/5?otherparam=value"></iframe>
    """
    attributes = {
        "year": 2023,
        "month": "January",
        "event_name": "Test Event"
    }
    request = Request(url="https://www.padelfip.com/event-url?tab=Orden+de+juego", meta={"attributes": attributes})
    response = HtmlResponse(url=request.url, body=html.encode('utf-8'), request=request)

    result = list(spider.parse_games_orders(response))[0]

    assert result["days_played"] == 5
    assert result["url"] == "/scores/5?otherparam=value"