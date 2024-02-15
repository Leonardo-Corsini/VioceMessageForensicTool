import os


def walk_on_directory(files_dir):
    tree_dir = os.walk(files_dir)

    for test_dir, files_subdir, files in tree_dir:
        print(f"Dir: '{test_dir}'")
        print(f"Subdir: '{files_subdir}'")
        print(f"Files: {files}")
        print("Number: ", len(files))
    return test_dir, files_subdir, files


def get_subdirectories(basepath):
    sub_dirs = []
    with os.scandir(basepath) as entries:
        for entry in entries:
            if entry.is_dir():
                sub_dirs.append(entry.name)
    return sub_dirs


def get_filename(path):
    file_name, file_extention = os.path.splitext(path)
    file_name = file_name.split("/")

    return file_name[-1], file_extention


def state(targets, case_directory):
    files_to_process = []
    with open(case_directory + "/transcriptions/state.txt", "r") as process_state:
        files = process_state.read().split('\n')
        files.remove('')
    print(files)
    print(targets)
    for target in targets:
        if target not in files:
            files_to_process.append(target)
    print("NUMBER OF FILES ALREADY DONE: ", len(files))
    print("NUMBER OF FILES TO BE PROCESSED ", len(files_to_process))
    print(targets)
    return files_to_process



def merge(arr, temp, first, mid, last):
    a = first
    b = first
    c = mid + 1

    while b <= mid and c <= last:
        if arr[b]["similarity"] > arr[c]["similarity"]:
            temp[a] = arr[b]
            b = b + 1
        else:
            temp[a] = arr[c]
            c = c + 1
        a = a + 1

    # remaining elements
    while b < len(arr) and b <= mid:
        temp[a] = arr[b]
        a = a + 1
        b = b + 1

    # copy back
    for b in range(first, last + 1):
        arr[b] = temp[b]


# Iterative sort
def merge_sort(arr):
    low = 0
    high = len(arr) - 1

    # sort list
    temp = arr.copy()

    d = 1
    while d <= high - low:

        for b in range(low, high, 2 * d):
            first = b
            mid = b + d - 1
            last = min(b + 2 * d - 1, high)
            merge(arr, temp, first, mid, last)

        d = 2 * d