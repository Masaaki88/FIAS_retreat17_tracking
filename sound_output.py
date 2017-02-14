from multiprocessing import Process, Pipe
from brian import *
from brian.hears import *

freq = 1000

def get_sound(freq):
    error = False
    while True:
        try:
            freq = float(freq)
        except ValueError:
            print 'Error: invalid value for frequency ({})!'.format(freq)
            error = True
            a_sound_ramp2 = None
            break
        a_sound_raw = vowel('a', pitch=freq*Hz, duration=1*second)
        a_sound_ramp1 = a_sound_raw.ramped(duration=1*second)
        a_sound_ramp2 = a_sound_ramp1.ramped(when='offset', duration=1*second)
        break

    return a_sound_ramp2, error


def sound_process(conn):
    sound, error = get_sound(freq)
    sound_silence = silence(duration=0.5*second)
    while not error:
        sound.play()
        sound_silence.play()
        #print 'sound'


def start_sound_output():
        #start process to generate the sound
    parent_conn, child_conn = Pipe()
    p = Process(target=sound_process, args=(child_conn,))
    p.start()
