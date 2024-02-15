import tkinter
from math import ceil, floor
from threading import Thread
import customtkinter
from customtkinter import filedialog
from PIL import Image
from Enumerations import Methods
import os
from Utils import get_subdirectories, get_filename
from Concurrency import Analyzer, AnalyzedData, Transcriber, StopTranscriber
import textwrap
import vlc


customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")
default_font = 'Helvetica'


class AnalysisPageCreated:
    def __init__(self):
        self.page_created = False

    def set_page_created(self, bool):
        self.page_created = bool

    def get_page_created(self):
        page = self.page_created
        return page


class ReportStarter(Thread):
    def __init__(self, data, case_name, search_word, files_dir, case_evidence_dir, page_creation):
        Thread.__init__(self)
        self.data = data
        self.case_name = case_name
        self.search_word = search_word
        self.files_dir = files_dir
        self.case_evidence_dir = case_evidence_dir
        self.page_creation = page_creation

    def run(self):
        mutex = self.data.get_mutex()
        mutex.acquire()
        result_data = self.data.get_result_data()
        page = AnalysisPage(case_name=self.case_name, search_word=self.search_word, result_data=result_data,
                            files_dir=self.files_dir, case_evidence_dir=self.case_evidence_dir)
        page.lift()
        page.attributes("-topmost", 1)
        page.after_idle(page.attributes, '-topmost', False)
        self.page_creation.set_page_created(True)
        mutex.release()


class TitleFrame(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.label = customtkinter.CTkLabel(master=self, text="Voice Message Forensic Tool",
                                            font=(default_font, 100, 'bold'), text_color="#1F6AA5", corner_radius=10)
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="news")


class SelectionButton(customtkinter.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=2, column=1, rowspan=2, columnspan=2, sticky="news", pady=10)


class TranscriptFrame(customtkinter.CTkFrame):
    def __init__(self, master, case_evidence_directory, files_directory, **kwargs):
        super().__init__(master, **kwargs)

        # usefull parameters
        self.case_evidence_directory = case_evidence_directory
        self.base_directory = files_directory
        self.number_of_files = len([name for name in os.listdir(self.base_directory) if os.path.isfile(os.path.join(self.base_directory, name))])
        print(self.number_of_files)
        self.stop_transcription = StopTranscriber()

        # create tabs
        self.transcript_completed_frame = None
        self.textbox = None

        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=4)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=6)
        self.grid_columnconfigure(2, weight=1)

        # Title
        self.label = customtkinter.CTkLabel(master=self, text="TRANSCRIPTION", font=(default_font, 40, 'bold'))
        self.label.grid(row=0, column=1,  sticky="wns")
        self.label = customtkinter.CTkLabel(master=self,
                                            text="Transcription status",
                                            font=(default_font, 20))
        self.label.grid(row=1, column=1,  sticky="wn", pady=10)

        # Progress bar
        self.progress_bar = customtkinter.CTkProgressBar(master=self, border_width=3, corner_radius=5, height=30, progress_color="#46c263")
        beginning_status = len([name for name in os.listdir(self.case_evidence_directory + "/transcriptions/text_data/") if
                            os.path.isfile(os.path.join(self.case_evidence_directory + "/transcriptions/text_data/", name))])
        if beginning_status == 0:
            self.progress_bar.set(0)
        else:
            self.progress_bar.set(beginning_status / self.number_of_files)

        self.progress_bar.grid(row=1, column=1, sticky="ew")

        # Button
        self.button_label = customtkinter.CTkLabel(master=self,
                                            text="Click button to START transcription process",
                                            font=(default_font, 20))
        self.button_label.grid(row=1, column=1, sticky="ws", pady=15)
        img = customtkinter.CTkImage(light_image=Image.open("Images/icona_trascrizione.png"),
                                     dark_image=Image.open("Images/icona_trascrizione.png"),
                                     size=(200, 200))
        self.transcript_button = customtkinter.CTkButton(master=self, image=img, text="", border_width=3,
                                                         command=self.button_click)
        self.transcript_button.grid(row=2, column=1, sticky="news", pady=10)

    def ask_dir(self, event):
        self.base_directory = filedialog.askdirectory()

    def update_progress(self):
        files_number = len([name for name in os.listdir(self.case_evidence_directory + "/transcriptions/text_data/") if os.path.isfile(os.path.join(self.case_evidence_directory + "/transcriptions/text_data/", name))])
        print(files_number)
        if files_number == 0:
            self.progress_bar.set(0)
        else:
            self.progress_bar.set(files_number/self.number_of_files)
        if files_number < self.number_of_files and not self.stop_transcription.get_stop():
            self.after(5000, self.update_progress)
        else:
            return

    def finalizing(self, dots, count):
        self.button_label.configure(text="Finalizing" + dots)
        if count < 3:
            dots += "."
            count += 1
        else:
            dots = ""
            count = 0
        if not self.stop_transcription.get_stopped():
            self.after(1000, lambda: self.finalizing(dots, count))
        else:
            self.button_label.configure(text="Click button to START transcription process")
            self.transcript_button.configure(fg_color="#1f538d", hover=True, hover_color="#14375e",
                                             command=self.button_click, state="normal")

    def stop(self):
        self.stop_transcription.set_stop(True)
        self.transcript_button.configure(state="disabled", hover="False")
        self.finalizing("", 0)

    def button_click(self):
        self.stop_transcription.set_stop(False)
        transcriber = Transcriber(self.base_directory, self.stop_transcription, self.case_evidence_directory)
        transcriber.start()
        self.update_progress()
        self.transcript_button.configure(fg_color="#FC3D39", hover_color="#E33437", command=self.stop)
        self.button_label.configure(text="Click button to STOP transcription process")


class SearchFrame(customtkinter.CTkFrame):

    def __init__(self, master, case_name, case_evidence_directory, files_dir, **kwargs):
        super().__init__(master, **kwargs)

        self.case_name = case_name

        # Usefully parameters
        self.analysis_page = None
        self.base_directory = case_evidence_directory
        self.files_dir = files_dir

        # create tabs
        self.transcript_completed_frame = None
        self.textbox = None

        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=4)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=3)
        self.grid_columnconfigure(3, weight=1)

        # Title
        self.label = customtkinter.CTkLabel(self, text="SEARCH", font=(default_font, 40, 'bold'))
        self.label.grid(row=0, column=1, columnspan=2, sticky="wns")
        self.label = customtkinter.CTkLabel(self, text="Search bar",
                                            font=(default_font, 20))
        self.label.grid(row=1, column=1, columnspan=2, sticky="wn", pady=10)

        # search bar
        self.search = customtkinter.CTkEntry(master=self, border_width=3, corner_radius=5)
        self.search.grid(row=1, column=1, sticky="ew")
        self.search.bind("<Any-KeyRelease>", self.enable_button)

        # Button
        self.button_label = customtkinter.CTkLabel(master=self,
                                                   text="Click button to START searching",
                                                   font=(default_font, 20))
        self.button_label.grid(row=1, column=1, columnspan=2, sticky="ws", pady=15)

        img = customtkinter.CTkImage(light_image=Image.open("Images/Icona_analisi.png"),
                                     dark_image=Image.open("Images/Icona_analisi.png"),
                                     size=(200, 200))
        self.search_button = customtkinter.CTkButton(master=self, image=img, text="", border_width=3,
                                                     fg_color="grey",
                                                     state="disabled",
                                                     command=self.button_click)
        self.search_button.grid(row=2, column=1, columnspan=2, sticky="news", pady=10)

    def enable_button(self, event):
        search = self.search.get()
        if search != "" and self.search_button.cget("state") == "disabled":
            self.search_button.configure(state="normal", hover=True, fg_color="#1F6AA5")
            self.search_button.grid(row=2, column=1, sticky="news", pady=10)
        elif search == "" and self.search_button.cget("state") == "normal":
            self.search_button.configure(state="disabled", hover=False, fg_color="grey")
            self.search_button.grid(row=2, column=1, sticky="news", pady=10)

    def wait_for_page_creation(self, progress_bar, is_created):
        if not is_created.get_page_created():
            self.after(1000, lambda: self.wait_for_page_creation(progress_bar, is_created))
        else:
            progress_bar.destroy()
            self.search_button.configure(state="normal", hover=True)
            self.search.configure(state="normal")

    def button_click(self):
        is_created = AnalysisPageCreated()
        self.search_button.configure(state="disabled")
        self.search.configure(state="disable")
        progress_bar = customtkinter.CTkProgressBar(master=self, border_width=3, corner_radius=5, height=30, width=140,
                                                    mode="indeterminate", progress_color="#46c263")
        progress_bar.grid(row=1, column=2)
        progress_bar.start()
        search_word = self.search.get()
        data = AnalyzedData()
        # THREADS che avviano i metodi di analisi
        threads = [Analyzer(method=Methods.SIMILAR_WINDOW, data=data, search_word=search_word,
                            case_evidence_directory=self.base_directory),
                   Analyzer(method=Methods.SIMILAR_WORD, data=data, search_word=search_word,
                            case_evidence_directory=self.base_directory),
                   Analyzer(method=Methods.DOC_AVERAGE, data=data, search_word=search_word,
                            case_evidence_directory=self.base_directory)
                   ]
        analysis_starter_thread = ReportStarter(data=data, case_name=self.case_name,
                                                search_word=search_word,
                                                files_dir=self.files_dir,
                                                case_evidence_dir=self.base_directory,
                                                page_creation=is_created)
        for thread in threads:
            thread.start()
        analysis_starter_thread.start()
        self.wait_for_page_creation(progress_bar, is_created)


class AudioFrame(customtkinter.CTkFrame):
    def __init__(self, master, audio_name, audio_text, similarity, files_dir, case_evidence_dir, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)
        self.grid_columnconfigure(2, weight=1)
        # self.grid_columnconfigure(3, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)

        self.case_evidence_dir = case_evidence_dir
        self.files_dir = files_dir
        self.audio_name = audio_name

        self.label = customtkinter.CTkLabel(self, text=audio_name,
                                            font=(default_font, 20, 'bold'),
                                            text_color="#1F6AA5")
        self.label.grid(row=0, column=0)
        titles = [customtkinter.CTkLabel(self, text="Text",
                                         font=(default_font, 15, 'bold'),
                                         text_color="#1F6AA5"),
                  # customtkinter.CTkLabel(self, text="Start time",
                  #                        font=(default_font, 15, 'bold'),
                  #                        text_color="#1F6AA5"),

                  customtkinter.CTkLabel(self, text="Similarity",
                                         font=(default_font, 15, 'bold'),
                                         text_color="#1F6AA5")
                  ]
        titles[0].grid(row=0, column=1
                       )

        titles[1].grid(row=0, column=2, sticky="we")

        img = customtkinter.CTkImage(light_image=Image.open("Images/icona_audio.png"),
                                     dark_image=Image.open("Images/icona_audio.png"),
                                     size=(30, 30))
    
        self.audio_icon = customtkinter.CTkButton(master=self, image=img, text="", fg_color="transparent", command=self.play_audio)
        self.audio_icon.grid(row=1, column=0)

        # Inserisce un numero massimo di caratteri nella riga della label prima di andare a capo
        audio_text = textwrap.fill(audio_text, width=140)

        self.audio_text = customtkinter.CTkLabel(master=self, text=audio_text, width=700)
        self.audio_text.grid(row=1, column=1, pady=5)
        self.similarity = customtkinter.CTkLabel(master=self, text=similarity)
        self.similarity.grid(row=1, column=2)

    def stop_audio(self,audio):
        audio.stop()

    def play_audio(self):
        name = get_filename(self.audio_name)[0]

        with open(self.case_evidence_dir + "/transcriptions/state.txt") as files:
            targets = files.read().split("\n")
            for target in targets:
                if name == get_filename(target)[0]:
                    audio_file = target
                    break

        audio = vlc.MediaPlayer(self.files_dir + "/" + audio_file)
        audio.play()


class ResultFrame(customtkinter.CTkFrame):
    def __init__(self, master, files_dir, result, case_evidence_dir, **kwargs):
        super().__init__(master, **kwargs)

        class Scrollable(customtkinter.CTkScrollableFrame):
            def __init__(self, master, analysis_result, case_evidence_dir, **kwargs):
                super().__init__(master, **kwargs)

                self.audio_list = []
                self.grid_columnconfigure(0, weight=1)

                # Genera i frame degli audio e solo se la similarity > 0.35
                def generate_audio_frame(loop_result, count):
                    if count < len(loop_result):
                        item = loop_result[count]
                        if item['similarity'] > 0.4:
                            audio = AudioFrame(master=self, audio_name=item['filename'],
                                               audio_text=item['text'],
                                               similarity=str(
                                                   round(item['similarity'] * 100, 2)) + "%", files_dir=files_dir,
                                               case_evidence_dir=case_evidence_dir)
                            audio.grid(row=len(self.audio_list), column=0, pady=5, sticky="we")
                            self.audio_list.append(audio)
                            count += 1
                            after = self.after(100, lambda: generate_audio_frame(loop_result=loop_result, count=count))
                            second_after = self.after(101, lambda: self.after_cancel(after))
                            self.after_cancel(second_after)
                        else:
                            return

                generate_audio_frame(loop_result=analysis_result, count=0)

        self.scroll = Scrollable(master=self, analysis_result=result, width=1600, height=1000, case_evidence_dir=case_evidence_dir)
        self.scroll.pack(padx=10)


class AnalysisPage(customtkinter.CTkToplevel):
    def __init__(self, case_name, search_word, files_dir, result_data, case_evidence_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.average_result = None
        self.similar_word_results = None
        self.similar_window_results = None
        self.results = []
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()

        self.title(case_name)
        self.minsize(int(width * 0.8), int(height * 0.8))

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)

        self.page_title = customtkinter.CTkLabel(master=self, text=search_word,
                                                 font=(default_font, 30, 'bold'), text_color="#1F6AA5",
                                                 corner_radius=10)
        self.page_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nws")
        self.tabview = customtkinter.CTkTabview(master=self)
        self.tabview.add("Window")
        self.tabview.add("Word")
        self.tabview.add("Average")
        self.tabview.grid(row=1, column=0, columnspan=2, sticky="news")

        def result_chooser(result):
            if result[0] == Methods.SIMILAR_WINDOW:
                self.similar_window_results = result[1]

            elif result[0] == Methods.SIMILAR_WORD:
                self.similar_word_results = result[1]

            elif result[0] == Methods.DOC_AVERAGE:
                self.average_result = result[1]

        for item in result_data:
            result_chooser(item)

        self.window_sim_frame = ResultFrame(master=self.tabview.tab("Window"),
                                            result=self.similar_window_results, files_dir=files_dir, case_evidence_dir=case_evidence_dir)
        self.window_sim_frame.grid(row=0, column=0, sticky="news")

        self.word_sim_frame = ResultFrame(master=self.tabview.tab("Word"),
                                          result=self.similar_word_results, files_dir=files_dir, case_evidence_dir=case_evidence_dir)
        self.word_sim_frame.grid(row=0, column=0, sticky="news")

        self.average_similarity = ResultFrame(master=self.tabview.tab("Average"),
                                              result=self.average_result, files_dir=files_dir,
                                              case_evidence_dir=case_evidence_dir)
        self.average_similarity.grid(row=0, column=0, sticky="news")


class CasePage(customtkinter.CTkToplevel):
    def __init__(self, case_name, case_evidence_directory, files_directory, *args, **kwargs):
        super().__init__(*args, **kwargs)

        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()

        self.title(case_name)
        self.minsize(int(width * 0.8), int(height * 0.8))

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=3)

        self.page_title = customtkinter.CTkLabel(master=self, text=case_name,
                                                 font=(default_font, 100, 'bold'), text_color="#1F6AA5",
                                                 corner_radius=10)
        self.page_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nws")
        # add widgets to app

        self.transcript_frame = TranscriptFrame(master=self, case_evidence_directory=case_evidence_directory,
                                                files_directory=files_directory)
        self.transcript_frame.grid(row=1, column=0, rowspan=2, padx=10, pady=20, sticky="news")

        self.search_frame = SearchFrame(master=self, case_name=case_name,
                                        case_evidence_directory=case_evidence_directory, files_dir=files_directory)
        self.search_frame.grid(row=1, rowspan=2, column=1, padx=10, pady=20, sticky="news")


class MainPage(customtkinter.CTk):

    def __init__(self):
        super().__init__()

        self.buttons = []
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()

        self.title("Voice message forensic tool")
        self.minsize(int(width * 0.8), int(height * 0.8))

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)
        self.grid_rowconfigure(2, weight=2)

        self.page_title = customtkinter.CTkLabel(master=self, text="Voice Message Forensic Tool",
                                                 font=(default_font, 100, 'bold'), text_color="#1F6AA5",
                                                 corner_radius=10)
        self.page_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nwe")

        ##########################
        ####### OPEN CASE ########
        ##########################
        self.scroll_cases = customtkinter.CTkScrollableFrame(master=self, label_text="Open a case",
                                                             label_font=(default_font, 30, 'bold'),
                                                             label_fg_color="transparent")
        self.scroll_cases.grid(row=1,
                               column=0,
                               padx=20,
                               pady=10,
                               sticky="nwse")

        files_subdir = get_subdirectories("Cases")
        print(files_subdir)

        class ButtonCase(customtkinter.CTkButton):
            def __init__(self, case_name, *args, **kwargs):
                super().__init__(*args, **kwargs)

                self.case_name = case_name
                self.configure(command=lambda: self.open_case(case_name=self.case_name))

            def open_case(self, case_name):
                case_directory = "Cases/" + case_name

                # TODO mettere possibilità di avere più reperti
                evidence_number = get_subdirectories(case_directory)[0]
                with open(case_directory + "/" + evidence_number + "/" + evidence_number + "_case_info.txt",
                          'r') as info_file:
                    info = info_file.read()
                    info = info.split("\n")
                    files_directory = info[0].replace("Directory: ", "")
                case = CasePage(case_name=case_name,
                                case_evidence_directory=case_directory + "/" + evidence_number,
                                files_directory=files_directory)

                case.attributes("-topmost", 1)
                case.after_idle(case.attributes, '-topmost', False)

        for directory in files_subdir:
            ButtonCase(master=self.scroll_cases,
                       width=400,
                       text=directory, case_name=directory).pack(padx=5, pady=5)

        # NEW CASE
        class NewCaseFrame(customtkinter.CTkFrame):
            def __init__(self, master, scroll, **kwargs):
                super().__init__(master, **kwargs)
                self.scroll = scroll
                self.case_page = None
                self.examiner_name = ""
                self.evidence_number = ""
                self.case_name = ""

                self.base_directory = ""
                self.grid_columnconfigure(0, weight=1)
                self.grid_columnconfigure(1, weight=1)

                self.grid_rowconfigure(0, weight=1)
                self.grid_rowconfigure(1, weight=1)
                self.grid_rowconfigure(2, weight=1)
                self.grid_rowconfigure(3, weight=1)
                self.grid_rowconfigure(4, weight=1)
                self.grid_rowconfigure(5, weight=1)

                self.label = customtkinter.CTkLabel(self, text="New case", font=(default_font, 30, 'bold'))
                self.label.grid(row=0,
                                column=0,
                                pady=5,
                                columnspan=2,
                                sticky="nwe")

                ######################
                ##### CASE NAME ######
                ######################
                self.enter_case_name_label = customtkinter.CTkLabel(master=self,
                                                                    text="Insert case name",
                                                                    font=(default_font, 18))
                self.enter_case_name_label.grid(row=1,
                                                column=0,
                                                padx=10,
                                                sticky="wn")
                self.enter_case_name = customtkinter.CTkEntry(master=self,
                                                              placeholder_text="case name",
                                                              font=(default_font, 16))
                self.enter_case_name.grid(row=1,
                                          column=0,
                                          padx=10,
                                          sticky="we")
                self.enter_case_name.bind("<Any-KeyRelease>", self.case_name_changed)

                ######################
                #### PROVE NUMBER ####
                ######################
                self.enter_evidence_number_label = customtkinter.CTkLabel(master=self,
                                                                          text="Insert evidence number",
                                                                          font=(default_font, 18))
                self.enter_evidence_number_label.grid(row=2,
                                                      column=0,
                                                      padx=10,
                                                      sticky="wn",
                                                      )
                self.enter_evidence_number = customtkinter.CTkEntry(master=self,
                                                                    placeholder_text="evidence number",
                                                                    font=(default_font, 16))
                self.enter_evidence_number.grid(row=2,
                                                column=0,
                                                padx=10,
                                                sticky="we")
                self.enter_evidence_number.bind("<Any-KeyRelease>", self.evidence_number_changed)

                ######################
                #### EXAMINER NAME ###
                ######################
                self.enter_examiner_name_label = customtkinter.CTkLabel(master=self,
                                                                        text="Insert examiner name",
                                                                        font=(default_font, 18))
                self.enter_examiner_name_label.grid(row=3,
                                                    column=0,
                                                    padx=10,
                                                    sticky="nw",
                                                    )
                self.enter_examiner_name = customtkinter.CTkEntry(master=self,
                                                                  placeholder_text="examiner",
                                                                  font=(default_font, 16))
                self.enter_examiner_name.grid(row=3,
                                              column=0,
                                              padx=10,
                                              sticky="we",
                                              )

                ######################
                #### AUDIO FILES #####
                ######################
                self.enter_case_audio_label = customtkinter.CTkLabel(master=self,
                                                                     text="Choose files directory",
                                                                     font=(default_font, 18))
                self.enter_case_audio_label.grid(row=4,
                                                 column=0,
                                                 padx=10,
                                                 columnspan=2,
                                                 sticky="nw")

                self.enter_case_audio_files = customtkinter.CTkEntry(master=self,
                                                                     placeholder_text=self.base_directory,
                                                                     font=(default_font, 16))

                self.enter_case_audio_files.grid(row=4,
                                                 column=0,
                                                 padx=10,
                                                 columnspan=2,
                                                 sticky="we")
                self.enter_case_audio_files.bind(sequence='<Button-1>', command=self.ask_dir)

                ######################
                ### SUBMIT BUTTON ####
                ######################
                self.submit_button = customtkinter.CTkButton(master=self, text="Submit", font=(default_font, 16),
                                                             state="disabled", command=self.submit)
                self.submit_button.grid(row=5,
                                        column=0,
                                        padx=10,
                                        columnspan=2)

            def enable_button(self):
                if self.case_name != "" and self.evidence_number != "" and self.base_directory != "":
                    self.submit_button.configure(state="normal", hover=True)
                else:
                    self.submit_button.configure(state="disabled", hover=True)

            def case_name_changed(self, event):
                self.case_name = self.enter_case_name.get()
                print(self.case_name)
                self.enable_button()

            def evidence_number_changed(self, event):
                self.evidence_number = self.enter_evidence_number.get()
                print(self.evidence_number)
                self.enable_button()

            def ask_dir(self, event):
                self.base_directory = filedialog.askdirectory()
                self.enter_case_audio_files.delete(0, customtkinter.END)
                self.enter_case_audio_files.insert(0, self.base_directory)
                self.enable_button()

            def submit(self):
                # Viene creato il caso con le relative directory e viene inserito il button del caso nella gui
                self.examiner_name = self.enter_examiner_name.get()
                cases_dir = "Cases/"
                os.mkdir(cases_dir + self.case_name)
                os.mkdir(cases_dir + self.case_name + "/" + self.evidence_number)
                os.mkdir(cases_dir + self.case_name + "/" + self.evidence_number + "/transcriptions")
                os.mkdir(cases_dir + self.case_name + "/" + self.evidence_number + "/transcriptions/text_data")
                open(cases_dir + self.case_name + "/" + self.evidence_number + "/transcriptions/state.txt", 'w')
                with open("Cases/" + self.case_name + "/" + self.evidence_number + "/" + self.evidence_number + "_case_info.txt", "x") as file:
                    file.write("Directory: " + self.base_directory + "\n" +
                               "Examiner name: " + self.examiner_name)
                self.case_page = CasePage(case_name=self.case_name,
                                          case_evidence_directory=cases_dir + self.case_name + "/" + self.evidence_number,
                                          files_directory=self.base_directory)

                self.case_page.attributes("-topmost", 1)
                self.case_page.after_idle(self.case_page.attributes, '-topmost', False)
                customtkinter.CTkButton(master=self.scroll,
                                        width=400,
                                        text=self.case_name).pack(padx=5, pady=5)

        self.new_case = NewCaseFrame(master=self, corner_radius=4, scroll=self.scroll_cases)
        self.new_case.grid(row=1,
                           column=1,
                           padx=20,
                           pady=10,
                           sticky="news")


main_page = MainPage()

main_page.iconbitmap('Images/icona.ico')

main_page.mainloop()
