from multiprocessing import Process, Pipe
from brian import *
from brian.hears import *



class SoundManager():
    def __init__(self):
        print 'Initializing sound process.'
        self.freq = 100
        self.p_process = None
        self.playback = True

    def get_sound(self, freq=100):
        self.error = False
        #print 'generating sound with freq:', freq
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
        self.sound_silence = silence(duration=0.5*second)
        self.error = False
        while self.playback and not self.error:
            try:
                self.recv_obj = self.child_conn.recv()
                #print  'received freq_list:', freq_list
            except EOFError:
                self.recv_obj = [100]
                #print 'No frequency received'
            self.freq = self.recv_obj[0]
            #print 'passing freq:', freq
            self.sound, self.error = self.get_sound(self.freq)
            self.sound.play(sleep=False)
            self.sound_silence.play(sleep=False)
            #print 'sound'


    def start_sound_output(self):
            #start process to generate the sound
        self.parent_conn, self.child_conn = Pipe()
        self.p_process = Process(target=self.sound_process, args=())
        self.p_process.start()
        return self.parent_conn, self.p_process


    def adjust_sound(self, centers):
        if len(centers) == 0:
            self.freq = 100
        else:
            self.freq = centers[0][0] + centers[0][1]
        #print 'sending freq:', freq
        self.parent_conn.send([self.freq])


    def kill_process(self):
        print 'Shutting down sound output.'
        self.p_process.terminate()


    def turn_off_playback(self):
        print 'Turning off sound playback.'
        self.playback = False


    def turn_on_playback(self):
        print 'Turning on sound playback.' 
        self.playback = True