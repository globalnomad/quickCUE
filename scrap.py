class track():
    total_tracks = 0

    def __init__(self, artist, title, cuetime):
        self.__artist = artist
        self.__title = title
        self.__cuetime = cuetime
        self.__trackNumber = track.total_tracks + 1
        self.__trackID = track.total_tracks + 1
        track.total_tracks += 1

    def updateTrackNumber(self, tracklist):
        difference = self.trackNumber - tracklist.index(self)
        if difference != 1:
            self.trackNumber -= difference-1
        else:
            pass

    def display_cue(self):
        h = str(self.__cuetime.get() // 3600).zfill(2)
        m = str((self.__cuetime.get() - h * 3600) // 60).zfill(2)
        s = str(self.__cuetime.get() - h * 3600 - m * 60).zfill(2)
        return f'{h}:{m}:{s}'

    def clean_cuetime(self, cuetime):
        if self.__trackNumber == '01' and not cuetime:
            return 0
        elif ':' not in cuetime:
            return 0
        else:
            hms = cuetime.split(':')
            if len(hms) < 3:
                hms.insert(0,'0')
            [h, m, s] = self.__cuetime.split(':')
            return int(h) * 3600 + int(m) * 60 + int(s)

    def adjust_cuetime(self, min_adj, sec_adj, early_or_late):
        adjustment = int(min_adj) * 60 + int(sec_adj)
        if self.__cuetime:
            split_cue = self.__cuetime.split(':')
            cue_secs = int(split_cue[0]) * 60 + int(split_cue[1])
            if early_or_late == '-':
                cue_secs -= adjustment
                if cue_secs < 0:
                    cue_secs = 0
            else:
                cue_secs += adjustment
            self.__cuetime =':'.join([str(cue_secs // 60).zfill(2), str(cue_secs % 60).zfill(2), '00'])
        else:
            pass

    def clean_track(self, cuesheet, aud_label_var):
        if aud_label_var:
            cuetimes = get_audacity_labels(self.label_file_path.get())
            real_tracks = [track for track in cuesheet.tracklist if track.__TLtrack != 'w/']
            if len(cuetimes) != len(real_tracks):
                messagebox.showwarning('', f"There are {len(cuetimes)} cuetimes in the Audacity label file, but {len(real_tracks)} tracks.\n\nIf there is one fewer cuetime than tracks, it is most likely because there is no label at the start of the audio file and quickCUE will now try to compensate.\n\nIf there is a greater discrepancy, please double check your labels.")
                if len(real_tracks) - len(cuetimes) == 1:
                    cuetimes.insert(0, '00:00:00')
                elif len(real_tracks) - len(cuetimes) > 1:
                    while len(cuetimes) != len(real_tracks):
                        cuetimes.append('')
            logging.info('Edited cuetimes acquired from Audacity label file!')
            logging.debug(cuetimes)
