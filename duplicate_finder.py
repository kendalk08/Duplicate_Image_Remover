import hashlib
import os
from send2trash import send2trash
from time import time
from functools import wraps
import json

"""
Please read the readme.txt before running this program.

Nothing in this script needs to be changed to run correctly it will crawl through 
directories for you. 
"""


total_file_count = 0

class Dupes:
    def __init__(self, root_list):
        self.value_list = []

        for i in root_list:
            self.add_value(i)

    def find_copies(self, sent_list, value):
        if value in self.value_list:
            for j in sent_list:
                if j == value:
                    return True
            return False
        else:
            self.add_value(value)
            return False

    def add_value(self, value):
        if value not in self.value_list:
            self.value_list.append(value)

def timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print('{} - Elapsed time: {}'.format(f.__name__, end - start))
        return result

    return wrapper


def getFiles():
    directory = os.getcwd()
    folder_names = {}

    for root, dirs, files in os.walk(directory):
        for folder in dirs:
            new_check = []
            checked = []
            direct = os.path.join(root, folder)

            file = os.path.join(direct, "_cache.json")
            if os.path.exists(file):
                with open(file, "r") as JsonReader:
                    file_dict = json.load(JsonReader)
                c_list = file_dict[folder]["checked"]

                for a in c_list:
                    checked.append(a[0])

                for filename in os.listdir(direct):
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        filepath = os.path.join(direct, filename)
                        if filepath not in checked:
                            new_check.append(filepath)
            else:
                for filename in os.listdir(direct):
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        filepath = os.path.join(direct, filename)
                        new_check.append(filepath)

            if len(new_check) != 0:
                folder_names.update({folder: {"checked": checked, "new": new_check}})

                cache = {folder: {"checked": checked, "new": new_check}}
                if not os.path.exists(file):
                    with open(file, "w") as JsonWriter:
                        json.dump(cache, JsonWriter, indent=4)
            else:
                continue

    if len(folder_names) != 0:
        return folder_names
    else:
        return False


@timing
def duplicate_finder():
    files = getFiles()

    if not files:
        return

    hash_dict = {}

    for key, status in files.items():
        print(f"Starting {key}...")
        for stat, file_list in status.items():
            print(f"Hashing {stat}")
            stat_dict = {}
            if stat == "checked":
                path = os.path.join(os.getcwd(), key, "_cache.json")
                with open(path, "r") as JsonReader:
                    cache = json.load(JsonReader)
                for c_index, cached_list in enumerate(cache[key]["checked"]):
                    stat_dict.update({c_index: cached_list[1]})

                hash_dict.update({stat: stat_dict})
            else:
                for index, value in enumerate(file_list):
                    try:
                        with open(value, "rb") as mainFile:
                            image1 = mainFile.read()

                        filehash = hashlib.md5(image1).hexdigest()
                        stat_dict.update({index: filehash})
                    except FileNotFoundError:
                        print("File not found")
                        continue
                if len(file_list) != 0:
                    hash_dict.update({stat: stat_dict})
        checkFiles(hash_dict, key, files)


def checkFiles(hash_dict, folder, files):
    res_list = []
    all_files = {}
    index = 0
    files_del = False

    global total_file_count
    for stat, stat_dict in hash_dict.items():
        for f_list in stat_dict:
            all_files.update({index: stat_dict[f_list]})
            index += 1

    stat_dict = hash_dict["new"]
    dupes = Dupes(hash_dict["checked"].values())
    for key, value in stat_dict.items():
        dupe = dupes.find_copies(all_files.values(), value)
        if dupe:
            res_list.append(key)

    if len(res_list) > 0:
        res_list = list(dict.fromkeys(res_list))
        res_list.reverse()
        for items in res_list:
            if os.path.exists(files[folder]["new"][items]):
                send2trash(files[folder]["new"][items])
                print(f"Duplicate deleted! {files[folder]['new'][items]}")
                files[folder]["new"].pop(items)
                hash_dict["new"].pop(items)
                total_file_count += 1
                files_del = True

    if files_del or len(hash_dict["new"]) > 0:
        new_hashes = hash_dict["new"].values()
        new_zipped = zip(files[folder]["new"], new_hashes)
        ch_hashes = hash_dict["checked"].values()
        ch_zipped = zip(files[folder]["checked"], ch_hashes)
        joined = [*list(ch_zipped), *list(new_zipped)]
        jsondata = {folder: {"checked": joined}}
        cur_dir = os.getcwd()
        path = os.path.join(cur_dir, folder, "_cache.json")
        with open(path, "w") as JsonWrite:
            json.dump(jsondata, JsonWrite, indent=4)


if __name__ == "__main__":
    duplicate_finder()
    print(total_file_count)
