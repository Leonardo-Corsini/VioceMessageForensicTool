import whisper_timestamped as whisper

from Utils import walk_on_directory, state, get_filename

model = whisper.load_model("large")


def take_transcribe_state(target, targets_directory, case_directory):
    target_path = targets_directory + "/" + target
    file_name, file_extention = get_filename(target_path)

    transcription = stt(target_path)

    with open(case_directory + "/transcriptions/text_data/" + file_name + ".txt", "w", encoding="utf-8") as file_transcription:
        for item in transcription:
            start = float(item["start"])
            end = float(item["end"])
            duration = end - start
            dict_transcription = {"text": item["text"], "start": str(item["start"]), "end": str(item["end"]), "duration": str(duration)}
            file_transcription.write("%s\n" % dict_transcription)
    with open(case_directory + "/transcriptions/state.txt", "a", encoding="utf-8") as transcription_state:
        file_done = file_name + file_extention
        transcription_state.write(''.join(file_done) + '\n')


def stt(audio):

    output = model.transcribe(audio, fp16=False, language='Italian')

    return output["segments"]


def transcription_process(directory, stop,  case_directory):
    work_dir, files_subdir, targets = walk_on_directory(directory)
    targets = state(targets, case_directory)
    for target in targets:
        if not stop.get_stop():
            take_transcribe_state(target, directory, case_directory)
            print("transcription")
        else:
            stop.set_stopped(True)
            print("stop")
            break
