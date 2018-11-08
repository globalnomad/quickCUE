from re import MULTILINE, findall, search

# test string
teststring = "00:00 test me - testerroo [ANJUNADEEP]\n01. boerd - Fragment II [ANJUNADEEP]\n[7:18] Timecop1983 - Tonight\n[11:21] Padai - Iglu [SUDBEAT]\n[17:22] Röyksopp - Sordid Affair [DOG TRIUMPH]\n[22:25] Libranine - Orca [GHOST DIGITAL]\n[28:11] Forerunners - Just For A While [PURE PROGRESSIVE]\n[35:16] Karmon - Eleventh Hour [DIYNAMIC]\n[40:40] Acid Pauli - Nana [PAMPA]\n[46:15] ID - ID\n[51:55] Van der Trip - Lunar Trip [1.2. TRIP]\n[57:21] Paul Oakenfold ft. Carla Werner - Southern Sun (Solarstone After Hours Mix) (Robert Nickson pres. RNX Edit) [PERFECTO]\n[1:03:40] Lunar Park - Tantra [BONZAI PROG]\n[1:08:30] Boris Brejcha - Pillenkäfer [FCKNG SERIOUS]\n[1:13:06] Orkidea - Forward Forever [PURE PROGRESSIVE]\n[1:18:37] Gordey Tsukanov - Opacity (Solarstone Retouch) [PURE PROGRESSIVE]\n[1:26:14] Kate Bush - Running Up That Hill (Orkidea Pure Progressive Mix) [EMI]\n[1:30:42] Solarstone & RABBII - Untitled Love (Nude Mix) [BLACK HOLE]\n[1:38:27] Markus Schulz pres. Dakota - Future Shock [COLDHARBOUR]\n[1:43:25] Solarstone ft. Clare Stagg - Requiem [BLACK HOLE]\n[1:50:32] Salt Tank - Phoenix (Allende Remix EA3 Reconstruction) [PURE TRANCE]\n[1:58:42] Solarstone - Nothing But Chemistry Here [BLACK HOLE]\n[2:05:35] Robert Nickson pres. RNX - Atoms [PURE PROGRESSIVE]\n[2:09:46] Gabriel & Dresden ft. Sub Teal - White Walls [ANJUNABEATS]\n[2:14:37] Solarstone - Leap Of Faith [PURE TRANCE]\nw/ Snap! - Rhythm Is A Dancer (Acappella) [ARISTA]\n[2:19:54] Solarstone & John 00 Fleming - Hemispheres [PURE TRANCE]\nw/ Depeche Mode - Never Let Me Down Again (Acappella)\n[2:28:00] Nugen - Deliverance (Forerunners Remix) [TOUCHSTONE]\n[2:35:12] Solarstone & Gai Barone - Fata Morgana [PURE PROGRESSIVE]\n[2:42:28] Gai Barone - Shiny [PURE PROGRESSIVE]\nw/ Frankie Goes To Hollywood - Relax (Acappella)\n[2:49:06] Solarstone - Spectrum [SOLARIS]\n[2:54:37] Jam & Spoon - Odyssey To Anyoona (Airwave Remix) [COLDHARBOUR]\n[3:01:37] ID - ID\n[3:06:28] Solarstone & Orkidea - Slowmotion IV [BLACK HOLE]\n[3:13:55] ReOrder - Beyond Time [PURE TRANCE]\n[3:19:40] Röyksopp - I Had This Thing (Solarstone Remix) [DOG TRIUMPH]\n[3:26:24] David Broaders - Swelter [PURE TRANCE]\n[3:29:47] Neil Bamford - They Are There [PURE TRANCE]\n[3:36:23] Solarstone & Clare Stagg - The Spell (Solarstone Pure Mix) [BLACK HOLE]\n[3:42:30] Craig Connelly - New York Sunday [PURE TRANCE]\n[3:46:45] Salt Tank - Eugina (Ciaran McAuley Remix) [GROTESQUE REWORKED]\nw/ Salt Tank - Eugina (Salt Tank Reactivation Mix) [GROTESQUE REWORKED]\n[3:53:04] Allende - 10 Minutes To Infinity [PURE TRANCE]\n[3:58:43] Armin van Buuren ft. Josh Cumbee - Sunny Days (Pure NRG Remix) [ARMIND]\n[4:03:00] Solarstone - Shield (Part II) [BLACK HOLE]\n[4:12:58] Solarstone & Betsie Larkin - Breathe You In (Solarstone Pure Mix) [PREMIER]\n[4:18:49] Ferry Corsten & Paul Oakenfold - A Slice Of Heaven [FLASHOVER]\n[4:24:56] Solarstone - Seven Cities (Solarstone Pure Mix) [ARMADA CAPTIVATING]\n[4:32:21] Solarstone ft. Jonathan Mendelsohn - This Is Where It Starts [BLACK HOLE]\n[4:39:15] Ciaran McAuley - Maria [PURE TRANCE]\n[4:43:00] Bicep - Glue [NINJA]\n[4:46:44] Solarstone - Thank You [BLACK HOLE]\n[4:52:58] Craig Connelly ft. Jessica Lawrence - How Can I (John O'Callaghan Remix) [SUBCULTURE]\n[4:56:40] Pure NRG - Scarlett [BLACK HOLE]\n[5:01:17] a-ha - Take On Me (Robert Nickson Bootleg) [WARNER BROS.]\n[5:05:15] Lostly - Colourways [PURE TRANCE]\n[5:10:25] Scott Bond vs. Solarstone - Red Line Highway (Factor B Back To The Future Mix) (Solarstone Edit) [ARMADA]\n[5:16:29] Sied Van Riel - Atomic Blonde [PURE TRANCE]\n[5:21:43] Martin Roth's Hands On Keane - This Is The Last Time\n[5:27:16] System F ft. Armin van Buuren - Exhale (Elucidus Bootleg Remix) (Solarstone Edit) [PURE TRANCE]\n[5:31:40] Solarstone & Meredith Call - I Found You (Giuseppe Ottaviani Remix) [BLACK HOLE]\n[5:37:12] Faithless - Insomnia (Danny Eaton Rework) [SONY BMG]\n[5:42:00] Solarstone - Motif [PURE TRANCE]\n[5:48:48] Solarstone & Iko - Once (Solarstone Pure Mix) [BLACK HOLE]\n[5:55:36] Solarstone ft. Lucia Holme - The Last Defeat Pt II (Royal Sapien Remix) [SOLARIS]\n[6:02:33] Push - Universal Nation (Gai Barone Remix) [BONZAI]\nw/ Solarstone - Solarcoaster [LOST LANGUAGE]\n[6:09:43] Sasha - Xpander [DECONSTRUCTION]"


# Add ? after the first grouping to also find w/ tracks and tracks w/o cuetimes (e.g. 01. artist - title)
#  match = search(r'(?P<cuetime>w/|\[?(\d?:?\d+:\d+)\]?)? (?P<artist>.*) - (?P<title>[^\[\]]+).*$', teststring, MULTILINE)
match = findall(r'\[?(w/|\d?:?\d+:\d+)?\]? (.*) - ([^\[\]\n]+).*$', teststring, MULTILINE)
#groups = match.groups()
tracks = []
for item in match:
	# tracks.append({'cue':item[0], 'artist':item[1], 'title':item[2].strip()})
    print(item)
# for item in tracks:
#	print(item)

#import times from audacity label file
with open('labels.txt', 'r') as audacity_labels:
    cuetimes = []
    for line in audacity_labels:
        time = float(line.split()[0])
        min = str(int(time // 60)).zfill(2)
        sec = str(int(time) % 60).zfill(2)
        frm = str(int((time - int(time))*75)).zfill(2)
        cuetimes.append(f'{min}:{sec}:{frm}')

print(cuetimes)

m, s = int(1) * 60 + int(23), 43

print(f'{m}:{s}')

Paul van Dyk - Music Rescues Me Album Launch at Printworks, London (Oct 12, 2018).mp3