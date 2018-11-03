from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from urllib.request import urlopen
from bs4 import BeautifulSoup
from mutagen import File
from mutagen.easyid3 import EasyID3


def cleaned_cuetimes(cuetimes):
    new_cuetimes = []
    for i in range(len(cuetimes)):
        if i == 0 and not cuetimes[i]:
            newtime = '00:00:00'
        elif not cuetimes[i]:
            continue
        elif cuetimes[i].count(':') == 1:
            min_sec = cuetimes[i].split(':')
            newtime = '{0}:{1}:00'.format(min_sec[0].zfill(2), min_sec[1])
        else:
            hr_min_sec = cuetimes[i].split(':')
            newtime = '{0}:{1}:00'.format(int(hr_min_sec[0]) * 60 + int(hr_min_sec[1]), hr_min_sec[2])
        new_cuetimes.append(newtime)
    return new_cuetimes


def min_limit_check(svar):
    min = svar.get()

    if len(min) > 3:
        svar.set(min[:3])


def sec_limit_check(svar):
    sec = svar.get()

    if len(sec) > 2:
        svar.set(sec[:2])


def clean_verification(tracklist, min_adj, sec_adj, early_or_late):
    tracks = []
    cuetimes = []
    for i in range(len(tracklist)):
        tracks.append([tracklist[i]['artist'].get(), tracklist[i]['title'].get()])
        adj_time = int(min_adj.get()) * 60 + int(sec_adj.get())
        cuetime = tracklist[i]['cuetime'].get()
        if adj_time > 0:
            cuetime = adjust_cuetimes(cuetime, adj_time, adj_time, early_or_late)
        cuetimes.append(cuetime)
    return cuetimes, tracks


class verification_window():
    def on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def __init__(self, master, tracklist):
        self.master = master
        master.title('Verify information...')

        self.top_frame = Frame(self.master)
        self.top_frame.pack(fill=X)
        self.instructions = Message(self.top_frame, text='Verify the information below and correct as necessary.', width=500)
        self.instructions.pack(anchor=CENTER, pady=5)

        self.bot_frame = Frame(self.master)
        self.bot_frame.pack(side=BOTTOM, fill=X)

        self.mid_frame = Frame(self.master)
        self.mid_frame.pack(expand=True, fill=Y)

        self.canvas = Canvas(self.mid_frame, width=627, height=500)
        self.canvas.pack(side=LEFT, expand=True, fill=Y)

        self.vsb = Scrollbar(self.mid_frame, command=self.canvas.yview)
        self.vsb.pack(side=RIGHT, fill=Y)

        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.bind('<Configure>', self.on_configure)

        self.frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor=NW)

        track_widgets = []
        for i in range(len(tracklist)):
            widgets = {}

            widgets['label'] = Label(self.frame, text='Track {})'.format(tracklist[i]['track'].get()), width=7)
            widgets['label'].grid(row=i, column=0, padx=(5, 0), sticky=E)

            widgets['cuetime'] = Entry(self.frame, width=10, textvariable=tracklist[i]['cuetime'])
            widgets['cuetime'].grid(row=i, column=1, padx=3)

            widgets['artist'] = Entry(self.frame, width=30, textvariable=tracklist[i]['artist'])
            widgets['artist'].grid(row=i, column=2, padx=3)

            widgets['title'] = Entry(self.frame, width=50, textvariable=tracklist[i]['title'])
            widgets['title'].grid(row=i, column=3, padx=(3, 7))

        track_widgets.append(widgets)

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


def verify_information(TLmaster, in_cuetimes, in_tracks):
    master = TLmaster
    master.title('Verify Information...')
    cuetimes = in_cuetimes
    tracks = in_tracks

    tracklist = []
    for i in range(len(cuetimes)):
        track = {'track': StringVar(), 'cuetime': StringVar(), 'artist': StringVar(), 'title': StringVar()}
        track['track'].set(str(i + 1).zfill(2))
        track['cuetime'].set(cuetimes[i])
        track['artist'].set(tracks[i][0])
        track['title'].set(tracks[i][1])
        tracklist.append(track)

    gui2 = verification_window(master, tracklist)

    master.wait_window()
    return (tracklist, gui2.min_var, gui2.sec_var, gui2.early_or_late)


def adjust_cuetimes(cuetime, adjustment, adj_time, early_or_late):
    cuetime = cuetime.split(':')
    cuetime_secs = int(cuetime[0]) * 60 + int(cuetime[1])
    if early_or_late.get() == '-':
        cuetime_secs -= adj_time
        if cuetime_secs < 0:
            cuetime_secs = 0
    else:
        cuetime_secs += adj_time
    return ':'.join([str(cuetime_secs // 60).zfill(2), str(cuetime_secs % 60).zfill(2), '00'])


class mainWindow():
    def __init__(self, master):
        self.master = master
        self.master.title('text2cue')

        # Use self. to avoid garbage collection and screwing default radio button selections
        self.var = StringVar()
        self.artistvar = StringVar()
        self.titlevar = StringVar()
        self.yearvar = StringVar()
        self.genrevar = StringVar()
        self.filepath = StringVar()

        self.instructions = Message(master, text='Please select the target audio file and correct the information below as necessary.', width=225)
        self.instructions.grid(row=0, column=0, columnspan=3, sticky=W)

        self.getFileButton = Button(text='Select target MP3, FLAC, or WAV...', wraplength=100, width=15, borderwidth=3, command=self.acquireAudioFile)
        self.getFileButton.grid(row=0, column=3, sticky=E, padx=10)

        self.artist = Entry(master, width=50, text=self.artistvar)
        self.artistLabel = Label(master, text='Artist:')
        self.artistLabel.grid(row=1, column=0, sticky=W)
        self.artist.grid(row=1, column=1, columnspan=3, pady=3, padx=10, sticky=W)

        self.title = Entry(master, width=50, text=self.titlevar)
        self.titleLabel = Label(master, text='Title:')
        self.titleLabel.grid(row=2, column=0, sticky=W)
        self.title.grid(row=2, column=1, columnspan=3, pady=3, padx=10, sticky=W)

        self.year = Entry(master, width=5, text=self.yearvar)
        self.yearLabel = Label(master, text='Year:')
        self.yearLabel.grid(row=3, column=0, sticky=W)
        self.year.grid(row=3, column=1, pady=3, padx=10, sticky=W)

        self.genre = Entry(master, width=15, text=self.genrevar)
        self.genreLabel = Label(master, text='Genre:')
        self.genreLabel.grid(row=3, column=2, sticky=E)
        self.genre.grid(row=3, column=3, pady=3, padx=10, sticky=W)

        self.webRadioButton = Radiobutton(master, text='1001 Tracklists link:', variable=self.var, value='online', command=lambda: self.RadioClicked('online'))
        self.webRadioButton.grid(row=4, column=1, columnspan=3, sticky=W)
        self.website = Entry(master, width=50)
        self.website.grid(row=5, column=1, columnspan=3, padx=10, sticky=W)

        self.customRadioButton = Radiobutton(master, text='Custom tracklist:', variable=self.var, value='offline', command=lambda: self.RadioClicked('offline'))
        self.customRadioButton.grid(row=6, column=1, columnspan=3, sticky=W)
        self.offline_tl = Entry(master, width=50, state=DISABLED)
        self.offline_tl.grid(row=7, column=1, columnspan=3, ipady=100, padx=10, sticky=W)

        self.verifyButton = Button(master, text='Verify CUE...', command=lambda *args: self.convert2cue('verify'))
        self.verifyButton.grid(row=8, column=2, pady=10)

        self.quickButton = Button(master, text='Quick CUE', command=lambda *args: self.convert2cue('quick'))
        self.quickButton.grid(row=8, column=3, pady=10)

        self.var.set('online')

    def acquireAudioFile(self):
        self.filepath.set(filedialog.askopenfilename(filetypes=[('Audio files', ('*.mp3', '*.flac', '*.wav'))]))
        if self.filepath.get():
            try:
                file = EasyID3(self.filepath.get())
            except:
                try:
                    file = File(self.filepath.get())
                except:
                    messagebox.showwarning('Bad file', 'Please select an MP3, FLAC, or WAV file.')
        try:
            self.artistvar.set(file.get('artist')[0])
            self.titlevar.set(file.get('title')[0])
            self.yearvar.set(file.get('date'))
            self.genrevar.set(file.get('genre'))
        except:
            pass

    def RadioClicked(self, var):
        if var == 'online':
            self.website.configure(state=NORMAL)
            self.offline_tl.configure(state=DISABLED)
        elif var == 'offline':
            self.offline_tl.configure(state=NORMAL)
            self.website.configure(state=DISABLED)

    def convert2cue(self, type):
        artist = self.artist.get() if self.artist.get() else '[ARTIST]'
        title = self.title.get() if self.title.get() else '[TITLE]'
        year = self.year.get() if self.year.get() else '9999'
        genre = self.genre.get() if self.genre.get() else '[GENRE]'
        website = self.website.get()
        offline_tl = self.offline_tl.get()
        if self.filepath.get():
            filename = self.filepath.get().split('/')[-1]
        else:
            filename = '[PLEASE MANUALLY INSERT FILENAME]'
        filetypes = {'wav': 'WAVE', 'lac': 'WAVE', 'mp3': 'MP3', 'ME]': '[INSERT FILE TYPE]'}

        if website and not offline_tl:
            site = BeautifulSoup(urlopen(website), 'lxml')
            cuetimes = [div.text.strip() for div in site.find_all('div', class_='cueValueField')]
            cuetimes = cleaned_cuetimes(cuetimes)
            tracks = [span.text.strip().split(' - ') for span in site.find_all('span', class_='trackFormat') if 'tlp_' in span.parent.parent.parent.parent.parent.parent.parent['id'] and 'tlpSubTog' not in span.parent.parent.parent.parent.parent.parent.parent['class']]
        elif offline_tl and not website:
            pass
        else:
            pass

        if type == 'verify':
            newwindow = Toplevel(root)
            tracklist, min_var, sec_var, early_or_late = verify_information(newwindow, cuetimes, tracks)
            cuetimes, tracklist = clean_verification(tracklist, min_var, sec_var, early_or_late)

        file = filedialog.asksaveasfile(defaultextension='.cue', filetypes=[('CUE', '*.cue')], initialfile='{0} - {1}'.format(artist, title))
        if file:
            try:
                error = False
                file.write('REM GENRE {}\n'.format(genre))
                file.write('REM DATE {}\n'.format(year))
                if website:
                    file.write('REM WWW {}\n'.format(website))
                file.write('PERFORMER "{}"\n'.format(artist))
                file.write('TITLE "{}"\n'.format(title))
                file.write('FILE "{0}" {1}\n'.format(filename, filetypes[filename[-3:]]))
                for i in range(len(cuetimes)):
                    file.write('    TRACK {} AUDIO\n'.format(str(i + 1).zfill(2)))
                    file.write('        TITLE "{}"\n'.format(tracks[i][1]))
                    file.write('        PERFORMER "{}"\n'.format(tracks[i][0]))
                    file.write('        INDEX 01 {}\n'.format(cuetimes[i]))
            except Exception as e:
                error = True
                exception = e.args[1]
                print(e)
            finally:
                file.close()
                if error:
                    message = 'Error - please verify and try again.\n{}'.format(exception)
                else:
                    message = 'Conversion to cue complete!'
                messagebox.showinfo('', message)
        else:
            pass


root = Tk()
root.resizable(0, 0)
gui = mainWindow(root)
root.mainloop()
