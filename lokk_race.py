import tkinter as tk
import tkinter.font as font
import datetime
import glob
import os.path
import operator

import raceconfig
import racebase


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
        for file in glob.glob(raceconfig.PARTICIPANTS_DIR + "*.json"):
            path, filename = os.path.split(file)
            name = filename.split('.')[0]
            self.available_racers_list.insert(tk.END, name)
        # self.available_racers_list.bind("<Double-Button-1>", self.select_racer)

        button_frame = tk.Frame(self, background="yellow")
        button_frame.pack(side="right", expand=1, fill=tk.Y)

        racers_frame = tk.Frame(self, background="yellow")
        racers_frame.pack(side="right", expand=1, fill=tk.Y)

        self.participant_label_text = tk.StringVar()
        self.participant_label_text.set("Deltagare")
        participant_label = tk.Label(racers_frame, textvariable=self.participant_label_text, background="yellow")
        participant_label.pack()

        self.racers_list = tk.Listbox(racers_frame, selectmode=tk.SINGLE)
        self.racers_list.pack(expand=1, fill=tk.Y)

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

        self.repor_button = tk.Button(button_frame)
        self.repor_button["text"] = "Rapport"
        self.repor_button["command"] = self.report_pressed
        self.repor_button.pack(side="bottom")

    def add_existing_participant_pressed(self):
        index = int(self.available_racers_list.curselection()[0])
        selected_racer_name = self.available_racers_list.get(index)
        self.race.add_participant(selected_racer_name, self.add_number.get())
        self.add_number.delete(0, tk.END)
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

        self.participant_label_text.set("Deltagare (" + str(len(self.race.participants)) + ")")


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
        self.best_time.insert(0, "50:00")
        self.best_time.pack(side="left")

        self.add_button = tk.Button(self)
        self.add_button["text"] = "Lägg till"
        self.add_button["command"] = self.add_pressed
        self.add_button.pack(side="left")

        self.racers_list = tk.Listbox(self, selectmode=tk.SINGLE)
        self.racers_list.pack(side="right", expand=1, fill=tk.Y)
        for file in glob.glob(raceconfig.PARTICIPANTS_DIR + "*.json"):
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
        racer = racebase.Participant(selected_racer_name)
        racer.load()
        self.best_time.insert(0, racebase.get_time_string(racer.best_time_seconds))

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

        text_font = font.Font(family='Courier', size=14)
        big_font = font.Font(size=25)

        self.start_list = tk.Text(left_frame, font=text_font)
        # TODO: Write protect.
        self.start_list.pack(side="top", expand=1, fill=tk.Y)

        self.start_button = tk.Button(left_frame)
        self.start_button["text"] = "START!"
        self.start_button["command"] = self.start_button_pressed
        self.start_button["font"] = big_font
        self.start_button.pack(side="bottom")

        self.time_label = tk.Label(left_frame, text="00:00", font=text_font)
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

        self.info_text = tk.StringVar()
        self.info_text.set("eller tryck M")
        tk.Label(goal_time_frame, background="yellow", textvariable=self.info_text).pack(side="bottom")
        self.goal_button = tk.Button(goal_time_frame)
        self.goal_button["text"] = "MÅL!"
        self.goal_button["command"] = self.goal_button_pressed
        self.goal_button["font"] = big_font
        self.goal_button.pack(side="bottom")

        # Bind m and M for goal button as well.
        self.bind("m", self.goal_button_pressed)
        self.bind("M", self.goal_button_pressed)

        self.remove_time_button = tk.Button(goal_time_frame, text="Ta bort\nTid")
        self.remove_time_button["command"] = self.remove_time_pressed
        self.remove_time_button.pack(side="right")

        self.manual_time = tk.Entry(goal_time_frame)
        self.manual_time.insert(0, "14:00")
        self.manual_time.pack(side="top")

        self.manual_time_button = tk.Button(goal_time_frame, text="Manuell Tid")
        self.manual_time_button["command"] = self.manual_time_pressed
        self.manual_time_button.pack(side="top")

        self.goal_list = tk.Listbox(goal_time_frame, selectmode=tk.SINGLE, font=text_font)
        self.goal_list.pack(side="top", expand=1, fill=tk.Y)

        self.racers_list = tk.Listbox(racers_frame, selectmode=tk.SINGLE, font=text_font)
        self.racers_list.pack(side="right", expand=1, fill=tk.Y)
        self.racers_list.bind("<Double-Button-1>", self.assign_goal_time)
        for participant in self.race.participants:
            self.racers_list.insert(tk.END, participant.name)

        assign_buttons_frame = tk.Frame(racers_frame, background="yellow")
        assign_buttons_frame.pack(side="left")
        self.race_set_time_button = tk.Button(assign_buttons_frame, text="Sätt tid\n<--")
        self.race_set_time_button["command"] = self.assign_goal_time
        self.race_set_time_button.pack(side="top")

        self.remove_assigned_button = tk.Button(assign_buttons_frame, text="Ångra\n-->")
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

    def manual_time_pressed(self):
        manual_datetime = datetime.datetime.strptime(self.manual_time.get(), "%M:%S")
        time_in_seconds = manual_datetime.minute * 60 + manual_datetime.second
        self.race.add_finish_time(time_in_seconds)
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
        self.start_button["state"] = "disabled"
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
        self.time_label["text"] = racebase.get_time_string(race_duration_seconds)

    def update_goal_list(self):
        goal_time_list = self.race.get_goal_time_list()
        print(goal_time_list)
        self.goal_list.delete(0, tk.END)
        for entry in goal_time_list:
            self.goal_list.insert(tk.END, entry)
        self.info_text.set(str(len(goal_time_list)) + "/" + str(len(self.race.participants)))

    def timer_update(self):
        if (self.racers_list.size() > 0):
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
        season_reports = []

        for file in glob.glob(raceconfig.PARTICIPANTS_DIR + "*.json"):
            path, filename = os.path.split(file)
            name = filename.split('.')[0]
            racer = racebase.Participant(name)
            racer.load()
            racer_report, season_result = racer.get_report()
            print(racer_report)
            self.report_text.insert(tk.END, racer_report)
            self.report_text.insert(tk.END, "\n")
            if season_result is not None:
                season_reports.append(season_result)
        season_reports.sort(key=operator.itemgetter('count'), reverse=True)
        self.report_text.insert(tk.END, "\n\nFlest starter denna säsong\n")
        total_start_count = 0
        for report in season_reports:
            report_string = "\t" + report["name"].ljust(20) + "\t" + str(report["count"]) + " starter\n"
            self.report_text.insert(tk.END, report_string)
            total_start_count += report["count"]
        self.report_text.insert(tk.END, "\nTotalt antal starter: " + str(total_start_count))

        season_reports.sort(key=operator.itemgetter('improvement'), reverse=True)
        self.report_text.insert(tk.END, "\n\nBäst förbättring denna säsong\n")
        for report in season_reports:
            report_string = "\t" + report["name"].ljust(20) + "\t" + racebase.get_time_string(report["improvement"]) + "\n"
            self.report_text.insert(tk.END, report_string)
            total_start_count += report["count"]


race = racebase.Race()
root = tk.Tk()
app = Application(master=root, race=race)
app.mainloop()
