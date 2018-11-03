from tkinter import *


def min_limit_check(svar):
    min = svar.get()

    if len(min) > 3:
        svar.set(min[:3])


def sec_limit_check(svar):
    sec = svar.get()

    if len(sec) > 2:
        svar.set(sec[:2])


class verification_window():
    def on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def __init__(self, master, tracklist):
        self.master = master
        master.title('Verify information...')

        self.top_frame = Frame(self.master)
        self.top_frame.pack(fill=X)
        instructions = Message(self.top_frame, text='Verify the information below and correct as necessary.', width=500)
        instructions.pack(anchor=CENTER, pady=5)

        self.bot_frame = Frame(self.master)
        self.bot_frame.pack(side=BOTTOM, fill=X)

        self.mid_frame = Frame(self.master)
        self.mid_frame.pack(expand=True, fill=Y)


        self.canvas = Canvas(self.mid_frame, width=660, height=500)
        self.canvas.pack(side=LEFT, expand=True, fill=Y)

        self.vsb = Scrollbar(self.mid_frame, command=self.canvas.yview)
        self.vsb.pack(side=RIGHT, fill=Y)

        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.bind('<Configure>', self.on_configure)

        self.frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor=NW)

        for i in range(30):
            Label(self.frame, text='Track {})'.format(str(i + 1).zfill(2)), width=7).grid(row=i, column=0, padx=(5,0), pady=3, sticky=E)
            Entry(self.frame, width=15, text='Cue time').grid(row=i, column=1, padx=3, pady=3)
            Entry(self.frame, width=30, text='Artist').grid(row=i, column=2, padx=3, pady=3)
            Entry(self.frame, width=50, text='Title').grid(row=i, column=3, padx=(3, 7), pady=3)

        self.bot_container = Frame(self.bot_frame)
        self.bot_container.pack(anchor=CENTER)

        self.adj_instructions = Label(self.bot_container, text='Adjust all cue times by')
        self.adj_instructions.grid(row=0, column=0, sticky=E)

        self.min_var = StringVar()
        self.min_var.trace('w', lambda *args: min_limit_check(self.min_var))
        self.sec_var = StringVar()
        self.sec_var.trace('w', lambda *args: sec_limit_check(self.sec_var))

        self.min_adj = Entry(self.bot_container, width=5, textvariable=self.min_var)
        self.min_var.set('00')
        self.min_adj_lbl = Label(self.bot_container, text='m')
        self.sec_adj = Entry(self.bot_container, width=5, textvariable=self.sec_var)
        self.sec_var.set('00')
        self.sec_adj_lbl = Label(self.bot_container, text='s')
        self.min_adj.grid(row=0, column=1)
        self.min_adj_lbl.grid(row=0, column=2)
        self.sec_adj.grid(row=0, column=3)
        self.sec_adj_lbl.grid(row=0, column=4)

        self.early_or_late = StringVar()
        self.earlier = Radiobutton(self.bot_container, variable=self.early_or_late, value='-', text='earlier')
        self.later = Radiobutton(self.bot_container, variable=self.early_or_late, value='+', text='later')
        self.earlier.grid(row=0, column=5)
        self.later.grid(row=0, column=6)

        self.early_or_late.set('-')

        self.confirm_button = Button(self.bot_container, text='Confirm', command=self.master.destroy)
        self.confirm_button.grid(row=1, column=0, pady=5, columnspan=7)

tracklist = []
root = Tk()
gui = verification_window(root, tracklist)
root.resizable(0, 1)
root.mainloop()
