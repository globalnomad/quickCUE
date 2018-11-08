from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from urllib.request import urlopen
from bs4 import BeautifulSoup
from mutagen import File, MutagenError
from mutagen.easyid3 import EasyID3
import re
import logging


# Create custom exception for when text in the website box is not a valid 1001tracklists link
class SiteValidationError(Exception):
    pass


def get_audacity_labels(label_file_path):
    with open(label_file_path, 'r') as audacity_labels:
        cuetimes = []
        for line in audacity_labels:
            time = float(line.split()[0])
            m = str(int(time // 60)).zfill(2)
            s = str(int(time) % 60).zfill(2)
            f = str(int((time - int(time))*75)).zfill(2)
            cuetimes.append(f'{m}:{s}:{f}')
    logging.info('Acquired cuetimes from Audacity label file!')
    logging.debug(cuetimes)
    return cuetimes


def clean_cuetime(track, cuetime=None):
    if cuetime:
        track['cuetime'] = cuetime
    else:
        if track['track'] == '01' and not track['cuetime']:
            track['cuetime'] = '00:00:00'
        elif track['cuetime'].count(':') == 1:
            min_sec = track['cuetime'].split(':')
            track['cuetime'] = '{0}:{1}:00'.format(min_sec[0].zfill(2), min_sec[1])
        elif track['cuetime']:
            hms = track['cuetime'].split(':')
            m, s = int(hms[0]) * 60 + int(hms[1]), hms[2]
            track['cuetime'] = f'{m}:{s}:00'
    return track['cuetime']


def min_limit_check(svar):
    min = svar.get()
    if len(min) > 3:
        svar.set(min[:3])


def sec_limit_check(svar):
    sec = svar.get()
    if len(sec) > 2:
        svar.set(sec[:2])


def return_tracks(tracklist):
    tracks = []
    for track in tracklist:
        tracks.append({'track': track['track'].get(), 'cuetime': track['cuetime'].get(), 'artist': track['artist'].get(), 'title': track['title'].get()})
    if logging.getLogger().getEffectiveLevel() < 50:
        log_message = [f'Verified cuetimes and tracks ({len(tracks)}):\n'] + [f'{" "*34}{track["cuetime"].rjust(9)}  {track["artist"]} - {track["title"]}\n' for track in tracks]
        logging.debug("".join(log_message))
    return tracks


def verify_information(TLroot, in_tracks):
    logging.info('Opening verification window...')
    master = Toplevel(TLroot)
    master.title('Verify Information...')

    tracks = []
    for in_track in in_tracks:
        track = {'track': StringVar(), 'cuetime': StringVar(), 'artist': StringVar(), 'title': StringVar()}
        track['track'].set(in_track['track'])
        track['cuetime'].set(in_track['cuetime'])
        track['artist'].set(in_track['artist'])
        track['title'].set(in_track['title'])
        tracks.append(track)

    gui2 = verification_window(master, tracks)
    master.lift()
    master.focus_force()

    master.wait_window()
    return (gui2.verified, tracks)


class verification_window():
    def on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _bind_to_mousewheel(self, event):
        self.canvas.bind_all('<MouseWheel>', self._on_mousehweel)

    def _unbind_to_mousewheel(self, event):
        self.canvas.unbind_all('<MouseWheel>')

    def _on_mousehweel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def adjust_cuetimes(self):
        logging.info('Adjusting cuetimes...')
        adjustment = int(self.min_adj.get()) * 60 + int(self.sec_adj.get())
        for track in self.tracklist:
            cuetime = track['cuetime'].get()
            cuetime = cuetime.split(':')
            cuetime_secs = int(cuetime[0]) * 60 + int(cuetime[1])
            if self.early_or_late.get() == '-':
                cuetime_secs -= adjustment
                if cuetime_secs < 0:
                    cuetime_secs = 0
            else:
                cuetime_secs += adjustment
            track['cuetime'].set(':'.join([str(cuetime_secs // 60).zfill(2), str(cuetime_secs % 60).zfill(2), '00']))
        logging.info(f'Cuetimes adjusted by {self.early_or_late.get()}{adjustment}s.')

    def adj_limit_check(self, svar):
        adj = svar.get()
        if len(adj) > 2:
            svar.set(adj[:2])
        if svar == self.sec_var and adj and int(adj) > 59:
            svar.set('59')

    def zero_fill(self, svar):
        if not svar.get():
            svar.set('0')

    def complete_verification(self):
        self.verified = True
        logging.info('Verification complete!')
        self.master.destroy()


    def __init__(self, master, tracklist):
        self.master = master
        self.tracklist = tracklist

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

        self.canvas = Canvas(self.mid_frame, width=627, height=500, highlightthickness=0)
        self.canvas.pack(side=LEFT, expand=True, fill=Y)

        self.vsb = Scrollbar(self.mid_frame, command=self.canvas.yview)
        self.vsb.pack(side=RIGHT, fill=Y)

        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.bind('<Configure>', self.on_configure)

        self.frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor=NW)

        self.frame.bind('<Enter>', self._bind_to_mousewheel)
        self.frame.bind('<Leave>', self._unbind_to_mousewheel)

        self.track_widgets = []
        for i, track in enumerate(self.tracklist):
            widget = {}

            widget['label'] = Label(self.frame, text=f'Track {track["track"].get()})', width=7)
            widget['label'].grid(row=i, column=1, sticky=E)

            widget['cuetime'] = Entry(self.frame, width=10, textvariable=track['cuetime'])
            widget['cuetime'].grid(row=i, column=2, padx=1)

            widget['artist'] = Entry(self.frame, width=30, textvariable=track['artist'])
            widget['artist'].grid(row=i, column=3, padx=1)

            widget['title'] = Entry(self.frame, width=50, textvariable=track['title'])
            widget['title'].grid(row=i, column=4, padx=(1, 7))

        self.track_widgets.append(widget)

        self.bot_container = Frame(self.bot_frame)
        self.bot_container.pack(anchor=CENTER)

        self.adj_instructions = Label(self.bot_container, text='Adjust all cue times by')
        self.adj_instructions.grid(row=0, column=0, sticky=E)

        self.min_var = StringVar()
        self.min_var.trace('w', lambda *args: self.adj_limit_check(self.min_var))
        self.sec_var = StringVar()
        self.sec_var.trace('w', lambda *args: self.adj_limit_check(self.sec_var))

        self.min_adj = Entry(self.bot_container, width=5, textvariable=self.min_var)
        self.min_var.set('0')
        self.min_adj_lbl = Label(self.bot_container, text='m')
        self.sec_adj = Entry(self.bot_container, width=5, textvariable=self.sec_var)
        self.sec_var.set('0')
        self.sec_adj_lbl = Label(self.bot_container, text='s')
        self.min_adj.grid(row=0, column=1)
        self.min_adj.bind('<FocusOut>', lambda *args: self.zero_fill(self.min_var))
        self.min_adj_lbl.grid(row=0, column=2)
        self.sec_adj.grid(row=0, column=3)
        self.sec_adj.bind('<FocusOut>', lambda *args: self.zero_fill(self.sec_var))
        self.sec_adj_lbl.grid(row=0, column=4)

        self.early_or_late = StringVar()
        self.earlier = Radiobutton(self.bot_container, variable=self.early_or_late, value='-', text='earlier')
        self.later = Radiobutton(self.bot_container, variable=self.early_or_late, value='+', text='later')
        self.earlier.grid(row=0, column=5)
        self.later.grid(row=0, column=6)

        self.early_or_late.set('-')

        self.adjust_button = Button(self.bot_container, text='Adjust', font=('Segoe UI', 8, 'normal'), borderwidth=1, command=self.adjust_cuetimes)
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
        self.method = StringVar()
        self.artistvar = StringVar()
        self.titlevar = StringVar()
        self.yearvar = StringVar()
        self.genrevar = StringVar()
        self.filepath = StringVar()

        self.instructions = Message(master, text='Please select the target audio file and correct the information below as necessary.', width=250)
        self.instructions.grid(row=0, column=1, columnspan=2, sticky=W, padx=(5, 0))

        self.getFileButton = Button(text='Select target MP3, FLAC, or WAV...', wraplength=130, width=15, borderwidth=2, command=self.acquireAudioFile)
        self.getFileButton.grid(row=0, column=3, sticky=E, padx=(5, 10), pady=(5, 10))

        self.file_name_var = StringVar()
        self.file_name_var.set('[No file selected]')
        self.file_name = Label(master, textvariable=self.file_name_var, font=('Segoe UI', 8, 'italic'), width=60)
        self.file_name.grid(row=1, column=1, columnspan=3)

        self.artist = Entry(master, width=60, text=self.artistvar)
        self.artistLabel = Label(master, text='Artist:')
        self.artistLabel.grid(row=2, column=0, sticky=W)
        self.artist.grid(row=2, column=1, columnspan=3, pady=3, padx=10, sticky=W)

        self.title = Entry(master, width=60, text=self.titlevar)
        self.titleLabel = Label(master, text='Title:')
        self.titleLabel.grid(row=3, column=0, sticky=W)
        self.title.grid(row=3, column=1, columnspan=3, pady=3, padx=10, sticky=W)

        self.yg_frame = Frame(master)
        self.yg_frame.grid(row=4, column=0, columnspan=4, sticky=W)

        self.year = Entry(self.yg_frame, width=5, text=self.yearvar)
        self.yearLabel = Label(self.yg_frame, text='Year:')
        self.yearLabel.grid(row=0, column=0, sticky=W, padx=(0, 5))
        self.year.grid(row=0, column=1, pady=3, padx=10, sticky=W)

        self.genre = Entry(self.yg_frame, width=15, text=self.genrevar)
        self.genreLabel = Label(self.yg_frame, text='Genre:')
        self.genreLabel.grid(row=0, column=2, sticky=E)
        self.genre.grid(row=0, column=3, pady=3, padx=10, sticky=W)

        self.aud_label_var = BooleanVar()
        self.audacity_label = Checkbutton(self.yg_frame, text='Optionally import an Audacity label file.', variable=self.aud_label_var, command=self.use_aud_labels)
        self.import_labels = Button(self.yg_frame, text='Import Labels', state=DISABLED, command=self.acquireLabelFile)
        self.label_file_path = StringVar()
        self.label_file = Entry(self.yg_frame, textvariable=self.label_file_path, width=46, state=DISABLED)
        self.audacity_label.grid(row=1, column=1, columnspan=2, pady=(15,0), sticky=W)
        self.import_labels.grid(row=2, column=1, pady=(0, 25))
        self.label_file.grid(row=2, column=2, columnspan=2, padx=10, pady=(0, 25))

        self.webRadioButton = Radiobutton(master, text='1001 Tracklists link:', variable=self.method, value='online', command=lambda: self.RadioClicked('online'))
        self.webRadioButton.grid(row=5, column=1, columnspan=3, sticky=W)
        self.website = Entry(master, width=60)
        self.website.grid(row=6, column=1, columnspan=3, padx=10, sticky=W)

        self.customRadioButton = Radiobutton(master, text='Custom tracklist:', variable=self.method, value='offline', command=lambda: self.RadioClicked('offline'))
        self.customRadioButton.grid(row=7, column=1, columnspan=3, sticky=W, pady=(10, 0))

        self.formatting_container = Frame(master)
        self.formatting_container.grid(row=8, column=1, columnspan=3, sticky=W)
        self.formatting_instructions = Message(self.formatting_container, text='Please input one track per line as "cue artist - title" or "track artist - title" (no quotes). Cues can be formatted as:   [h:mm:ss] or [mmm:sss]   with or without the [ ].', width=350)
        # self.formatting_label = Label(self.formatting_container, text='Formatting:', width=10)
        # self.tl_formatting = StringVar()
        # self.tl_formatting.set('[h:mm:ss] artist - title')
        # self.formatting_entry = Entry(self.formatting_container, width=43, state=DISABLED, textvariable=self.tl_formatting)
        self.formatting_instructions.grid(row=0, column=0, columnspan=2)
        # self.formatting_label.grid(row=1, column=0, sticky=W)
        # self.formatting_entry.grid(row=1, column=1, sticky=W)

        self.offline_tl_container = Frame(master)
        self.offline_tl_container.grid(row=9, column=1, columnspan=3, padx=10, sticky=W)
        self.offline_tl = Text(self.offline_tl_container, width=57, state=DISABLED, bg=self.website.cget('disabledbackground'), font=('Segoe UI', 8, 'normal'), wrap=WORD)
        self.offline_tl_vsb = Scrollbar(self.offline_tl_container, command=self.offline_tl.yview)
        self.offline_tl_vsb.pack(side=RIGHT, fill=Y)
        self.offline_tl.config(yscrollcommand=self.offline_tl_vsb.set)
        self.offline_tl.pack(side=LEFT)

        self.bot_but_containter = Frame(master)
        self.bot_but_containter.grid(row=10, column=0, columnspan=4, padx=10)

        self.log_label = StringVar()
        self.log_label.set('Logging off')
        self.log_var = BooleanVar()
        self.log_var.set(False)
        self.log_switch = Checkbutton(self.bot_but_containter, textvariable=self.log_label, variable=self.log_var, command=self.loggingChecked, width=8)
        self.log_switch.pack(side=LEFT)

        self.verifyButton = Button(self.bot_but_containter, text='Verify CUE...', command=lambda *args: self.convert2cue('verify'), default=ACTIVE)
        self.verifyButton.pack(side=RIGHT, pady=10)

        self.quickButton = Button(self.bot_but_containter, text='Quick CUE', command=lambda *args: self.convert2cue('quick'))
        self.quickButton.pack(side=RIGHT, pady=10, padx=(160, 10))

        self.method.set('online')

        # Set verify as default action for <Return>
        self.master.bind('<Return>', (lambda event, button=self.verifyButton: button.invoke()))

    def acquireAudioFile(self):
        self.filepath.set(filedialog.askopenfilename(filetypes=[('Audio files', ('*.mp3', '*.flac', '*.wav'))]))
        logging.info(f'Attempting to open file {self.filepath.get()}' if self.filepath.get() else 'File selection cancelled.')
        if self.filepath.get():
            try:
                file = EasyID3(self.filepath.get())
            except MutagenError as me:
                logging.warning(f'EasyID3 failed. Trying File method. {me}')
                try:
                    file = File(self.filepath.get())
                except MutagenError as me:
                    messagebox.showwarning('Bad file', 'Please select an MP3, FLAC, or WAV file.')
                    logging.warning(f'Failed to import file. {me}\n')
            if file:
                self.artistvar.set(file.get('artist')[0])
                self.titlevar.set(file.get('title')[0])
                self.yearvar.set(file.get('date'))
                self.genrevar.set(file.get('genre'))
                filename = self.filepath.get().split("/")[-1]
                if len(filename) > 70:
                    chars_to_remove = (len(filename) - 68) // 2
                    midpoint = len(filename) // 2
                    filename = f'{filename[:midpoint - chars_to_remove]}...{filename[midpoint + chars_to_remove:]}'
                self.file_name_var.set(filename)
                logging.info(f'Imported file "{self.file_name_var.get()}"')
                if logging.getLogger().getEffectiveLevel() < 50:
                    var_dic = {'Artist': self.artistvar, 'Title': self.titlevar, 'Year': self.yearvar, 'Genre': self.genrevar}
                    log_message = ['File properties:\n'] + [f'{" "*34}{key}: {value.get()}\n' for key, value in var_dic.items()]
                    logging.debug("".join(log_message))

    def acquireLabelFile(self):
        self.label_file_path.set(filedialog.askopenfilename(filetypes=[('Text','*.txt')]))
        logging.info(f'Opening Audacity label file from {self.label_file_path.get()}')

    def RadioClicked(self, var):
        if var == 'online':
            self.website.config(state=NORMAL)
            self.offline_tl.config(state=DISABLED, bg=self.website.cget('disabledbackground'))
            #self.formatting_entry.config(state=DISABLED)
        elif var == 'offline':
            self.offline_tl.config(state=NORMAL, bg='white')
            #self.formatting_entry.config(state=NORMAL)
            self.website.config(state=DISABLED)
        logging.info(f'Radio button clicked: {var}\n')

    def use_aud_labels(self):
        if self.aud_label_var.get():
            self.import_labels.config(state=NORMAL)
            self.label_file.config(state=NORMAL)
        else:
            self.import_labels.config(state=DISABLED)
            self.label_file.config(state=DISABLED)

    def loggingChecked(self):
        if self.log_var.get():
            self.log_label.set('Logging on')
            logging.basicConfig(handlers=[logging.FileHandler('log.txt', 'w', 'utf-8')], level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        else:
            self.log_label.set('Logging off')
            logging.basicConfig(level=logging.CRITICAL)

    def save_cue(self, website=None, soup=None):
        logging.info('Beginning CUE creation...')
        artist = self.artist.get() if self.artist.get() else '[ARTIST]'
        title = self.title.get() if self.title.get() else '[TITLE]'

        file = filedialog.asksaveasfile(defaultextension='.cue', filetypes=[('CUE', '*.cue')], initialfile=f'{artist} - {title}')
        logging.info(f'Saving to {file.name}' if file else 'CUE creation cancelled.\n')
        if file:
            year = self.year.get() if self.year.get() else '9999'
            genre = self.genre.get() if self.genre.get() else '[GENRE]'
            if self.filepath.get():
                filename = self.filepath.get().split('/')[-1]
            else:
                filename = '[PLEASE MANUALLY INSERT FILENAME]'
            filetypes = {'wav': 'WAVE', 'lac': 'WAVE', 'mp3': 'MP3', 'ME]': '[INSERT FILE TYPE]'}

            try:
                file.write(f'REM GENRE {genre}\n')
                file.write(f'REM DATE {year}\n')
                if website:
                    short_url = soup.find('td', text='short url').next_sibling.next_sibling.contents[0]['href']
                    file.write(f'REM WWW {short_url}\n')
                file.write(f'PERFORMER "{artist}"\n')
                file.write(f'TITLE "{title}"\n')
                file.write(f'FILE "{filename}" {filetypes[filename[-3:]]}\n')
                for track in self.tracks:
                    file.write(f'    TRACK {track["track"]} AUDIO\n')
                    file.write(f'        TITLE "{track["title"]}"\n')
                    file.write(f'        PERFORMER "{track["artist"]}"\n')
                    file.write(f'        INDEX 01 {track["cuetime"]}\n')
                success = True
                exception = None
                logging.info('CUE creation successful.')
            except Exception as e:
                success = False
                exception = e.args[1]
                logging.warning(f'Error during creation of CUE. {exception}')
            finally:
                file.close()
                return success, exception
        else:
            return False, False

    def super_parent(self, span):
        return span.parent.parent.parent.parent.parent.parent.parent

    def with_track(self, wtrack, i):
        if self.tracks[i]['cuetime'] != 'w/':
            self.tracks[i]['artist'] += f' vs. {wtrack["artist"]}'
            self.tracks[i]['title'] += f' vs. {wtrack["title"]}'
        else:
            self.with_track(wtrack, i - 1)

    def clean_tracks(self):
        cleaned_tracks = []
        if self.aud_label_var.get():
            cuetimes = get_audacity_labels(self.label_file_path.get())
            real_tracks = [track for track in self.tracks if track['track'] != 'w/']
            if len(cuetimes) != len(real_tracks):
                messagebox.showwarning('', f"There are {len(cuetimes)} cuetimes in the Audacity label file, but {len(real_tracks)} tracks.\n\nIf there is one fewer cuetime than tracks, it is most likely because there is no label at the start of the audio file and quickCUE will now try to compensate.\n\nIf there is a greater discrepancy, please double check your labels.")
                if len(real_tracks) - len(cuetimes) == 1:
                    cuetimes.insert(0, '00:00:00')
                elif len(real_tracks) - len(cuetimes) > 1:
                    while len(cuetimes) != len(real_tracks):
                        cuetimes.append('')
            logging.info('Edited cuetimes acquired from Audacity label file!')
            logging.debug(cuetimes)

        for i, track in enumerate(self.tracks):
            if track['track'] == 'w/':
                self.with_track(track, i - 1)
            elif self.aud_label_var.get():
                track['cuetime'] = clean_cuetime(track, cuetimes[int(track['track'])-1])
            else:
                track['cuetime'] = clean_cuetime(track)

        for track in self.tracks:
            if track['track'] != 'w/':
                cleaned_tracks.append(track)
        if logging.getLogger().getEffectiveLevel() < 50:
            message = []
            for track in self.tracks:
                if track['track'] != 'w/':
                    message.append(f'{" "*34}{track["cuetime"].rjust(9)}  {track["artist"]} - {track["title"]}\n')
                else:
                    message.append(f'{" "*34}{"Merged":^9s}  {track["artist"]} - {track["title"]}\n')
            log_message = [f'Cleaned cuetimes and tracks ({len(cleaned_tracks)}):\n'] + message
            logging.debug("".join(log_message))
        return cleaned_tracks

    def convert2cue(self, type):
        self.quickButton.config(state=DISABLED)
        self.verifyButton.config(state=DISABLED)

        open_success = False

        if self.method.get() == 'online':
            try:
                website = self.website.get()
                logging.info(f'Attempting to open {website}')
                if '1001tracklists' not in website and '1001.tl' not in website:
                    raise SiteValidationError
                soup = BeautifulSoup(urlopen(website), 'lxml')
                open_success = True
                logging.info('Successfully opened site.\n')
            except SiteValidationError as e:
                open_success = False
                messagebox.showwarning('Warning!', 'Please provide a 1001tracklists.com or 1001.tl link.')
                logging.warning('Website not 1001tracklists.com or 1001.tl link. {e}\n')
            except Exception as e:
                open_success = False
                messagebox.showerror('Error!', 'Could not reach site. Please verify and try again.')
                logging.warning('Unable to reach site. {e}\n')

            if open_success:
                cuetimes = [div.text.strip() for div in soup.find_all('div', class_='cueValueField')]
                track_nos = [no.text.strip() for no in soup.find_all('span', id=re.compile('_tracknumber_value'))]
                spans = soup.find_all('span', class_='trackFormat')
                self.tracks = []
                skipped = 0
                for i, span in enumerate(spans):
                    if 'tgHid' in self.super_parent(span)['class']:
                        skipped += 1
                        continue
                    artist, title = spans[i].text.strip().replace(u'\xa0', u' ').split(' - ')
                    status = span.next_sibling.next_sibling
                    if status and 'trackStatus' in status['class']:
                        title += f' {status.text.strip()}'
                    self.tracks.append({'track': track_nos[i - skipped], 'cuetime': cuetimes[i - skipped], 'artist': artist, 'title': title})
                if logging.getLogger().getEffectiveLevel() < 50:
                    log_message = [f'Original tracks ({len(self.tracks)}):\n'] + [f'{" "*34}{track["track"]}  {track["cuetime"].rjust(7)}  {track["artist"]} - {track["title"]}\n' for track in self.tracks]
                    logging.debug("".join(log_message))
        elif self.method.get() == 'offline':
            offline_tl = self.offline_tl.get('1.0', 'end-1c')
            '''Info for the following regex:
               Group 1: \[?(w/|\d?:?\d+:\d+)?\]? --> optional brackets to handle non-bracketed times --> cuetime
               Group 2:  (.*) - --> all text after the above and before ' - '--> artist
               Group 3: ([^\[\]\n]+).*$ --> all characters but []\n followed by any character and end line --> title
                        title has trailing space'''
            match = re.findall(r'\[?(w/|\d?:?\d+:\d+)?\]? (.*) - ([^\[\]\n]+).*$', offline_tl, re.MULTILINE)
            self.tracks = []
            track_no = 1
            for item in match:
                trackno = str(track_no).zfill(2)
                track = {'track': '', 'cuetime': '', 'artist': '', 'title': ''}

                if item[0] == 'w/':
                    track['track'] = 'w/'
                    track['cuetime'] = ''
                else:
                    track['track'] = trackno
                    track['cuetime'] = item[0]
                    track_no += 1

                track['artist'] = item[1]
                track['title'] = item[2].strip()
                self.tracks.append(track)
            if logging.getLogger().getEffectiveLevel() < 50:
                log_message = [f'Original tracks ({len(self.tracks)}):\n'] + [f'{" "*34}{track["track"]}  {track["cuetime"].rjust(7)}  {track["artist"]} - {track["title"]}\n' for track in self.tracks]
                logging.debug("".join(log_message))
            website = None
            offline_prep_success = True

        self.tracks = self.clean_tracks()

        if (open_success and self.method.get() == 'online') or (offline_prep_success and self.method.get() == 'offline'):
            if type == 'verify':
                verified, tracklist = verify_information(root, self.tracks)
            if verified:
                self.tracks = return_tracks(tracklist)
                if website:
                    success, error = self.save_cue(website, soup)
                else:
                    success, error = self.save_cue()
                if success:
                    messagebox.showinfo('', 'Conversion to cue complete!')
                    logging.info('Conversion to cue complete!\n')
                elif not success and error:
                    messagebox.showwarning('', f'Error - please verify and try again.\n{error}')
                    logging.error(f'Conversion to cue failed! {error}\n')
                else:
                    pass

        self.verifyButton.config(state=NORMAL)
        self.quickButton.config(state=NORMAL)


root = Tk()
root.resizable(0, 0)
gui = mainWindow(root)
root.mainloop()
