from multiprocessing import Process, Pipe
from brian import *
from brian.hears import *

#freq = 100
parent_conn = None

def get_sound(freq=100):
    error = False
    print 'generating sound with freq:', freq
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
    sound_silence = silence(duration=0.5*second)
    error = False
    while not error:
        try:
            freq_list = conn.recv()
            print  'received freq_list:', freq_list
        except EOFError:
            freq_list = [100]
            print 'EOFError!'
        freq = freq_list[0]
        print 'passing freq:', freq
        sound, error = get_sound(freq)
        sound.play(sleep=True)
        sound_silence.play(sleep=True)
        #print 'sound'


def start_sound_output():
    global parent_conn
        #start process to generate the sound
    parent_conn, child_conn = Pipe()
    p = Process(target=sound_process, args=(child_conn,))
    p.start()


def adjust_sound(centers):
    if len(centers) == 0:
        freq = 100
    else:
        freq = 5*(centers[0][0] + centers[0][1])
    #print 'sending freq:', freq
    parent_conn.send([freq])
