from threading import Thread, Semaphore
from transcription_analizer_methods import search_similar_words
from S2T_methods import transcription_process


class AnalyzedData:
    def __init__(self, ):
        self.analyses_result = []
        self.finished = 0
        self.mutex = Semaphore(0)
        self.data_mutex = Semaphore()

    def get_mutex(self):
        return self.mutex

    def put_data(self, data):
        self.data_mutex.acquire()
        self.analyses_result.append(data)
        self.finished += 1
        if self.finished == 3:
            self.mutex.release()
        self.data_mutex.release()

    def get_result_data(self):
        data = self.analyses_result
        return data


class Analyzer(Thread):
    def __init__(self, method, data, search_word, case_evidence_directory):
        Thread.__init__(self)
        self.method = method
        self.data = data
        # self.work_dir = work_dir
        self.search_word = search_word
        self.case_evidence_directory = case_evidence_directory

    def run(self):
        data = search_similar_words(self.search_word, self.method, self.case_evidence_directory)
        self.data.put_data(data)


class StopTranscriber:
    def __init__(self):
        self.stop = False
        self.stopped = False

    def set_stop(self, stop):
        self.stop = stop

    def get_stop(self):
        stop = self.stop
        return stop

    def set_stopped(self, stopped):
        self.stopped = stopped

    def get_stopped(self):
        stopped = self.stopped
        return stopped


class Transcriber(Thread):
    def __init__(self, data_directory, stop,  case_evidence_directory):
        Thread.__init__(self)
        self.data_directory = data_directory
        self.case_evidence_directory = case_evidence_directory
        self.stop = stop

    def run(self):
        transcription_process(self.data_directory, self.stop, self.case_evidence_directory)
