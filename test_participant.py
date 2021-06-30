import racebase


def test_initial_values():
    pelle = racebase.Participant('Pelle')
    assert pelle.best_time_seconds == 14*60
