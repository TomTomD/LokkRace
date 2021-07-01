import os.path
import datetime
from operator import attrgetter
import json
import raceconfig


def get_time_string(time_in_seconds):
    time_rounded = round(time_in_seconds)
    if time_in_seconds >= 0:
        return str(int(time_rounded/60)).zfill(2) + ":" + str(int(time_rounded % 60)).zfill(2)
    else:
        return "**:**"


class Participant:
    best_time_seconds = 50 * 60
    name = "No One"
    number = 0
    race_time_seconds = 0
    race_finish_time_seconds = 0
    race_improvement_seconds = 0

    def __init__(self, name, best_time_seconds=None):
        self.name = name
        self.race_history = list()
        if best_time_seconds is not None:
            self.best_time_seconds = best_time_seconds

    def store_race(self, race_string):
        print("STORE")
        print(self.race_history)
        self.race_history.append({"race": race_string, "time_seconds": self.race_time_seconds})
        print(self.race_history)

    def save(self):
        if not os.path.isdir(raceconfig.PARTICIPANTS_DIR):
            os.makedirs(raceconfig.PARTICIPANTS_DIR)
        dict_to_save = self.__dict__
        dict_to_save["race_history"] = self.race_history
        file_name = raceconfig.PARTICIPANTS_DIR + self.name + ".json"
        with open(file_name, "w") as write_file:
            json.dump(dict_to_save, write_file, indent=4)

    def load(self):
        try:
            file_name = raceconfig.PARTICIPANTS_DIR + self.name + ".json"
            with open(file_name, "r") as read_file:
                data = json.load(read_file)
                self.best_time_seconds = data["best_time_seconds"]
                if "race_history" in data.keys():
                    self.race_history = data["race_history"]
                    print("load")
                    print(self.race_history)
        except FileNotFoundError:
            # OK. this is a new racer. Nothing to load.
            print("New racer!")

    def get_report(self):
        string_to_return = self.name + "\n"
        string_to_return += "Bästa tid:" + get_time_string(self.best_time_seconds) + "\n"
        season_first = None
        season_best = 10000
        for history_element in self.race_history:
            string_to_return += history_element["race"] + " - "
            time = history_element["time_seconds"]
            string_to_return += get_time_string(time) + "\n"
            if season_first is None:
                season_first = time
            if season_best > time:
                season_best = time
        if season_first is not None:
            string_to_return += "Säsongens första:      " + get_time_string(season_first) + "\n"
            string_to_return += "Säsongens bästa:       " + get_time_string(season_best) + "\n"
            string_to_return += "Säsongens förbättring: " + get_time_string(season_first - season_best) + "\n"

        return string_to_return


class Race:
    participants = []
    goal_time_list_seconds = []
    goal_list_participant = []
    start_time = None
    longest_time = raceconfig.RACE_INITIAL_TIME

    def get_participant_start_time(self, participant):
        if participant.best_time_seconds > raceconfig.RACE_INITIAL_TIME:
            calculated_time = raceconfig.RACE_INITIAL_TIME # Limit so we don't spread out the starting field too much.
        else:
            calculated_time = participant.best_time_seconds

        start_time = self.longest_time - calculated_time

        return start_time

    def get_race_duration(self):
        if self.start_time is not None:
            now = datetime.datetime.now()
            race_duration_seconds = (now - self.start_time).total_seconds()
        else:
            race_duration_seconds = 0
        return race_duration_seconds

    def get_start_list(self):
        return_string = "start".ljust(6)
        return_string += "Nr "
        return_string += "Namn".ljust(20)
        return_string += "best".ljust(6)
        return_string += "start".ljust(6)
        return_string += "mål".ljust(6)
        return_string += "tid".ljust(6)
        return_string += "förbättring".ljust(12)
        return_string += "\n"

        race_duration_seconds = self.get_race_duration()

        for a in self.participants:
            return_string += get_time_string(self.get_participant_start_time(a) - race_duration_seconds).ljust(6)
            return_string += str(a.number).ljust(2)[:2] + " "
            return_string += a.name.ljust(20)[:20]
            return_string += get_time_string(a.best_time_seconds).ljust(6)
            return_string += get_time_string(self.get_participant_start_time(a)).ljust(6)
            return_string += get_time_string(a.race_finish_time_seconds).ljust(6)
            return_string += get_time_string(a.race_time_seconds).ljust(6)
            return_string += get_time_string(a.race_improvement_seconds).ljust(12)
            return_string += "\n"
        return return_string

    def get_goal_time_list(self):
        return_string_list = []
        index = 0
        for time_entry in self.goal_time_list_seconds:
            string_entry = get_time_string(time_entry)
            if self.goal_list_participant:
                if index < len(self.goal_list_participant):
                    string_entry += " - " + self.goal_list_participant[index].name
            index = index + 1
            return_string_list.append(string_entry)

        return return_string_list

    def find_participant(self, name):
        for participant in self.participants:
            if participant.name == name:
                return participant
        return None

    def add_participant(self, name, number, time=None):

        current_participant = self.find_participant(name)

        if current_participant is None:
            current_participant = Participant(name)
            current_participant.load()
            self.participants.append(current_participant)

        if time is not None:
            # New best time to set.
            current_participant.best_time_seconds = time
        current_participant.number = number

        current_participant.save()

        self.participants = sorted(self.participants, key=attrgetter('best_time_seconds'), reverse=True)
        longest_best_time = self.participants[0].best_time_seconds
        if longest_best_time > raceconfig.RACE_INITIAL_TIME:
            self.longest_time = raceconfig.RACE_INITIAL_TIME
        else:
            self.longest_time = self.participants[0].best_time_seconds

    def remove_participant(self, name):
        current_participant = self.find_participant(name)

        if current_participant is not None:
            self.participants.remove(current_participant)

    def start(self):
        self.start_time = datetime.datetime.now()

    def timestamp_goal(self):
        now = datetime.datetime.now()
        race_duration_seconds = (now - self.start_time).total_seconds()
        self.goal_time_list_seconds.append(race_duration_seconds)

    def assign_next_finish_time(self, name):
        current_participant = self.find_participant(name)
        if not self.goal_list_participant:
            # List empty. index will be 0
            index = 0
        else:
            # If we can add this will be the index.
            index = len(self.goal_list_participant)

        if self.goal_time_list_seconds:
            if index < len(self.goal_time_list_seconds):
                finish_time = self.goal_time_list_seconds[index]
                self.goal_list_participant.append(current_participant)
                start_time_seconds = self.get_participant_start_time(current_participant)
                race_result_seconds = finish_time - start_time_seconds
                current_participant.race_finish_time_seconds = finish_time
                current_participant.race_time_seconds = race_result_seconds
                current_participant.race_improvement_seconds = current_participant.best_time_seconds - race_result_seconds
                self.participants = sorted(self.participants, key=attrgetter('race_improvement_seconds'), reverse=True)

                return True

        return False

    def remove_last_assigned(self):
        if self.goal_list_participant:
            removed_participant = self.goal_list_participant.pop()
            return removed_participant.name
        return None

    def remove_finish_time_index(self, index):
        if self.goal_time_list_seconds:
            if index < len(self.goal_time_list_seconds):
                if index >= len(self.goal_list_participant):
                    # Only allow removal if no participant assign to time.
                    self.goal_time_list_seconds.pop(index)

    def add_finish_time(self, time_in_seconds):
        self.goal_time_list_seconds.append(time_in_seconds)
        self.goal_time_list_seconds.sort()

    def save(self):
        if not os.path.isdir(raceconfig.RACE_RESULT_DIR):
            os.makedirs(raceconfig.RACE_RESULT_DIR)
        race_string = self.start_time.strftime("%Y%m%d-%H%M%S")
        file_name = raceconfig.RACE_RESULT_DIR + race_string + ".txt"
        with open(file_name, "w") as write_file:
            write_file.write(self.get_start_list())

        for a in self.participants:
            if a.best_time_seconds > a.race_time_seconds:
                a.best_time_seconds = a.race_time_seconds
            a.store_race(race_string)
            a.save()
