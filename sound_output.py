from multiprocessing import Process, Pipe
from brian import *         # for Hz and seconds
from brian.hears import *   # for Sound class and vowel generation



class SoundManager():
    """
    class for managing process for sound playback and sound generation

    methods:
        __init__()

        get_sound():
            input:  
                freq (int), pitch of generated sound in Hz, default is 100
            outputs:
                a_sound_ramp2 (Sound), generated "a" vowel sound with given pitch
                error (bool), whether error was encountered in method

        sound_process()

        start_sound_output():
            outputs:
                parent_conn (Connection): Pipe connection end for handling the sound process
                p_process (Process): the sound playback process

        adjust_sound():
            inputs:
                centers (([int, int])): tuple that includes x- and y-coordinate of tracked face center
                options (Options): object with options as attributes

        kill_process()
    """

    def __init__(self):
        """
        initializes attributes:
            freq (int): pitch of generated sound in Hz, default is 100
            p_process (Process): the sound playback process
            playback (bool): whether sound is played back
            debug (bool): debug mode for verbose mode
        """
        print 'Initializing sound process.'
        self.freq = 100
        self.p_process = None
        self.playback = True
        self.debug = False


    def get_sound(self, freq=100):
        """
        generates "a" vowel for sound playback with given pitch frequency
        input:
            freq (int): pitch frequency of generated sound in Hz, default is 100
        output:
            a_sound_ramp2 (Sound): generated "a" vowel sound with given pitch
            error (bool): whether error was encountered in method
        """
        self.error = False
        if self.debug:
            print 'generating sound with freq:', freq
        while True:
            try:
                self.freq = float(freq)
            except ValueError:
                print 'Error: invalid value for frequency ({})!'.format(freq)
                self.error = True
                self.a_sound_ramp2 = None
                break
            self.a_sound_raw = vowel('a', pitch=freq*Hz, duration=1*second)
            self.a_sound_ramp1 = self.a_sound_raw.ramped(duration=1*second)
            self.a_sound_ramp2 = self.a_sound_ramp1.ramped(when='offset', duration=1*second)
            break

        return self.a_sound_ramp2, self.error


    def sound_process(self):
        """
        the sound process for playing back sound
        receives parameters from adjust_sound() via Pipe connection
        """
        self.sound_silence = silence(duration=0.5*second)   # the silent break between vowels
        self.error = False
        while not self.error:
            # receive frequency and options from Pipe connection end handled in adjust_sound()
            try:
                self.recv_obj = self.child_conn.recv()
            except EOFError:
                self.recv_obj = [100, None]
                # recv_obj is [freq, options]
            self.freq = self.recv_obj[0]
            self.options = self.recv_obj[1]
            if self.options:
                self.playback = self.options.playSound
            if self.debug:
                print 'passing freq:', freq
            if self.playback:
                self.sound, self.error = self.get_sound(self.freq)
                self.sound.play(sleep=False)
                self.sound_silence.play(sleep=False)
            if self.error:
                self.kill_process()


    def start_sound_output(self):
        """
        starts the sound playback process
        outputs:
            parent_conn (Connection)
        """
            #start process to generate the sound
        self.parent_conn, self.child_conn = Pipe()
        self.p_process = Process(target=self.sound_process, args=())
        self.p_process.start()
        return self.parent_conn, self.p_process


    def adjust_sound(self, centers, options):
        if len(centers) == 0:
            self.freq = 100
        else:
            self.freq = centers[0][0] + centers[0][1]
        #print 'sending freq:', freq
        self.parent_conn.send([self.freq, options])


    def kill_process(self):
        print 'Shutting down sound output.'
        self.p_process.terminate()