import json
import pytest

@pytest.fixture
def player_data():
    with open("padelscraper/players.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def test_ranking_is_number(player_data):
    for player in player_data:
        ranking = player.get("ranking")
        assert ranking is not None, "Ranking should not be None"
        assert ranking.isdigit(), f"Ranking {ranking} should be a number"

def test_points_is_number(player_data):
    for player in player_data:
        ranking = player.get("points")
        assert ranking is not None, "Points should not be None"
        assert ranking.isdigit(), f"Points {ranking} should be a number"

if __name__ == "__main__":
    pytest.main()