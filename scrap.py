        elif cuetimes[i].count(':') == 1:
            min_sec = cuetimes[i].split(':')
            newtime = int(min_sec[0]) * 60 + int(min_sec[1])
        else:
            hr_min_sec = cuetimes[i].split(':')
            newtime = int(hr_min_sec[0]) * 3600 + int(hr_min_sec[1]) * 60 + int(hr_min_sec[2])