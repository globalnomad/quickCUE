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

class track():
    total_tracks = 0
    def __init__(self, artist, title, cuetime):
        self.__artist = artist
        self.__title = title
        self.__cuetime = cuetime
        self.trackNumber = track.total_tracks + 1
        self.trackID = track.total_tracks + 1
        track.total_tracks += 1
    def getArtist(self):
        return self.__artist.get()
    def setArtist(self, artist):
        self.__artist.set(artist)
    def getTitle(self):
        return self.__title.get()
    def setTitle(self, cue):
        self.__title.set(cue)
    def getCue(self):
        return self.__cuetime.get()
    def setCue(self, cue):
        self.__cuetime.set(cue)
    def updateTrackNumber(self, tracklist):
        difference = self.trackNumber - tracklist.index(self)
        if difference != 1:
            self.trackNumber -= difference-1
        else:
            pass

def get_audacity_labels(label_file_path):
    with open(label_file_path, 'r') as audacity_labels:
        cuetimes = []
        for line in audacity_labels:
            time = float(line.split()[0])
            m = str(int(time // 60)).zfill(2)
            s = str(int(time) % 60).zfill(2)
            f = str(int((time - int(time)) * 75)).zfill(2)
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


def verify_information(TLroot, in_tracks, bg_dark, bg_light):
    logging.info('Opening verification window...')
    master = Toplevel(TLroot)
    master.iconbitmap('quickCUE.ico')
    master.title('Verify Information...')

    tracks = []
    for in_track in in_tracks:
        track = {'track': StringVar(), 'cuetime': StringVar(), 'artist': StringVar(), 'title': StringVar()}
        track['track'].set(in_track['track'])
        track['cuetime'].set(in_track['cuetime'])
        track['artist'].set(in_track['artist'])
        track['title'].set(in_track['title'])
        tracks.append(track)

    gui2 = verification_window(master, tracks, bg_dark, bg_light)
    master.lift()
    master.focus_force()

    master.wait_window()
    return (gui2.verified, tracks)


class verification_window():
    def __init__(self, master, tracklist, bg_dark, bg_light):
        self.master = master
        self.tracklist = tracklist

        # To handle x-ing or canceling verification
        self.verified = False

        # Colors
        self.bg_dark = bg_dark
        self.bg_light = bg_light

        self.verify_top_frame = Frame(self.master, borderwidth=0, bg=self.bg_dark)
        self.verify_mid_frame = Frame(self.master, borderwidth=0, bg=self.bg_light)
        self.verify_bot_frame = Frame(self.master, borderwidth=0, bg=self.bg_light)
        self.verify_top_frame.pack(fill=X)
        self.verify_bot_frame.pack(side=BOTTOM, fill=X)
        self.verify_mid_frame.pack(expand=True, fill=Y)

        # Pack into verify_top_frame
        self.instructions = Label(self.verify_top_frame, text='Verify and edit...', bg=self.bg_dark, font=('Segoe UI', 12, 'bold'))
        self.instructions.pack(side=LEFT, padx=5)

        # Pack into verify_mid_frame
        self.canvas = Canvas(self.verify_mid_frame, width=615, height=500, highlightthickness=0, bg=self.bg_light)
        self.vsb = Scrollbar(self.verify_mid_frame, command=self.canvas.yview)
        self.canvas.pack(side=LEFT, expand=True, fill=Y, pady=10)
        self.vsb.pack(side=RIGHT, fill=Y)

        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.bind('<Configure>', self.on_configure)

        # Pack into canvas (which is in verify_mid_frame)
        self.frame = Frame(self.canvas, bg=self.bg_light)
        self.canvas.create_window((0, 0), window=self.frame, anchor=NW)

        self.frame.bind('<Enter>', self._bind_to_mousewheel)
        self.frame.bind('<Leave>', self._unbind_to_mousewheel)

        # Pack into frame (which is in canvas (which is in verify_mid_frame))
        self.track_widgets = []
        for i, track in enumerate(self.tracklist):
            widget = {}

            widget['label'] = Label(self.frame, text=f'Track {track["track"].get()})', width=7, bg=self.bg_light)
            widget['label'].grid(row=i, column=1, sticky=E)

            widget['cuetime'] = Entry(self.frame, width=10, textvariable=track['cuetime'])
            widget['cuetime'].grid(row=i, column=2, padx=1)

            widget['artist'] = Entry(self.frame, width=30, textvariable=track['artist'])
            widget['artist'].grid(row=i, column=3, padx=1)

            widget['title'] = Entry(self.frame, width=50, textvariable=track['title'])
            widget['title'].grid(row=i, column=4, padx=(1, 7))

        self.track_widgets.append(widget)

        # Pack into verify_bot_frame
        self.bot_container = Frame(self.verify_bot_frame, bg=self.bg_light)
        self.bot_container.pack(anchor=CENTER)

        # Pack into bot_container (which is in verify_bot_frame)
        self.min_var = StringVar()
        self.sec_var = StringVar()
        self.early_or_late = StringVar()
        self.min_var.trace('w', lambda *args: self.adj_limit_check(self.min_var))
        self.sec_var.trace('w', lambda *args: self.adj_limit_check(self.sec_var))

        self.adj_instructions = Label(self.bot_container, text='Adjust all cue times by', bg=self.bg_light)
        self.min_adj = Entry(self.bot_container, width=5, textvariable=self.min_var)
        self.min_adj_lbl = Label(self.bot_container, text='m', bg=self.bg_light)
        self.sec_adj = Entry(self.bot_container, width=5, textvariable=self.sec_var)
        self.sec_adj_lbl = Label(self.bot_container, text='s', bg=self.bg_light)
        self.earlier = Radiobutton(self.bot_container, variable=self.early_or_late, value='-', text='earlier', bg=self.bg_light)
        self.later = Radiobutton(self.bot_container, variable=self.early_or_late, value='+', text='later', bg=self.bg_light)
        self.adjust_button = Button(self.bot_container, text='Adjust', font=('Segoe UI', 8, 'normal'), borderwidth=1, command=self.adjust_cuetimes, bg=self.bg_dark, fg=self.bg_light)
        self.cancel_button = Button(self.bot_container, text='Cancel', command=self.master.destroy, bg=self.bg_dark, fg=self.bg_light)
        self.confirm_button = Button(self.bot_container, text='Confirm', command=self.complete_verification, font=('Segoe UI', 9, 'bold'), default=ACTIVE, bg=self.bg_dark, fg=self.bg_light)

        self.adj_instructions.grid(row=0, column=0, sticky=E)
        self.min_adj.grid(row=0, column=1)
        self.min_adj_lbl.grid(row=0, column=2)
        self.sec_adj.grid(row=0, column=3)
        self.sec_adj_lbl.grid(row=0, column=4)
        self.earlier.grid(row=0, column=5)
        self.later.grid(row=0, column=6)
        self.adjust_button.grid(row=0, column=7)
        self.cancel_button.grid(row=1, column=0, pady=5, columnspan=4)
        self.confirm_button.grid(row=1, column=4, pady=5, columnspan=4)

        self.min_var.set('0')
        self.sec_var.set('0')
        self.early_or_late.set('-')

        self.min_adj.bind('<FocusOut>', lambda *args: self.zero_fill(self.min_var))
        self.sec_adj.bind('<FocusOut>', lambda *args: self.zero_fill(self.sec_var))

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
            if cuetime:
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
        self.method.set('online')

        # Background colors
        self.bg_light = 'ghost white'
        self.bg_dark = 'light slate gray'
        self.bg_disabled = 'ghost white'

        # Holding frames for GUI
        self.step1_frame = Frame(master, bg=self.bg_dark)
        self.main_top_frame = Frame(master, bg=self.bg_light)
        self.step2_frame = Frame(master, bg=self.bg_dark)
        self.main_tag_frame = Frame(master, bg=self.bg_light)
        self.step3_frame = Frame(master, bg=self.bg_dark)
        self.main_tlimport_frame = Frame(master, bg=self.bg_light)
        self.step4_frame = Frame(master, bg=self.bg_dark)
        self.main_options_frame = Frame(master, bg=self.bg_light)
        self.bot_buttons_frame = Frame(master,bg=self.bg_light)
        self.bot_text_frame = Frame(master, bg=self.bg_light)
        self.step1_frame.pack(fill=X)
        self.main_top_frame.pack(fill=X)
        self.step2_frame.pack(fill=X)
        self.main_tag_frame.pack(fill=X)
        self.step3_frame.pack(fill=X)
        self.main_tlimport_frame.pack(fill=X)
        self.step4_frame.pack(fill=X)
        self.main_options_frame.pack(fill=X)
        self.bot_buttons_frame.pack(fill=X)
        self.bot_text_frame.pack(fill=X)

        # Pack into step1_frame
        self.step1 = Label(self.step1_frame, text='Select file...', bg=self.bg_dark, font=('Segoe UI', 12, 'bold'), anchor=W)
        self.step1.pack(side=LEFT, padx=5)

        # Pack into main_top_frame
        self.instructions = Message(self.main_top_frame, text='Please select the target audio file and correct the information below as necessary. This step is optional, but tells the CUE file which audio file to use.', width=290, bg=self.bg_light)
        self.getFileButton = Button(self.main_top_frame, text='Select target MP3, FLAC, or WAV...', wraplength=130, width=15, borderwidth=2, command=self.acquireAudioFile, fg=self.bg_light, bg=self.bg_dark)
        self.instructions.pack(side=LEFT, padx=(5, 0), pady=(0, 5))
        self.getFileButton.pack(side=RIGHT, padx=(5, 10), pady=(0, 5))

        # Pack into step2_frame
        self.step2 = Label(self.step2_frame, text='Verify file data...', bg=self.bg_dark, font=('Segoe UI', 12, 'bold'), anchor=W)
        self.step2.pack(side=LEFT, padx=5)

        # Pack into main_tag_frame
        self.file_name_var = StringVar()
        self.file_name_var.set('[No file selected]')

        self.file_name = Label(self.main_tag_frame, textvariable=self.file_name_var, font=('Segoe UI', 8, 'italic'), width=60, bg=self.bg_light)
        self.artistLabel = Label(self.main_tag_frame, text='Artist:', width=4, bg=self.bg_light)
        self.artist = Entry(self.main_tag_frame, width=60, text=self.artistvar)
        self.titleLabel = Label(self.main_tag_frame, text='Title:', width=4, bg=self.bg_light)
        self.title = Entry(self.main_tag_frame, width=60, text=self.titlevar)
        self.file_name.grid(row=0, column=1, columnspan=3)
        self.artistLabel.grid(row=1, column=0, sticky=W, padx=(5, 0))
        self.artist.grid(row=1, column=1, columnspan=3, pady=3, padx=10, sticky=W)
        self.titleLabel.grid(row=2, column=0, sticky=W, padx=(5, 0))
        self.title.grid(row=2, column=1, columnspan=3, pady=3, padx=10, sticky=W)

        self.yg_frame = Frame(self.main_tag_frame, bg=self.bg_light)
        self.yg_frame.grid(row=3, column=0, columnspan=4, sticky=W, pady=(0, 5))

        # Pack into yg_frame (which is in main_tag_frame)
        self.yearLabel = Label(self.yg_frame, text='Year:', width=4, bg=self.bg_light)
        self.year = Entry(self.yg_frame, width=5, text=self.yearvar)
        self.genreLabel = Label(self.yg_frame, text='Genre:', bg=self.bg_light)
        self.genre = Entry(self.yg_frame, width=15, text=self.genrevar)
        self.yearLabel.grid(row=0, column=0, sticky=W, padx=(5, 0))
        self.year.grid(row=0, column=1, pady=3, padx=10, sticky=W)
        self.genreLabel.grid(row=0, column=2, sticky=E)
        self.genre.grid(row=0, column=3, pady=3, padx=10, sticky=W)

        # Pack into step3_frame
        self.step3 = Label(self.step3_frame, text='Select tracklist...', bg=self.bg_dark, font=('Segoe UI', 12, 'bold'), anchor=W)
        self.step3.pack(side=LEFT, padx=5)

        # Pack into main_tlimport_frame
        self.spacer_radio1 = Label(self.main_tlimport_frame, text='', width=5, bg=self.bg_light)
        self.webRadioButton = Radiobutton(self.main_tlimport_frame, text='1001 Tracklists link:', variable=self.method, value='online', command=lambda: self.RadioClicked('online'), takefocus=0, bg=self.bg_light)
        self.spacer_radio1entry = Label(self.main_tlimport_frame, text='', width=5, bg=self.bg_light)
        self.website = Entry(self.main_tlimport_frame, width=60, disabledbackground=self.bg_disabled)
        self.spacer_radio2 = Label(self.main_tlimport_frame, text='', width=5, bg=self.bg_light)
        self.customRadioButton = Radiobutton(self.main_tlimport_frame, text='Custom tracklist:', variable=self.method, value='offline', command=lambda: self.RadioClicked('offline'), takefocus=0, bg=self.bg_light)
        self.spacer_radio2entry = Label(self.main_tlimport_frame, text='', width=5, bg=self.bg_light)
        self.formatting_container = Frame(self.main_tlimport_frame, bg=self.bg_light)
        self.offline_tl_container = Frame(self.main_tlimport_frame, bg=self.bg_light)
        self.spacer_radio1.grid(row=0, column=0)
        self.webRadioButton.grid(row=0, column=1, columnspan=3, sticky=W)
        self.spacer_radio1entry.grid(row=1, column=0)
        self.website.grid(row=1, column=1, columnspan=3, padx=10, sticky=W)
        self.spacer_radio2.grid(row=2, column=0)
        self.customRadioButton.grid(row=2, column=1, columnspan=3, sticky=W, pady=(10, 0))
        self.spacer_radio2entry.grid(row=3, column=0)
        self.formatting_container.grid(row=3, column=1, columnspan=3, sticky=W)
        self.offline_tl_container.grid(row=4, column=1, columnspan=3, sticky=W)

        # Pack into formatting_container (which is in main_tlimport_frame)
        self.formatting_instructions = Label(self.formatting_container, text='Please input one track per line.', bg=self.bg_light)
        self.formatting_help = Button(self.formatting_container, text='Formatting Help', fg='blue', bg=self.bg_light, font=('Segoe UI', 9, 'underline'), borderwidth=0, command=self.help_format, takefocus=0, cursor='hand2')
        self.formatting_instructions.grid(row=0, column=0, columnspan=2)
        self.formatting_help.grid(row=1, column=0, columnspan=2, sticky=W, pady=(0, 5))

        # Pack into offline_tl_container (which is in main_tlimport_frame)
        self.offline_tl = Text(self.offline_tl_container, width=59, height=20, state=DISABLED, bg=self.bg_disabled, font=('Segoe UI', 8, 'normal'), wrap=WORD)
        self.offline_tl_vsb = Scrollbar(self.offline_tl_container, command=self.offline_tl.yview)
        self.offline_tl_vsb.pack(side=RIGHT, fill=Y, pady=(0, 7))
        self.offline_tl.config(yscrollcommand=self.offline_tl_vsb.set)
        self.offline_tl.pack(side=LEFT, pady=(0, 7))

        # Pack into step4_frame
        self.step4 = Label(self.step4_frame, text='Options...', bg=self.bg_dark, font=('Segoe UI', 12, 'bold'), anchor=W)
        self.step4.pack(side=LEFT, padx=5)

        # Pack into main_options_frame
        self.aud_label_var = BooleanVar()
        self.label_file_path = StringVar()

        self.spacer_labels = Label(self.main_options_frame, text='', width=5, bg=self.bg_light)
        self.audacity_label = Checkbutton(self.main_options_frame, text='Optionally import an Audacity label file.', variable=self.aud_label_var, command=self.use_aud_labels, takefocus=0, font=('Segoe UI', 10, 'italic'), bg=self.bg_light)
        self.import_labels = Button(self.main_options_frame, text='Import Labels', state=DISABLED, command=self.acquireLabelFile, bg=self.bg_dark, fg=self.bg_light)
        self.label_file = Entry(self.main_options_frame, textvariable=self.label_file_path, width=46, state=DISABLED, disabledbackground=self.bg_disabled)
        self.spacer_labels.grid(row=0, column=0)
        self.audacity_label.grid(row=0, column=1, columnspan=2, sticky=W)
        self.import_labels.grid(row=1, column=1, pady=(0, 5))
        self.label_file.grid(row=1, column=2, columnspan=2, padx=10, pady=(0, 5))

        # Pack into bot_buttons_frame
        self.log_label = StringVar()
        self.log_label.set('Logging off')
        self.log_var = BooleanVar()
        self.log_var.set(False)

        self.log_switch = Checkbutton(self.bot_buttons_frame, textvariable=self.log_label, variable=self.log_var, command=self.loggingChecked, width=8, takefocus=0, bg=self.bg_light)
        self.verifyButton = Button(self.bot_buttons_frame, text='Verify CUE...', command=lambda *args: self.convert2cue('verify'), default=ACTIVE, bg=self.bg_dark, fg=self.bg_light)
        self.quickButton = Button(self.bot_buttons_frame, text='quickCUE', command=lambda *args: self.convert2cue('quick'), takefocus=0, bg=self.bg_dark, fg=self.bg_light)
        self.log_switch.pack(side=LEFT)
        self.verifyButton.pack(side=RIGHT, padx=10, pady=(5, 0))
        self.quickButton.pack(side=RIGHT, padx=(160, 0), pady=(5, 0))

        # Pack into bot_text_frame
        self.center_text = Frame(self.bot_text_frame, bg=self.bg_light)
        self.center_text.pack()

        # Pack into center_text (which is in bot_text_frame)
        self.appInfo = Button(self.center_text, text='About', fg='blue', bg=self.bg_light, font=('Segoe UI', 8, 'underline'), borderwidth=0, cursor='hand2', command=self.info, takefocus=0)
        self.version = Label(self.center_text, text='v1.1.0', bg=self.bg_light)
        self.appHelp = Button(self.center_text, text='Help', fg='blue', bg=self.bg_light, font=('Segoe UI', 8, 'underline'), borderwidth=0, cursor='hand2', command=self.help, takefocus=0)
        self.appInfo.pack(side=RIGHT, padx=1, pady=(5, 10))
        self.version.pack(side=RIGHT, pady=(5, 10))
        self.appHelp.pack(side=RIGHT, padx=1, pady=(5, 10))

    def acquireAudioFile(self):
        self.filepath.set(filedialog.askopenfilename(filetypes=[('Audio files', ('*.mp3', '*.m4a', '*.flac', '*.wav'))]))
        logging.info(f'Attempting to open file {self.filepath.get()}' if self.filepath.get() else 'File selection cancelled.')
        if self.filepath.get():
            try:
                file = EasyID3(self.filepath.get())
            except MutagenError as me:
                logging.warning(f'EasyID3 failed. Trying File method. {me}')
                try:
                    file = File(self.filepath.get())
                except MutagenError as me:
                    messagebox.showwarning('Bad file', 'Please select an MP3, FLAC, M4A or WAV file.')
                    logging.warning(f'Failed to import file. {me}\n')
            if file:
                if self.filepath.get()[-4:].lower() !=  '.m4a':
                    self.artistvar.set(file.get('artist')[0])
                    self.titlevar.set(file.get('title')[0])
                    self.yearvar.set(file.get('date'))
                    self.genrevar.set(file.get('genre'))
                else:
                    self.artistvar.set(file.get('\xa9ART')[0])
                    self.titlevar.set(file.get('\xa9nam')[0])
                    self.yearvar.set(file.get('\xa9day'))
                    self.genrevar.set(file.get('\xa9gen'))
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
        self.label_file_path.set(filedialog.askopenfilename(filetypes=[('Text', '*.txt')]))
        logging.info(f'Opening Audacity label file from {self.label_file_path.get()}')

    def RadioClicked(self, var):
        if var == 'online':
            self.website.config(state=NORMAL)
            self.offline_tl.config(state=DISABLED, bg=self.bg_disabled, fg=self.bg_disabled)
        elif var == 'offline':
            self.offline_tl.config(state=NORMAL, bg='white', fg='black')
            self.website.config(state=DISABLED)
        logging.info(f'Radio button clicked: {var}\n')

    def help_format(self):
        messagebox.showinfo('Help with formatting', '\n'.join(['Tracks can be formatted in any of the following ways. Note that any non-alphanumeric character is a literal. (e.g. [text] means text surrounded by [ and ].\n', 'Basic format: [cue] artist - title [other_text]\n', 'All cuetimes can be read with or without the surrounding [ ]. Cues can be formatted as:   [h:mm:ss]   or   [mmm:ss]\n', '"other_text" is discarded and is optional. It\'s there to handle some tracklists that may include release label info. It must be surrounded by [ ].\n', 'Any text prior to the artist and not a cue will be discarded (e.g., track numbers).\n', "I haven't seen any tracklists using frames (e.g. mm:ss:ff), so the algorithm doesn't parse frames on input. Cues are converted into mm:ss:ff format by quickCUE. If you'd like the option to parse cues with frames, please contact me (see Help).\n", '[other text] following the title is optional. It is included in the algorithm to identify labels placed there by default 1001TL tracklist exporting.']))

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

    def help(self):
        messagebox.showinfo('Help with quickCUE', '\n'.join(['Select an audio file that the CUE will be tied to. This will autofill the Artist, Title, Year, and Genre fields if the file is properly tagged. Otherwise, please manually fill those in.\n', 'If you want to use cues from an exported Audacity label file, please check the box then import the label file.\n', 'Paste a direct link to the set page on 1001TL or paste in a tracklist.\n', "Quick CUE will skip verification and immediately make the CUE file. Use this if you're 100% confident about your tracklist and cues. Otherwise, please use Verify CUE.\n", 'Any fields left blank on this screen (other than the 1001TL link or Custom TL text box) can be manually edited in the generated CUE file.', 'Check logging if you run into an error as the log file it creates will help me track it down. Note that logging only begins AFTER logging has been checked, so you will need to repeat the steps you took - thanks!']))

    def info(self):
        messagebox.showinfo('About quickCUE', '\n'.join(['App made by /u/aglobalnomad. Please message me on Reddit if you have any questions, issues, or suggestions.\n', 'Shout out to /r/trance!\n', 'Icon made by Kiranshastry from www.flaticon.com and is licensed by CC 3.0 BY.\n', 'Kiranshastry: https://www.flaticon.com/authors/kiranshastry', 'Flaticon: https://www.flaticon.com/', 'CC: http://creativecommons.org/licenses/by/3.0/']))

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
            filetypes = {'wav': 'WAVE', 'lac': 'WAVE', 'm4a' : 'WAVE', 'mp3': 'MP3', 'ME]': '[INSERT FILE TYPE]'}

            try:
                file.write(f'REM GENRE {genre}\n')
                file.write(f'REM DATE {year}\n')
                if website:
                    short_url = 'https://' + soup.find('td', text='short link').next_sibling.next_sibling.text.strip()
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
                exception = e.args[0]
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
                track['cuetime'] = clean_cuetime(track, cuetimes[int(track['track']) - 1])
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
        type_log_msg = {'quick': 'Beginning creation with quickCUE...', 'verify': 'Beginning creation with verification...'}
        logging.info(type_log_msg[type])

        open_success = False

        if self.method.get() == 'online':
            try:
                website = self.website.get()
                logging.info(f'Attempting to open {website}')
                full_url_check = re.search(r'1001tracklists\.com/tracklist/.{8}/', website)
                short_url_check = re.search(r'http://1001\.tl/.{8}', website)
                if full_url_check or short_url_check:
                    soup = BeautifulSoup(urlopen(website), 'lxml')
                    open_success = True
                    logging.info('Successfully opened site.\n')
                else:
                    raise SiteValidationError
            except SiteValidationError as e:
                open_success = False
                messagebox.showwarning('Warning!', 'Please provide a valid 1001tracklists.com or 1001.tl tracklist link.\n\n1001TL is picky with URLs, so if you are using a 1001.tl short URL, provide it in the form of:  http://www.1001.tl/12345678')
                logging.warning(f'Website not 1001tracklists.com or 1001.tl tracklist link.\n{" "*36}Not a valid tracklist link: {website}\n')
            except Exception as e:
                open_success = False
                messagebox.showerror('Error!', 'Could not reach site. Please verify and try again.')
                logging.warning(f'Unable to reach site.\n{" "*36}{e}\n')

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
            if offline_tl:
                '''Info for the following regex:
                Group 1: \[?(w/|\d?:?\d+:\d+)?\]? --> optional brackets to handle non-bracketed times --> cuetime
                Group 2:  (.*) - --> all text after the above and before ' - '--> artist
                Group 3: ([^\[\]\n]+).*$ --> all characters but []\n followed by any character and end line --> title (title has trailing space)'''
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
                if self.tracks:
                    website = None
                    open_success = True
                else:
                    messagebox.showwarning('Improper formatting', 'Please see the Formatting Help and input a properly formatted tracklist.')
                    logging.warning('Improperly formatted tracklist input into text field.')
                    open_success = False
            else:
                messagebox.showwarning('No tracklist', 'Please input a tracklist into the text field.')
                logging.warning('No tracklist input into text field.')
                open_success = False

        if open_success:
            self.tracks = self.clean_tracks()
            if type == 'verify':
                quick = False
                verified, tracklist = verify_information(root, self.tracks, self.bg_dark, self.bg_light)
            else:
                quick = True
                verified = False
            if verified or quick:
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
root.iconbitmap('quickCUE.ico')
gui = mainWindow(root)
root.mainloop()
