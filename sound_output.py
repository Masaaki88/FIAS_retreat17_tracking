from multiprocessing import Process, Pipe
from brian import *
from brian.hears import *

#freq = 100
parent_conn = None
p_process = None

def get_sound(freq=100):
    error = False
    #print 'generating sound with freq:', freq
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
    global p_process
    sound_silence = silence(duration=0.5*second)
    error = False
    while not error:
        try:
            recv_obj = conn.recv()
            #print  'received freq_list:', freq_list
        except EOFError:
            recv_obj = [100]
            #print 'No frequency received'
        if recv_obj == ['kill']:
            p_process.terminate()
        else:
            freq = recv_obj[0]
        #print 'passing freq:', freq
        sound, error = get_sound(freq)
        sound.play(sleep=False)
        sound_silence.play(sleep=False)
        #print 'sound'


def start_sound_output():
    global parent_conn, p_process
        #start process to generate the sound
    parent_conn, child_conn = Pipe()
    p_process = Process(target=sound_process, args=(child_conn,))
    p_process.start()
    return parent_conn


def adjust_sound(centers):
    if len(centers) == 0:
        freq = 100
    else:
        freq = centers[0][0] + centers[0][1]
    #print 'sending freq:', freq
    parent_conn.send([freq])
