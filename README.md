# quickCUE

quickCUE creates compliant CUE files directly from [1001tracklists](https://www.1001tracklists.com) pages or user inputted track lists.

## Getting Started

1. Select audio file to automatically fill Artist, Title, Year, Genre, and Filename fields used in the CUE header. *(optional)*
2. Import a label file (a file with a list of cue times) exported from <a href="https://www.audacityteam.org/" title="Audacity" target="_blank">Audacity</a>. *(optional)*
3. Paste either a link to a 1001tracklists page or your own tracklist following formatting rules (see [Formatting Help](#formatting-help)).
3. Select quickCUE to immediately make the CUE without verifying imported information. Otherwise, select Verify CUE.
4. Manually adjust individual cues and track information. You can also adjust all cues earlier or later by a fixed amount.
5. Confirm and save.

### Prerequisites

No prerequisites for quickCUE itself.

If you wish to import label files, you'll need to use <a href="https://www.audacityteam.org/" title="Audacity" target="_blank">Audacity</a>.

### Installing

This is a single EXE file, so no installation required.

### Formatting Help

Tracks can be formatted in any of the following ways. Note that any non-alphanumeric character is a literal. (e.g. [text] means text surrounded by [ and ].

Note: "other_text" is discarded by quickCUE as this usually is release label information or track numbers without cue times.
```
[h:mm:ss] artist - title [other_text] 
[h:mm:ss] artist - title 

h:mm:ss artist - title [other_text]
h:mm:ss artist - title

[mmm:ss] artist - title [other_text] 
[mmm:ss] artist - title

mmm:ss artist - title [other_text] 
mmm:ss artist - title

w/ artist - title [other_text] 
w/ artist - title

other_text artist - title
```

## Credit

<div>Icon made by <a href="https://www.flaticon.com/authors/kiranshastry" title="Kiranshastry" target="_blank">Kiranshastry</a> from <a href="https://www.flaticon.com/" title="Flaticon" target="_blank">www.flaticon.com</a> is licensed by <a href="http://creativecommons.org/licenses/by/3.0/" title="Creative Commons BY 3.0" target="_blank">CC 3.0 BY</a></div>

## Contributing

I'll be honest - I'm a noob programmer. I still don't understand how pull requests and such work, so please bear with me if you want to contribute.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Acknowledgments
* Thanks to **you** for using this and hopefully finding it useful!
* Thanks to all the Stack Overflow posts whose code was used or inspired my own code
* Thanks to Reddit's <a href="http://www.reddit/com/r/trance/" title="r/trance" target="_blank">r/trance</a> for initial input and being an awesome community.

