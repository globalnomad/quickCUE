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
    def clean_cuetime(self, cuetime=None):
        if cuetime:
            self.__cuetime = cuetime
        else:
            if self.trackNumber == '01' and not self.__cuetime:
                self.__cuetime = '00:00:00'
            elif self.__cuetime.count(':') == 1:
                min_sec = self.__cuetime.split(':')
                self.__cuetime = '{0}:{1}:00'.format(min_sec[0].zfill(2), min_sec[1])
            else:
                hms = self.__cuetime.split(':')
                m, s = int(hms[0]) * 60 + int(hms[1]), hms[2]
                self.__cuetime = f'{m}:{s}:00'