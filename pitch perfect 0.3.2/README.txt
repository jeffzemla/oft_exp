pitch perfect v0.3.2
written by Sean McKean

Description:
    This program is meant to demonstrate how to generate audio tones
    with or without pre-loading them as .wav files. As of v0.3.0 I have
    added the ability to load small .wav samples as instruments and,
    with some fine-tuning, play them in the same pitch ranges as are
    available for the original tones.
    I was thinking about including something similar to this method in
    an upcoming game, to make the control a little more interesting. But
    I do not have a date set on it yet, and I still have some bugs to
    work out.


The Windows binary version can be run without external dependencies;
simply run 'pitch perfect.exe' in the main directory to start the program.

The source version requires the Python interpreter and a couple of libraries
installed:

    Python >= v2.6.6, < v3.0  (http://www.python.org/)
    Pygame >= v1.9.1          (http://www.pygame.org/)
    numpy  >= v1.3.0          (http://numpy.scipy.org/)

To run the program from source, simply call "python main.py" from
the command-line, or "./main.py" if you are on a Unix and have
appropriate permissions set.


Controls:

    There are some command-line options that can be set, in case you do
    not want to make changes to the program source. Add a "-h" option to
    the program invocation to see a list of the options available.

    This program is mainly mouse-driven, but includes or duplicates some
    keyboard commands as well. To quit, press Escape key or close the
    window. After the program starts, the screen displays a disk with
    lines, and some note names around the perimeter. To select a note,
    left-click the mouse on one of the lines on the disk. To alter the
    volume, click or drag the mouse closer to the center (quieter), or
    closer to the edge (louder). Dragging the mouse through the disk
    with the left button pressed alters the sound in real time, while
    letting go silences the tone. To select a different type of tone for
    playback, click on one of the four buttons displayed in the
    upper-right corner of the window, or press a number key (1-4).
    The fourth waveform cycles through sample-based tones.

    Chording commands:
        Control keys:   Create a persistent note in current voice and octave.
        Shift keys:     Select a note to alter with left mouse button.
        'c' key:        Cancel selection.
        'x' key:        Delete selected note.
        's' key:        Silence all notes on screen.

    Other commands:
        Right mouse button:             Toggle between-note or on-note modes.
        Middle button scroll:           Alter current octave by a third in
                                        either direction.
        Left and right arrow keys:      (same as above)
        Middle button down and scroll:  Raise or lower current octave by
                                        a full count.
        Up and down arrow keys:         (same as above)
        Middle mouse button, no scroll: Reset current octave, keeping
                                        the current third.
        Space key:                      (same as above)
        'd' key:                        Show some debugging information.


Tone-generating and pitch-shifting functions:

    To create a dynamic pygame.mixer.Sound object with optional
    parameters (see below), take a look at the GenerateTone function in
    the file generate.py; pygame.mixer must be initialized before
    calling the function. A second function, GeneratePitchedSample, is
    defined for the purpose of adjusting the pitch and volume of an
    array of sample information.

    Note: If you have tried running pitch perfect as of v0.2, you
          might notice a change in the argument order to GenerateTone.

    For instance:

        import pygame
        from generate import GenerateTone, GeneratePitchedSample
        ...

        pygame.mixer.init()
        # Creates a 440 Hz A tone sine wave at full volume.
        sound_a = GenerateTone()
        sound_a.play(-1)  # Plays a 440 Hz sine wave at full volume
        sound_b = GenerateTone(shape='square', freq='D#', vol=0.1)
        sound_b.play(-1)
        ...

        # array is a numpy.ndarray object obtained from sample data
        # already loaded (take a look at documentation for function
        # pygame.sndarray.array).

        # 'base' is the relative base note that the sample is tuned to;
        # 'freq' is the actual note or frequency that the sample will be
        #   pitched to;
        # 'vol' is the volume, with 1.0 being the original sample volume,
        #   and 0.0 being silent.
        sound_c = GeneratePitchedSample(array, base='C4', freq='G5', vol=0.2)
        sound_c.play(-1)
        ...


Changelog:

    v0.3.2 (2010-11-15): Fixed various bugs; program seems to run
                         through stress tests okay without exiting
                         prematurely.

    v0.3.1 (2010-11-13): Added an option to lengthen loaded samples for
                         increased resolution at differing pitches.

    v0.3.0b (2010-11-12): Added pitched-sample support and various fixes;
                          GenerateTone function has reordered arguments.

    v0.2.1b (2010-11-07): Set default to 8-bit sound on Windows 64-bit
                          platform.

    v0.2b (2010-11-07): Added note chording and abstracted the tone
                        generation function to a separate module.

    v0.1b (2010-11-05): Initial release.


Credits:

    Due credit goes to David Cole for suggesting the ability to add and
    alter chords, and also for suggesting more voices, and to Jug for
    the idea of separating the tone generator function for further use.
    I have tried to add comments to help in making sense of the code,
    which has been suggested more that once, but it takes some getting
    used to :)

    The samples were obtained online through http://www.findsounds.com/
    and processed through Audacity (http://audacity.sourceforge.net/).


Please let me know what you think of this program, or if you have
encountered a bug or have a fix. All feedback is welcome.

Email: <smckean83 AT gmail DOT com>
