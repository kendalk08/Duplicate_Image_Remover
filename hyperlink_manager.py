from tkinter import CURRENT


class HyperlinkManager:

    def __init__(self, text):

        self.text = text

        self.text.tag_config("hyper", foreground="blue", underline=1, font="Helvetica 12")
        self.text.tag_config("remove", foreground="red", font="Helvetica 12")
        self.text.tag_config("folder", foreground="darkorange", font="Helvetica 12")

        self.text.tag_bind("hyper", "<Enter>", self._enter)
        self.text.tag_bind("hyper", "<Leave>", self._leave)
        self.text.tag_bind("hyper", "<Button-1>", self._click)

        self.text.tag_bind("remove", "<Enter>", self._enter)
        self.text.tag_bind("remove", "<Leave>", self._leave)
        self.text.tag_bind("remove", "<Button-1>", self._click)

        self.text.tag_bind("folder", "<Enter>", self._enter)
        self.text.tag_bind("folder", "<Leave>", self._leave)
        self.text.tag_bind("folder", "<Button-1>", self._click)

        self.links = {}

    def reset(self):
        self.links.clear()

    def add(self, action, index, folder):
        # add an action to the manager.  returns tags to use in
        # associated text widget
        tag = "hyper-%d" % len(self.links)
        self.links[tag] = [action, index, folder]
        return "hyper", tag

    def addRemove(self, action, folder, index):
        # add an action to the manager.  returns tags to use in
        # associated text widget
        tag = "remove-%d" % len(self.links)
        self.links[tag] = [action, folder, index]
        return "remove", tag

    def addFolder(self, action, folder, index):
        # add an action to the manager.  returns tags to use in
        # associated text widget
        tag = "folder-%d" % len(self.links)
        self.links[tag] = [action, folder, index]
        return "folder", tag

    def _enter(self, event):
        self.text.config(cursor="hand2")

    def _leave(self, event):
        self.text.config(cursor="")

    def _click(self, event):
        for tag in self.text.tag_names(CURRENT):
            if tag[:6] == "hyper-":
                self.links[tag][0](self.links[tag][1], self.links[tag][2])
                return
            elif tag[:7] == "remove-":
                self.links[tag][0](self.links[tag][1], self.links[tag][2])
                return
            elif tag[:7] == "folder-":
                self.links[tag][0](self.links[tag][1], self.links[tag][2])
                return
