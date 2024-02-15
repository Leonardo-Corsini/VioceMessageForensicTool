import json
import spacy
from Enumerations import Methods
from Utils import walk_on_directory, merge_sort

nlp = spacy.load("it_core_news_lg")

stopwords = nlp.Defaults.stop_words


def stop_words_removal(text: str):
    stop_chars = ["!", "?", ".", ",", ":", "(", ")", "[", "]", ";", "un'", "all'",
                  "dell'", "nell'", "l'"]
    text = text.lower()
    for char in stop_chars:
        if char in text:
            text = text.replace(char, "")
    text_tokens = text.split()

    tokens_without_sw = [word for word in text_tokens if word not in stopwords]

    tokens_without_sw = " ".join(tokens_without_sw)
    return tokens_without_sw


def to_json(line):
    line = line.replace("{'", "{\"").replace("':", "\":").replace("', '", "\", '").replace("'}", "\"}").replace(
        " '", " \"").replace(": ' ", ": \" ").replace("'", " ")
    print(line + "\n\n")

    line = json.loads(line)

    return line

def lemmatize(words):
    doc_lemma = []
    doc = nlp(words)
    for token in doc:
        doc_lemma.append(token.lemma_)
    doc_lemma = " ".join(doc_lemma)

    return doc_lemma


# METHODS
def window_similarity(window, word):
    word = word.lower()
    word_token = nlp(word)

    window = " ".join(window)
    doc_lemma = lemmatize(window)
    doc = nlp(doc_lemma)
    similarity = doc.similarity(word_token)

    return similarity


def calc_similarity_sliding_window(doc, target_word, max_window):
    max_sim = 0
    sliding_window = []
    similarities = []
    doc = doc.split()
    iterations = 0

    if len(doc) <= max_window:
        similarities.append(window_similarity(doc, target_word))
    else:
        for word in doc:
            if iterations < max_window:
                sliding_window.append(word)
            else:
                similarities.append(window_similarity(sliding_window, target_word))
                sliding_window.append(word)
                del sliding_window[0]
            iterations += 1

    for s in similarities:
        if max_sim < s:
            max_sim = s

    return max_sim


def average_similarity(doc, target_word):
    doc = doc.lower()
    target_word = target_word.lower()
    doc_lemma = lemmatize(doc)
    word_lemma = lemmatize(target_word)
    doc = nlp(doc_lemma)
    token = nlp(word_lemma)

    return doc.similarity(token)


def chose_similarity_method(method, text, target):
    if method == Methods.SIMILAR_WORD:
        max_window = 1
        doc = stop_words_removal(text)
        return calc_similarity_sliding_window(doc, target, max_window)
    elif method == Methods.SIMILAR_WINDOW:
        max_window = 4
        doc = stop_words_removal(text)
        return calc_similarity_sliding_window(doc, target, max_window)
    elif method == Methods.DOC_AVERAGE:
        doc = stop_words_removal(text)
        return average_similarity(doc, target)


def get_similarities_from_transcriptions(target, method, case_directory):
    base_dir = case_directory + "/transcriptions/text_data/"
    files = walk_on_directory(base_dir)[2]

    result = []

    for file in files:
        print(file)
        with open(base_dir + file, "r", errors='ignore') as trans:
            text = trans.read()
            transcription_data = text.split("\n")

            if "" in transcription_data:
                transcription_data.remove("")

            full_text = ""
            for line in transcription_data:
                line = to_json(line)
                full_text = full_text + line["text"]

            similarity = chose_similarity_method(method, full_text, target)

            similarity_data = {'filename': file, 'text': full_text, 'similarity': similarity}
            result.append(similarity_data)

    merge_sort(result)
    data = [method, result[:100]]

    return data


def search_similar_words(word, method, case_directory):
    word = stop_words_removal(word)
    word = lemmatize(word)

    result = get_similarities_from_transcriptions(word, method, case_directory)

    return result

