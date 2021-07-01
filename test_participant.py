import racebase


def test_initial_values():
    pelle = racebase.Participant('Pelle')
    assert pelle.best_time_seconds == 14*60


def test_start_times():
    race = racebase.Race()
    race.add_participant('Anna', '14', 15*60)
    race.add_participant('Pelle', '19', 16*60+30)
    race.add_participant('Sara', '49', 10*60+22)
    expected_string = '00:00 ' + '14 ' + 'Anna'.ljust(20) + '15:00 ' + '00:00 '
    assert expected_string in race.get_start_list()

    expected_string = '00:00 ' + '19 ' + 'Pelle'.ljust(20) + '16:30 ' + '00:00 '
    assert expected_string in race.get_start_list()

    expected_string = '03:38 ' + '49 ' + 'Sara'.ljust(20) + '10:22 ' + '03:38 '
    assert expected_string in race.get_start_list()
