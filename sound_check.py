from brian import *
from brian.hears import *

a_sound = vowel('a', duration=1*second)
sound = a_sound.ramped(duration=1*second).ramped(when='offset', duration=1*second)
sound.play()
raw_input('Press Enter to exit')