# MP3 Chapter Splitter

This utility reads the headers of MP3 audiobook files and splits them according to the information found in the tags. For each original file, it will create a new directory and then create a numbered sequence of files each with a section of the original file. **It requires the `ffmpeg` command line utility to split the files**

It is currently written to split files that are downloaded from the Overdrive service from our library.  These files store the chapter markers in the `UserTextFrames` MP3 header.  The markers are stored in an xml format:

```xml
<Markers>
   <Marker>
      <Name>Episode 5</Name>
      <Time>00:00.000</Time>
   </Marker>
   <Marker>
      <Name>      Episode 5 (03:42)</Name>
      <Time>03:42.227</Time>
   </Marker>
   <Marker>
      <Name>      Episode 5 (04:32)</Name>
      <Time>04:32.093</Time>
   </Marker>
   <Marker>
      <Name>      Episode 5 (05:10)</Name>
      <Time>05:10.067</Time>
   </Marker>
   <Marker>
      <Name>Episode 6</Name>
      <Time>28:04.493</Time>
   </Marker>
   <Marker>
      <Name>      Episode 6 (30:57)</Name>
      <Time>30:57.360</Time>
   </Marker>
   <Marker>
      <Name>      Episode 6 (35:41)</Name>
      <Time>35:41.547</Time>
   </Marker>
</Markers>
```



## Installing

Right now there's not a good way to install it short of cloning or downloading the repo and running it directly from there.  

Remember you need to have `ffmpeg` installed for this tool to work!  

## Usage

`splitter.py` will split all files presented on the command line.  I usually have a directory where the original MP3 files from overdrive are kept, so running it would look like:

```bash
$ ./splitter.py book/*.mp3
```

Note that this will create a directory in the current directory for each file found and split the contents of the given file into that directory.

The tool also creates a `copyit.sh` script which will copy each of the files in order to a fixed position on the file system. **NOTE:** this is currently hard-coded to copy to the position the mp3 player shows up on my machine.  Eventually I'll change it to take a parameter (pull requests welcome!).

## Status

The project is currently in the "useful tool for me" stage and has not been tested beyond seeing that it works on the files I needed splitting.  I did have a pull request to get it working on Windows.  I have **not** tested subsequent releases on windows, but I suspect they work. 

If you're interested in more features or have a file it doesn't work with, send me a note or create an issue and I'll see what I can do! I'll happily review pull requests if you've got a change you'd like.  Send me a note or create an issue if you'd like help creating a pull request. :)