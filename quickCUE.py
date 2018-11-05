from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from urllib.request import urlopen
from bs4 import BeautifulSoup
from mutagen import File, MutagenError
from mutagen.easyid3 import EasyID3
import logging

logging.basicConfig(handlers=[logging.FileHandler('log.txt', 'w', 'utf-8')], level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create custom exception for when text in the website box is not a valid 1001tracklists link


class SiteValidationError(Exception):
    pass


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
            cuetime = adjust_cuetimes(cuetime, adj_time, early_or_late)
        cuetimes.append(cuetime)
    return cuetimes, tracks


def verify_information(TLroot, in_cuetimes, in_tracks):
    master = Toplevel(TLroot)
    master.title('Verify Information...')
    cuetimes = in_cuetimes
    tracks = in_tracks

    if len(cuetimes) < len(tracks):
        messagebox.showinfo('', 'It seems that not all tracks have cuetimes on 1001tracklists. Remaining tracks without cuetimes will need to be manually added to the generated CUE.')
        last = cuetimes[-1]
        for i in range(len(tracks) - len(cuetimes)):
            cuetimes.append(last)

    tracklist = []
    for i in range(len(cuetimes)):
        track = {'track': StringVar(), 'cuetime': StringVar(), 'artist': StringVar(), 'title': StringVar()}
        track['track'].set(str(i + 1).zfill(2))
        track['cuetime'].set(cuetimes[i])
        track['artist'].set(tracks[i][0])
        track['title'].set(tracks[i][1])
        tracklist.append(track)

    gui2 = verification_window(master, tracklist)
    master.lift()
    wait_window.destroy()
    master.focus_force()

    master.wait_window()
    return (gui2.verified, tracklist, gui2.min_var, gui2.sec_var, gui2.early_or_late)


def adjust_cuetimes(cuetime, adjustment, early_or_late):
    cuetime = cuetime.split(':')
    cuetime_secs = int(cuetime[0]) * 60 + int(cuetime[1])
    if early_or_late.get() == '-':
        cuetime_secs -= adjustment
        if cuetime_secs < 0:
            cuetime_secs = 0
    else:
        cuetime_secs += adjustment
    return ':'.join([str(cuetime_secs // 60).zfill(2), str(cuetime_secs % 60).zfill(2), '00'])


class verification_window():
    def on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _bind_to_mousewheel(self, event):
        self.canvas.bind_all('<MouseWheel>', self._on_mousehweel)

    def _unbind_to_mousewheel(self, event):
        self.canvas.unbind_all('<MouseWheel>')

    def _on_mousehweel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def complete_verification(self):
        self.verified = True
        self.master.destroy()

    def __init__(self, master, tracklist):
        self.master = master

        # To handle x-ing or canceling verification
        self.verified = False

        self.top_frame = Frame(self.master, borderwidth=0)
        self.top_frame.pack(fill=X)
        self.instructions = Message(self.top_frame, text='Verify the information below and correct as necessary.', width=500)
        self.instructions.pack(anchor=CENTER, pady=5)

        self.bot_frame = Frame(self.master, borderwidth=0)
        self.bot_frame.pack(side=BOTTOM, fill=X)

        self.mid_frame = Frame(self.master, borderwidth=0)
        self.mid_frame.pack(expand=True, fill=Y)

        self.canvas = Canvas(self.mid_frame, width=615, height=500, highlightthickness=0)
        self.canvas.pack(side=LEFT, expand=True, fill=Y)

        self.vsb = Scrollbar(self.mid_frame, command=self.canvas.yview)
        self.vsb.pack(side=RIGHT, fill=Y)

        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.bind('<Configure>', self.on_configure)

        self.frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor=NW)

        self.frame.bind('<Enter>', self._bind_to_mousewheel)
        self.frame.bind('<Leave>', self._unbind_to_mousewheel)

        track_widgets = []
        for i in range(len(tracklist)):
            widget = {}

            widget['label'] = Label(self.frame, text='Track {})'.format(tracklist[i]['track'].get()), width=7)
            widget['label'].grid(row=i, column=0, padx=(5, 0), sticky=E)

            widget['cuetime'] = Entry(self.frame, width=10, textvariable=tracklist[i]['cuetime'])
            widget['cuetime'].grid(row=i, column=1, padx=1)

            widget['artist'] = Entry(self.frame, width=30, textvariable=tracklist[i]['artist'])
            widget['artist'].grid(row=i, column=2, padx=1)

            widget['title'] = Entry(self.frame, width=50, textvariable=tracklist[i]['title'])
            widget['title'].grid(row=i, column=3, padx=(1, 7))

        track_widgets.append(widget)

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

        self.adjust_button = Button(self.bot_container, text='Adjust', font=('Segoe UI', 8, 'normal'), borderwidth=1)
        self.adjust_button.grid(row=0, column=7)

        self.cancel_button = Button(self.bot_container, text='Cancel', command=self.master.destroy)
        self.cancel_button.grid(row=1, column=0, pady=5, columnspan=4)

        self.confirm_button = Button(self.bot_container, text='Confirm', command=self.complete_verification, font=('Segoe UI', 9, 'bold'), default=ACTIVE)
        self.confirm_button.grid(row=1, column=4, pady=5, columnspan=4)


class mainWindow():
    def __init__(self, master):
        self.master = master
        self.master.title('quickCUE')

        # Use self. to avoid garbage collection and screwing default radio button selections
        self.var = StringVar()
        self.artistvar = StringVar()
        self.titlevar = StringVar()
        self.yearvar = StringVar()
        self.genrevar = StringVar()
        self.filepath = StringVar()

        self.instructions = Message(master, text='Please select the target audio file and correct the information below as necessary.', width=250)
        self.instructions.grid(row=0, column=0, columnspan=3, sticky=W)

        self.getFileButton = Button(text='Select target MP3, FLAC, or WAV...', wraplength=100, width=15, borderwidth=3, command=self.acquireAudioFile)
        self.getFileButton.grid(row=0, column=3, sticky=E, padx=10)

        self.artist = Entry(master, width=60, text=self.artistvar)
        self.artistLabel = Label(master, text='Artist:')
        self.artistLabel.grid(row=1, column=0, sticky=W)
        self.artist.grid(row=1, column=1, columnspan=3, pady=3, padx=10, sticky=W)

        self.title = Entry(master, width=60, text=self.titlevar)
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
        self.website = Entry(master, width=60)
        self.website.grid(row=5, column=1, columnspan=3, padx=10, sticky=W)

        self.customRadioButton = Radiobutton(master, text='Custom tracklist:', variable=self.var, value='offline', command=lambda: self.RadioClicked('offline'))
        self.customRadioButton.grid(row=6, column=1, columnspan=3, sticky=W)

        self.formatting_container = Frame(master)
        self.formatting_container.grid(row=7, column=1, columnspan=3, pady=3, sticky=W)
        self.formatting_instructions = Message(self.formatting_container, text='Please input your tracklist formatting using "cue", "artist", and "title".\n For example: [cue] artist - title)', width=370)
        self.formatting_label = Label(self.formatting_container, text='Formatting:', width=10)
        self.tl_formatting = StringVar()
        self.tl_formatting.set('[cue] artist - title')
        self.formatting_entry = Entry(self.formatting_container, width=49, state=DISABLED, textvariable=self.tl_formatting)
        self.formatting_instructions.grid(row=0, column=0, columnspan=2)
        self.formatting_label.grid(row=1, column=0, sticky=W)
        self.formatting_entry.grid(row=1, column=1, sticky=W)

        self.offline_tl_container = Frame(master)
        self.offline_tl_container.grid(row=8, column=1, columnspan=3, padx=10, sticky=W)
        self.offline_tl = Text(self.offline_tl_container, width=60, state=DISABLED, bg=self.website.cget('disabledbackground'), font=('Segoe UI', 8, 'normal'), wrap=WORD)
        self.offline_tl_vsb = Scrollbar(self.offline_tl_container, command=self.offline_tl.yview, width=0)
        self.offline_tl_vsb.pack(side=RIGHT, fill=Y)
        self.offline_tl.config(yscrollcommand=self.offline_tl_vsb.set)
        self.offline_tl.pack(side=LEFT)

        self.log_label = StringVar()
        self.log_label.set('Logging off')
        self.log_var = BooleanVar()
        self.log_var.set(False)
        self.log_switch = Checkbutton(master, textvariable=self.log_label, variable=self.log_var, command=self.loggingChecked)
        self.log_switch.grid(row=9, column=0, columnspan=2, sticky=W)

        self.verifyButton = Button(master, text='Verify CUE...', command=lambda *args: self.convert2cue('verify'), default=ACTIVE)
        self.verifyButton.grid(row=9, column=2, pady=10)

        self.quickButton = Button(master, text='Quick CUE', command=lambda *args: self.convert2cue('quick'))
        self.quickButton.grid(row=9, column=3, pady=10)

        self.var.set('online')

        # Set verify as default action for <Return>
        self.master.bind('<Return>', (lambda e, b=self.verifyButton: b.invoke()))

    def acquireAudioFile(self):
        self.filepath.set(filedialog.askopenfilename(filetypes=[('Audio files', ('*.mp3', '*.flac', '*.wav'))]))
        if self.filepath.get():
            try:
                file = EasyID3(self.filepath.get())
            except MutagenError:
                try:
                    file = File(self.filepath.get())
                except MutagenError:
                    messagebox.showwarning('Bad file', 'Please select an MP3, FLAC, or WAV file.')
            if file:
                self.artistvar.set(file.get('artist')[0])
                self.titlevar.set(file.get('title')[0])
                self.yearvar.set(file.get('date'))
                self.genrevar.set(file.get('genre'))
            # except:
            # pass

    def RadioClicked(self, var):
        if var == 'online':
            self.website.config(state=NORMAL)
            self.offline_tl.config(state=DISABLED, bg=self.website.cget('disabledbackground'))
            self.formatting_entry.config(state=DISABLED)
            print(self.var.get())
        elif var == 'offline':
            self.offline_tl.config(state=NORMAL, bg='white')
            self.formatting_entry.config(state=NORMAL)
            self.website.config(state=DISABLED)
            print(self.var.get())

    def loggingChecked(self):
        if self.log_var.get():
            self.log_label.set('Logging on')
        else:
            self.log_label.set('Logging off')

    def save_cue(self, site, website, tracks, cuetimes):
        artist = self.artist.get() if self.artist.get() else '[ARTIST]'
        title = self.title.get() if self.title.get() else '[TITLE]'

        file = filedialog.asksaveasfile(defaultextension='.cue', filetypes=[('CUE', '*.cue')], initialfile='{0} - {1}'.format(artist, title))
        if file:
            year = self.year.get() if self.year.get() else '9999'
            genre = self.genre.get() if self.genre.get() else '[GENRE]'
            if self.filepath.get():
                filename = self.filepath.get().split('/')[-1]
            else:
                filename = '[PLEASE MANUALLY INSERT FILENAME]'
            filetypes = {'wav': 'WAVE', 'lac': 'WAVE', 'mp3': 'MP3', 'ME]': '[INSERT FILE TYPE]'}

            try:
                file.write('REM GENRE {}\n'.format(genre))
                file.write('REM DATE {}\n'.format(year))
                if website:
                    short_url = site.find('td', text='short url').next_sibling.next_sibling.contents[0]['href']
                    file.write('REM WWW {}\n'.format(short_url))
                file.write('PERFORMER "{}"\n'.format(artist))
                file.write('TITLE "{}"\n'.format(title))
                file.write('FILE "{0}" {1}\n'.format(filename, filetypes[filename[-3:]]))
                for i in range(len(cuetimes)):
                    file.write('    TRACK {} AUDIO\n'.format(str(i + 1).zfill(2)))
                    file.write('        TITLE "{}"\n'.format(tracks[i][1]))
                    file.write('        PERFORMER "{}"\n'.format(tracks[i][0]))
                    file.write('        INDEX 01 {}\n'.format(cuetimes[i]))
                success = True
                exception = None
            except Exception as e:
                success = False
                exception = e.args[1]
                logging.debug(e)
            finally:
                file.close()
                return success, exception
        else:
            return False, False

    def convert2cue(self, type):
        self.quickButton.config(state=DISABLED)
        self.verifyButton.config(state=DISABLED)

        open_success = False

        if self.var.get() == 'online':
            try:
                website = self.website.get()
                if '1001tracklists' not in website and '1001.tl' not in website:
                    raise SiteValidationError
                site = BeautifulSoup(urlopen(website), 'lxml')
                open_success = True
            except SiteValidationError as e:
                open_success = False
                messagebox.showwarning('', 'Please provide a 1001tracklists.com or 1001.tl link.')

            if open_success:
                cuetimes = [div.text.strip() for div in site.find_all('div', class_='cueValueField')]
                cuetimes = cleaned_cuetimes(cuetimes)
                logging.debug(cuetimes)
                tracks = [span.text.strip().split(' - ') for span in site.find_all('span', class_='trackFormat') if 'tlp_' in span.parent.parent.parent.parent.parent.parent.parent['id'] and 'tlpSubTog' not in span.parent.parent.parent.parent.parent.parent.parent['class']]
                logging.debug(tracks)
        elif self.var.get() == 'offline':
            offline_tl = self.offline_tl.get('1.0', 'end-1c')
            messagebox.showinfo('Whoops!', 'Still working on custom tracklists!\nPlease provide a 1001TL link instead - thanks!')
            self.var.set('online')
            self.RadioClicked('online')
        else:
            pass

        if open_success:
            if type == 'verify':
                verified, tracklist, min_var, sec_var, early_or_late = verify_information(root, cuetimes, tracks)
                cuetimes, tracklist = clean_verification(tracklist, min_var, sec_var, early_or_late)
            if verified:
                success, error = self.save_cue(site, website, tracks, cuetimes)
                if success:
                    messagebox.showinfo('', 'Conversion to cue complete!')
                elif not success and error:
                    messagebox.showwarning('', 'Error - please verify and try again.\n{}'.format(error))
                else:
                    pass

        self.verifyButton.config(state=NORMAL)
        self.quickButton.config(state=NORMAL)


root = Tk()
root.resizable(0, 0)
gui = mainWindow(root)
root.mainloop()
