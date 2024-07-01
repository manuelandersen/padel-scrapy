import json
import pytest
import warnings

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

def test_name_not_none(player_data):
    for player in player_data:
        name = player.get("name")
        assert name is not None, "Name should not be None"

def test_points_is_number(player_data):
    for player in player_data:
        ranking = player.get("points")
        assert ranking is not None, "Points should not be None"
        assert ranking.isdigit(), f"Points {ranking} should be a number"

def test_position(player_data):
    for player in player_data:
        position = player.get("position")
        assert position in ["Right","Left"], "Position should not be None" 

def test_height_is_number(player_data):
    for player in player_data:
        height = player.get("height")
        if height is None:
            warnings.warn("Height should not be None")
        else:
            try:
                float(height)
            except ValueError:
                pytest.fail(f"Height {height} should be a number")

def test_matches_played_is_number(player_data):
    for player in player_data:
        matches_played = player.get("matches_played")
        if matches_played is None:
            warnings.warn("matches_played should not be None")
        else:
            assert matches_played.isdigit(), f"matches_played {matches_played} should be a number"

if __name__ == "__main__":
    pytest.main()