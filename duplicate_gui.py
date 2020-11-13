import tkinter as tk
import hashlib
import os
from send2trash import send2trash
from time import time
from functools import partial, update_wrapper
import json
from hyperlink_manager import HyperlinkManager
from PIL import Image, ImageTk
import threading


class StoreHashes(object):
    def __init__(self):
        self.all_hashes = {}
        self.hash_list = []

    def clear(self):
        self.hash_list.clear()

    def addHash(self, hash_list, folder, stat):
        self.all_hashes[(folder, stat)] = hash_list

    def returnHash(self, folder, stat):
        return self.all_hashes[(folder, stat)]

    def resetHash(self, hash_list, folder, stat):
        self.all_hashes[(folder, stat)] = hash_list

    def pop(self, folder, key):
        hashes = self.all_hashes[(folder, "new")]
        del hashes[key]
        self.all_hashes[(folder, "new")] = hashes

    def __call__(self, *args, **kwargs):
        return self.all_hashes


class Counter(object):
    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)

    def __call__(self, obj, *args, **kwargs):
        # start = time()
        result = self.func(obj, *args, **kwargs)
        # end = time()
        # runtime = round(round(end - start) / 60, 2)
        # et = 'Completed - Elapsed time: {} minutes'.format(runtime)
        obj.addToConsole(f"{args[0]} contains {obj.total_file_count} duplicates!")
        return result


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


class GUI:

    def __init__(self):
        self.files = {}
        self.res_dict = {}
        self.hashes = StoreHashes()
        self.files_del = False
        self.delete_all_pressed = False
        self.total_file_count = 0

        self.window = tk.Tk()
        self.window.geometry("800x600")
        self.window.config(bg="black")
        self.window.protocol("WM_DELETE_WINDOW", self.onClose)
        self.window.title("Duplicate Finder")

        self.header = tk.Label(self.window, text="Duplicate Finder", font=("helvetica", 20, "bold"))
        self.header.pack(side="top", fill="x")
        self.header.config(foreground="white", bg="black")

        self.program_body = tk.Frame(self.window, background="black", height=550)
        self.program_body.pack(side="top", fill="x", padx="15")

        self.button_container = tk.Frame(self.program_body, background="black")
        self.button_container.pack(side="bottom", fill="x")

        self.thread = threading.Thread(target=self.duplicate_finder, args=())
        self.thread.daemon = True

        self.start = tk.Button(self.button_container, anchor="e", text="Start",
                               command=self.startMainThread)

        self.start.pack(side="right", anchor="e")

        self.thread2 = threading.Thread(target=self.delete_files, args=())
        self.thread2.daemon = True

        self.delete_all = tk.Button(self.button_container, anchor="e", text="Delete All",
                                    command=self.startSecThread)
        self.delete_all.pack(side="right", anchor="e")

        self.console_header = tk.Label(self.program_body, text="Console:", anchor="w", justify="left",
                                       foreground="white", bg="black",
                                       font=("helvetica", 10))
        self.console_header.pack(side="top", fill="x")

        self.console_body = tk.Frame(self.program_body, height=290, background="gray45")
        self.console_body.pack(side="top", fill="x")

        self.console_text = tk.Text(self.console_body, height=16, font=("Helvetica", 12))
        self.console_text.pack(side="top", fill="both")

        self.spacer = tk.Frame(self.program_body, height=35, background="black")
        self.spacer.pack(side="top", fill="x")

        self.dupe_header = tk.Label(self.spacer, text="Duplicate Images:", anchor="w", justify="left",
                                    foreground="white", bg="black",
                                    font=("helvetica", 10))
        self.dupe_header.pack(side="bottom", fill="x")

        self.dupe_body = tk.Frame(self.program_body, height=200, background="gray40")
        self.dupe_body.pack(side="top", fill="x", pady=5)

        self.dupe_text = tk.Text(self.dupe_body, height=10, font=("Helvetica", 12))
        self.dupe_text.pack(side="top", fill="both")

        self.link = HyperlinkManager(self.dupe_text)

        self.window.mainloop()

    def startMainThread(self):
        try:
            self.thread.start()
        except RuntimeError:
            self.addToConsole("Program has already ran!")
            self.addToConsole("If you want to run again, please restart the program.")

    def startSecThread(self):
        try:
            self.thread2.start()
        except RuntimeError:
            self.addToConsole("You have already deleted all files!")

    def addToConsole(self, value):
        self.console_text.insert(tk.END, f"{value}\n")
        self.console_text.see(tk.END)

    def onClose(self):
        self.save_to_cache()
        self.window.destroy()

    def getFiles(self):
        directory = os.getcwd()
        self.addToConsole("Starting File Crawl!")
        self.addToConsole("Please wait...")
        self.addToConsole("Note: If this is your first run, it may take a bit. Please be patient.")

        for root, dirs, files in os.walk(directory, followlinks=False):
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
                    self.files.update({direct: {"checked": checked, "new": new_check}})

                    cache = {folder: {"checked": checked, "new": new_check}}
                    if not os.path.exists(file):
                        with open(file, "w") as JsonWriter:
                            json.dump(cache, JsonWriter, indent=4)
                else:
                    continue

    def duplicate_finder(self):
        self.getFiles()

        if len(self.files) == 0:
            self.addToConsole("No Duplicates Detected")
            return

        for key, status in self.files.items():
            self.addToConsole(f"Starting {key}...")
            for stat, file_list in status.items():
                self.addToConsole(f"Loading {stat} items...")
                hash_list = []
                folder = os.path.split(key)
                folder_path = key
                if stat == "checked":
                    path = os.path.join(key, "_cache.json")

                    with open(path, "r") as JsonReader:
                        cache = json.load(JsonReader)

                    for c_index, cached_list in enumerate(cache[folder[-1]]["checked"]):
                        hash_list.append(cached_list[1])
                    self.hashes.addHash(hash_list, folder_path, stat)
                else:
                    for index, value in enumerate(file_list):
                        try:
                            with open(value, "rb") as mainFile:
                                image1 = mainFile.read()

                            filehash = hashlib.md5(image1).hexdigest()
                            hash_list.append(filehash)
                        except FileNotFoundError:
                            print("File not found")
                            self.addToConsole("File not found")
                            continue
                    self.hashes.addHash(hash_list, folder_path, stat)
            self.checkFiles(key)

    @Counter
    def checkFiles(self, folder):
        all_files = []
        res_list = []
        hash_dict = {}
        self.total_file_count = 0

        hash_dict["new"] = self.hashes.returnHash(folder, "new")
        hash_dict["checked"] = self.hashes.returnHash(folder, "checked")

        for stat_list in hash_dict.values():
            all_files.extend(stat_list)

        try:
            stat_list = hash_dict["new"]
        except KeyError:
            return

        foldername = os.path.split(folder)

        if not foldername[-1].startswith("c"):
            folder_root = os.path.split(foldername[0])
        else:
            folder_root = ""

        self.dupe_text.insert(tk.END, f"../{folder_root[-1]}/{foldername[-1]}/")
        self.dupe_text.insert(tk.END, "    ")
        self.dupe_text.insert(tk.END, "Remove all from folder\n", self.link.addFolder(self.delete_files, folder, None))
        dupes = Dupes(hash_dict["checked"])
        for index, value in enumerate(stat_list):
            dupe = dupes.find_copies(all_files, value)
            if dupe:
                filename = os.path.split(self.files[folder]["new"][index])
                self.dupe_text.insert(tk.END, f"{filename[-1]}",
                                      self.link.add(self.display_image, index, folder))
                self.dupe_text.insert(tk.END, "    ")
                self.dupe_text.insert(tk.END, "Remove\n", self.link.addRemove(self.delete_files, folder, index))
                self.dupe_text.see(tk.END)
                res_list.append(index)
                self.total_file_count += 1

        self.res_dict.update({folder: res_list})

    """
    def _resize_image(self, event):

        self.image_window.unbind("<Configure>")                                 
        new_height = int(self.width**2 / event.width)
        self.width = int(self.height**2 / event.height)
        self.height = new_height
        self.image_window.geometry(f"{self.width}x{self.height}")
        self.image_window.bind("<Configure>", self._resize_image)

        #self.load = self.image.resize((self.width, self.height))
        #self.render = ImageTk.PhotoImage(self.load)
        #self.image_label.configure(image= self.render)
    """

    def display_image(self, index, folder):
        try:
            if self.image_window:
                self.image_window.destroy()
        except AttributeError:
            pass

        try:
            file = self.files[folder]["new"][index]
        except IndexError:
            self.addToConsole("File has been removed already!")
            return

        self.image_window = tk.Toplevel(self.window)

        self.load = Image.open(file)
        self.image = self.load.copy()

        width, height = self.load.size
        if width > height:
            y = round(height / (width / 500))
            self.image_window.geometry(f"500x{y}")
            self.height = y
            self.width = 500
        else:
            x = round(width / (height / 500))
            self.image_window.geometry(f"{x}x500")
            self.height = 500
            self.width = x

        # self.image_window.bind("<Configure>", self._resize_image)
        self.image_window.resizable(width=False, height=False)

        self.load = self.load.resize((self.width, self.height))
        self.render = ImageTk.PhotoImage(self.load)

        self.image_label = tk.Label(self.image_window, image=self.render)
        self.image_label.pack()

    def delete_files(self, folder="all", file=None):
        if file is None:
            if folder == "all":
                self.delete_all_pressed = True
                if len(self.res_dict) > 0:
                    for folders in self.res_dict:
                        self.delete_files(folders)
                else:
                    self.addToConsole("No files to delete!")
            else:
                if len(self.res_dict[folder]) > 0:
                    res_list = list(self.res_dict[folder])
                    res_list.reverse()

                    for items in res_list:
                        try:
                            if os.path.exists(self.files[folder]["new"][items]):
                                send2trash(self.files[folder]["new"][items])
                                self.addToConsole(f"Duplicate deleted! {self.files[folder]['new'][items]}")
                                self.files[folder]["new"].pop(items)
                                self.hashes.pop(folder, items)
                                self.res_dict[folder].pop(items)
                                self.files_del = True
                        except Exception as e:
                            print(e)
                            continue
                    self.rebuildDupeList()
        else:
            try:
                if os.path.exists(self.files[folder]["new"][file]):
                    send2trash(self.files[folder]["new"][file])
                    self.addToConsole(f"Duplicate deleted! {self.files[folder]['new'][file]}")
                    self.files[folder]["new"].pop(file)
                    self.hashes.pop(folder, file)
                    self.files_del = True
                    updated_res = []
                    self.res_dict[folder].pop(file)
                    for i in self.res_dict[folder]:
                        if i <= file:
                            updated_res.append(i)
                        else:
                            updated_res.append(i-1)
                    self.res_dict[folder] = updated_res
                    self.rebuildDupeList()

            except Exception as e:
                print(e)
                pass

    def rebuildDupeList(self):
        self.dupe_text.delete("1.0", tk.END)
        for folder in self.res_dict:
            if len(self.res_dict[folder]) > 0:
                foldername = os.path.split(folder)

                if not foldername[-1].startswith("c"):
                    folder_root = os.path.split(foldername[0])
                else:
                    folder_root = ""

                self.dupe_text.insert(tk.END, f"../{folder_root[-1]}/{foldername[-1]}/")
                self.dupe_text.insert(tk.END, "    ")
                self.dupe_text.insert(tk.END, "Remove all from folder\n", self.link.addFolder(self.delete_files, folder, None))
                for i in self.res_dict[folder]:
                    filename = os.path.split(self.files[folder]["new"][i])
                    self.dupe_text.insert(tk.END, f"{filename[-1]}",
                                          self.link.add(self.display_image, i, folder))
                    self.dupe_text.insert(tk.END, "    ")
                    self.dupe_text.insert(tk.END, "Remove\n", self.link.addRemove(self.delete_files, folder, i))

    def save_to_cache(self, folder="all"):
        if folder == "all":
            for folder_tuple in self.hashes():
                folders = folder_tuple[0]
                self.save_to_cache(folders)
        else:
            if self.files_del or len(self.hashes()[(folder, "new")]) > 0:
                child = os.path.split(folder)
                new_hashes = self.hashes.returnHash(folder, "new")
                new_zipped = zip(self.files[folder]["new"], new_hashes)
                ch_hashes = self.hashes.returnHash(folder, "checked")
                ch_zipped = zip(self.files[folder]["checked"], ch_hashes)
                joined = [*list(ch_zipped), *list(new_zipped)]
                jsondata = {child[-1]: {"checked": joined}}
                cur_dir = os.getcwd()
                path = os.path.join(cur_dir, folder, "_cache.json")
                with open(path, "w") as JsonWrite:
                    json.dump(jsondata, JsonWrite, indent=4)


if __name__ == "__main__":
    gui = GUI()
