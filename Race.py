import tkinter as tk
import tkinter.font as font
from operator import attrgetter
import datetime
import glob
import os.path

DATA_DIR = "./data"
PARTICIPANTS_DIR = DATA_DIR + "/kanotister/"
RACE_RESULT_DIR = DATA_DIR + "/reces/"

class Application(tk.Frame):
    def __init__(self, master=None, race=None):
        super().__init__(master, background="yellow")
        master.title("LöKK OnsdagsRejs")
        self.master = master
        self.race = race
        self.pack()
        self.create_widgets()
        self.update()

    def create_widgets(self):
        self.start_list = tk.Text(self)
        self.start_list.pack(side="left", expand=1, fill=tk.Y)



        self.available_racers_list = tk.Listbox(self, selectmode=tk.SINGLE)
        self.available_racers_list.pack(side="right", expand=1, fill=tk.Y)
        for file in glob.glob(PARTICIPANTS_DIR + "*.json"):
            path, filename = os.path.split(file)
            name = filename.split('.')[0]
            self.available_racers_list.insert(tk.END, name)
        #self.available_racers_list.bind("<Double-Button-1>", self.select_racer)

 

    
        button_frame = tk.Frame(self, background="yellow")
        button_frame.pack(side="right", expand=1, fill=tk.Y)

        racers_frame = tk.Frame(self, background="yellow")
        racers_frame.pack(side="right", expand=1, fill=tk.Y)

        participant_label = tk.Label(racers_frame, text="Deltagare", background="yellow")
        participant_label.pack()
        
        self.racers_list = tk.Listbox(racers_frame, selectmode=tk.SINGLE)
        self.racers_list.pack( expand=1, fill=tk.Y)

        tk.Label(button_frame, text="Nummer", background="yellow").pack()
        self.add_number = tk.Entry(button_frame, width=4)
        self.add_number.insert(0, "00")
        self.add_number.pack()
        
        self.add_existing_participant_button = tk.Button(button_frame)
        self.add_existing_participant_button["text"] = "Lägg till"
        self.add_existing_participant_button["command"] = self.add_existing_participant_pressed
        self.add_existing_participant_button.pack(pady=10)
        
        self.add_new_participant_button = tk.Button(button_frame)
        self.add_new_participant_button["text"] = "Lägg till ny deltagare"
        self.add_new_participant_button["command"] = self.add_new_participant_pressed
        self.add_new_participant_button.pack(pady=20)

        self.remove_participant_button = tk.Button(button_frame)
        self.remove_participant_button["text"] = "Ta bort"
        self.remove_participant_button["command"] = self.remove_participant_pressed
        self.remove_participant_button.pack()
        
        self.start_race_button = tk.Button(button_frame)
        self.start_race_button["text"] = "Start Race"
        self.start_race_button["command"] = self.start_race_pressed
        self.start_race_button.pack(side="bottom", pady=20)

        self.manual_race_button = tk.Button(button_frame)
        self.manual_race_button["text"] = "Manuellt resultat"
        #self.manual_race_button["command"] =
        self.manual_race_button.pack(side="bottom")

        self.repor_button = tk.Button(button_frame)
        self.repor_button["text"] = "Rapport"
        self.repor_button["command"] = self.report_pressed
        self.repor_button.pack(side="bottom")
        

    def add_existing_participant_pressed(self):
        index = int(self.available_racers_list.curselection()[0])
        selected_racer_name = self.available_racers_list.get(index)
        self.race.add_participant(selected_racer_name, self.add_number.get())
        self.add_number.delete(0,tk.END)
        self.add_number.insert(0, "00")
        self.update()
        
    def add_new_participant_pressed(self):
        d = AddParticipantDialog(self.master, self.race)
        self.master.wait_window(d)
        self.update()

    def remove_participant_pressed(self):
        index = int(self.racers_list.curselection()[0])
        selected_racer_name = self.racers_list.get(index)
        self.race.remove_participant(selected_racer_name)
        self.update()
        
    def report_pressed(self):
        d = ReportDialog(self.master, self.race)
        self.master.wait_window(d)
        self.update()
        
    def start_race_pressed(self):
        d = RunRaceDialog(self.master, self.race)
        self.master.wait_window(d)
        self.update()

    def update(self):
        start_list = self.race.get_start_list()
        self.start_list.config(state=tk.NORMAL)
        self.start_list.delete("1.0", tk.END)
        self.start_list.insert("1.0", start_list)
        self.start_list.config(state=tk.DISABLED)

        self.racers_list.delete(0, tk.END)
        for participant in self.race.participants:
            self.racers_list.insert(tk.END, participant.name)

class AddParticipantDialog(tk.Toplevel):
    def __init__(self, master=None, race=None):
        super().__init__(master, background="yellow")
        self.master = master
        self.race = race
        self.create_widgets()
        self.focus_set()
        self.grab_set()

    def create_widgets(self):
        self.number = tk.Entry(self)
        self.number.insert(0, "00")
        self.number.pack(side="left")
        self.name = tk.Entry(self)
        self.name.insert(0, "Namn")
        self.name.pack(side="left")
        self.best_time = tk.Entry(self)
        self.best_time.insert(0, "14:00")
        self.best_time.pack(side="left")

        self.add_button = tk.Button(self)
        self.add_button["text"] = "Lägg till"
        self.add_button["command"] = self.add_pressed
        self.add_button.pack(side="left")

        self.racers_list = tk.Listbox(self, selectmode=tk.SINGLE)
        self.racers_list.pack(side="right", expand=1, fill=tk.Y)
        for file in glob.glob(PARTICIPANTS_DIR + "*.json"):
            path, filename = os.path.split(file)
            name = filename.split('.')[0]
            self.racers_list.insert(tk.END, name)
        self.racers_list.bind("<Double-Button-1>", self.select_racer)

    def select_racer(self, event):
        index = int(self.racers_list.curselection()[0])
        selected_racer_name = self.racers_list.get(index)
        self.name.delete(0, tk.END)
        self.name.insert(0, selected_racer_name)
        self.best_time.delete(0, tk.END)
        racer = Participant(selected_racer_name)
        racer.load()
        self.best_time.insert(0, get_time_string(racer.best_time_seconds))
        
    def add_pressed(self):
        best_datetime = datetime.datetime.strptime(self.best_time.get(), "%M:%S")
        time_in_seconds = best_datetime.minute * 60 + best_datetime.second
        self.race.add_participant(self.name.get(), self.number.get(), time_in_seconds)
        self.destroy()


class RunRaceDialog(tk.Toplevel):
    def __init__(self, master=None, race=None):
        super().__init__(master, background="yellow")
        self.master = master
        self.race = race
        self.create_widgets()
        self.focus_set()
        self.grab_set()
        race.start_time = None
        self.update()
        
        
    def create_widgets(self):

        left_frame = tk.Frame(self, background="yellow")

        text_font = font.Font(family='Courier', size = 14)
        big_font = font.Font(size = 25)
        
        self.start_list = tk.Text(left_frame, font = text_font)
        # TODO: Write protect.
        self.start_list.pack(side="top", expand=1, fill=tk.Y)

        self.start_button = tk.Button(left_frame)
        self.start_button["text"] = "START!"
        self.start_button["command"] = self.start_button_pressed
        self.start_button["font"] = big_font
        self.start_button.pack(side="bottom")

        self.time_label = tk.Label(left_frame, text="00:00", font = text_font)
        self.time_label.pack(side="bottom")

        self.save_button = tk.Button(left_frame, text="Save Race", command=self.save_button_pressed)
        self.save_button["font"] = big_font

        left_frame.pack(side="left", expand=1, fill=tk.Y)
        
        right_frame = tk.Frame(self, background="yellow")
        right_frame.pack(side="right", expand=1, fill=tk.Y)

        goal_time_frame = tk.Frame(right_frame, background="yellow")
        goal_time_frame.pack(side="left", expand=1, fill=tk.Y)

        racers_frame = tk.Frame(right_frame, background="yellow")
        racers_frame.pack(side="left", expand=1, fill=tk.Y)

        tk.Label(goal_time_frame, background="yellow", text="eller tryck M").pack(side="bottom")
        self.goal_button = tk.Button(goal_time_frame)
        self.goal_button["text"] = "MÅL!"
        self.goal_button["command"] = self.goal_button_pressed
        self.goal_button["font"] = big_font
        self.goal_button.pack(side="bottom")

        # Bind m and M for goal button as well.
        self.bind("m", self.goal_button_pressed)
        self.bind("M", self.goal_button_pressed)


        self.remove_time_button = tk.Button(goal_time_frame, text = "Ta bort\nTid")
        self.remove_time_button["command"] = self.remove_time_pressed
        self.remove_time_button.pack(side="right")
        

        
        self.goal_list = tk.Listbox(goal_time_frame, selectmode=tk.SINGLE, font = text_font)
        self.goal_list.pack(side="top", expand=1, fill=tk.Y)
        
        
        self.racers_list = tk.Listbox(racers_frame, selectmode=tk.SINGLE, font = text_font)
        self.racers_list.pack(side="right", expand=1, fill=tk.Y)
        self.racers_list.bind("<Double-Button-1>", self.assign_goal_time)
        for participant in self.race.participants:
            self.racers_list.insert(tk.END, participant.name)

        assign_buttons_frame = tk.Frame(racers_frame, background="yellow")
        assign_buttons_frame.pack(side="left")
        self.race_set_time_button = tk.Button(assign_buttons_frame, text = "Sätt tid\n<--")
        self.race_set_time_button["command"] = self.assign_goal_time
        self.race_set_time_button.pack(side="top")

        self.remove_assigned_button = tk.Button(assign_buttons_frame, text = "Ångra\n-->")
        self.remove_assigned_button["command"] = self.remove_assigned_pressed
        self.remove_assigned_button.pack(side="top")

               
        

    def goal_button_pressed(self, event=None):
        self.race.timestamp_goal()
        self.update_goal_list()
        
    def assign_goal_time(self, event=None):
        index = int(self.racers_list.curselection()[0])
        selected_racer_name = self.racers_list.get(index)
        added = self.race.assign_next_finish_time(selected_racer_name)
        if added:
            self.racers_list.delete(index)
        self.update_goal_list()
        self.update()

    def remove_assigned_pressed(self):
        removed_racer = self.race.remove_last_assigned()
        if removed_racer:
            self.racers_list.insert(tk.END, removed_racer)
        self.update_goal_list()
        self.update()

    def remove_time_pressed(self):
        index = int(self.goal_list.curselection()[0])
        self.race.remove_finish_time_index(index)
        self.update_goal_list()
        self.update()

        
    def start_button_pressed(self):
        self.race.start()
        self.after(500, self.timer_update)
        self.start_button.pack_forget()

    def save_button_pressed(self):
        print("Save")
        print(self.race.get_start_list())
        self.race.save()
        self.save_button.pack_forget()

    def update(self):
        start_list = self.race.get_start_list()
        self.start_list.config(state=tk.NORMAL)
        self.start_list.delete("1.0", tk.END)
        self.start_list.insert(tk.END, start_list)
        self.start_list.config(state=tk.DISABLED)
        race_duration_seconds = self.race.get_race_duration()
        self.time_label["text"] = get_time_string(race_duration_seconds)

    def update_goal_list(self):
        goal_time_list = self.race.get_goal_time_list()
        print(goal_time_list)
        self.goal_list.delete(0, tk.END)
        for entry in goal_time_list:
            self.goal_list.insert(tk.END, entry)

        
    def timer_update(self):
        if (self.racers_list.size() > 0) :
            # Race still ongoing. Trigger again.
            self.after(500, self.timer_update)
        else:
            self.save_button.pack()
        self.update()

class ReportDialog(tk.Toplevel):
    def __init__(self, master=None, race=None):
        super().__init__(master, background="yellow")
        self.master = master
        self.race = race
        self.create_widgets()
        self.focus_set()
        self.grab_set()
        
    def create_widgets(self):
        self.report_text = tk.Text(self)
        # TODO: Write protect.
        self.report_text.pack(side="top", expand=1, fill=tk.Y)

        for file in glob.glob(PARTICIPANTS_DIR + "*.json"):
            path, filename = os.path.split(file)
            name = filename.split('.')[0]
            racer = Participant(name)
            racer.load()
            racer_report = racer.get_report()
            print(racer_report)
            self.report_text.insert(tk.END, racer_report)
            self.report_text.insert(tk.END, "\n")
        
import json

def get_time_string(time_in_seconds):
    time_rounded = round(time_in_seconds)
    if time_in_seconds >= 0 :
        return str(int(time_rounded/60)).zfill(2) + ":" + str(int(time_rounded%60)).zfill(2)
    else:
        return "**:**"
    
class Participant:
    best_time_seconds = 14*60
    name = "No One"
    number = 0
    race_time_seconds = 0
    race_finish_time_seconds = 0
    race_improvement_seconds = 0
    race_history = []

    def __init__(self, name, best_time_seconds = None):
        self.name = name
        if(best_time_seconds != None):
            self.best_time_seconds = best_time_seconds
            
    def store_race(self, race_string):
        print("STORE")
        print(self.race_history)
        self.race_history.append({"race": race_string, "time_seconds": self.race_time_seconds})
        print(self.race_history)
                   
    def save(self):
        if not os.path.isdir(PARTICIPANTS_DIR):
            os.makedirs(PARTICIPANTS_DIR)
        dict_to_save = self.__dict__
        dict_to_save["race_history"] = self.race_history
        file_name = PARTICIPANTS_DIR + self.name + ".json"
        with open(file_name, "w") as write_file:
            json.dump(dict_to_save, write_file, indent = 4)

    def load(self):
        try:
            file_name = PARTICIPANTS_DIR + self.name + ".json"
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
            if season_first == None :
                season_first = time
            if season_best > time :
                season_best = time
        if season_first != None :
            string_to_return += "Säsongens första:      " + get_time_string(season_first) + "\n"
            string_to_return += "Säsongens bästa:       " + get_time_string(season_best) + "\n"
            string_to_return += "Säsongens förbättring: " + get_time_string(season_first-season_best) + "\n"
        
        return string_to_return
            
    
    

    

class Race:
    participants = []
    goal_time_list_seconds = []
    goal_list_participant = []
    start_time = None

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
            return_string += get_time_string(self.longest_time - a.best_time_seconds - race_duration_seconds).ljust(6)
            return_string += str(a.number).ljust(2)[:2] + " "
            return_string += a.name.ljust(20)[:20]
            return_string += get_time_string(a.best_time_seconds).ljust(6)
            return_string += get_time_string(self.longest_time - a.best_time_seconds).ljust(6)
            return_string += get_time_string(a.race_finish_time_seconds).ljust(6)
            return_string += get_time_string(a.race_time_seconds).ljust(6)
            return_string += get_time_string(a.race_improvement_seconds).ljust(12)
            return_string += "\n"
        return return_string

    def get_goal_time_list(self):
        return_string_list = []
        index = 0;
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

        
    def add_participant(self, name, number, time = None):
        current_participant = None

        current_participant = self.find_participant(name)

        if current_participant == None:
            current_participant = Participant(name)
            current_participant.load()
            self.participants.append(current_participant)

        if time != None:
            # New best time to set.
            current_participant.best_time_seconds = time
        current_participant.number = number

        current_participant.save()
            
        self.participants = sorted(self.participants, key=attrgetter('best_time_seconds'), reverse=True)
        self.longest_time = self.participants[0].best_time_seconds

    def remove_participant(self, name):
        current_participant = self.find_participant(name)

        if current_participant != None:
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
                start_time_seconds = self.longest_time - current_participant.best_time_seconds
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
                    #Only allow removal if no participant assign to time.
                    self.goal_time_list_seconds.pop(index)
            

        
    def save(self):
        if not os.path.isdir(RACE_RESULT_DIR):
            os.makedirs(RACE_RESULT_DIR)
        race_string = self.start_time.strftime("%Y%m%d-%H%M%S")
        file_name = RACE_RESULT_DIR + race_string + ".txt"
        with open(file_name, "w") as write_file:
            write_file.write(self.get_start_list())

        for a in self.participants:
            if a.best_time_seconds > a.race_time_seconds :
                a.best_time_seconds = a.race_time_seconds
            a.store_race(race_string)
            a.save()


race = Race()
root = tk.Tk()
app = Application(master=root, race=race)
app.mainloop()
