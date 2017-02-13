#
# Copyright (C) 2008 Cournapeau David <cournape@gmail.com>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in
#        the documentation and/or other materials provided with the
#        distribution.
#      * Neither the author nor the names of any contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
#  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


#
#  Note that this is not the original file (you can find the original file in scikits.audiolab).
#  This file was modified by Frank Stollmeier such that the play method produces a continuous sound. 
#  The sound changes or stops only if it recieves a signal via a connection (a multiprocessing.Pipe) from its parent.
#


import numpy as np
cimport numpy as cnp
import scipy.signal
cimport stdlib
cimport python_exc
from alsa cimport *

cdef int BUFFER_TIME  = 4*1024#500000
cdef int PERIOD_TIME  = 0

cdef extern from "alsa/asoundlib.h":
        # This is needed here because it is a macro and is not recognized by
        # gccxml it seems
        int snd_pcm_hw_params_alloca(snd_pcm_hw_params_t **)
        int snd_pcm_sw_params_alloca(snd_pcm_sw_params_t **)

cdef extern from "Python.h":
        object PyString_FromStringAndSize(char *v, int len)

class AlsaException(Exception):
        pass

def alsa_version():
        """Return the version of libasound used by the alsa backend."""
        return snd_asoundlib_version()

def enumerate_devices():
        """Return list of found devices (includes user-space ones)."""
        cdef int st, card
        cdef char** hints
        cdef char* name

        devices = []
        names = []

        card = -1
        st = snd_device_name_hint(card, "pcm", <void***>&hints)
        card = 0
        while(hints[card] != NULL):
                #name = snd_device_name_get_hint(hints[card], "NAME")
                #names.append(PyString_FromStringAndSize(name, stdlib.strlen(name)))
                #if name != NULL:
                #        stdlib.free(name)
                devices.append(PyString_FromStringAndSize(hints[card], 
                        stdlib.strlen(hints[card])))
                card += 1
        snd_device_name_free_hint(<void**>hints)

        return devices

cdef struct format_info:
        # number of channels
        int nchannels
        # Rate (samples/s -> Hz)
        int rate
        # Bits per sample
        int nbits
        # Byte format
        int byte_fmt

cdef class AlsaDevice:
        cdef snd_pcm_t *handle
        cdef format_info format
        def __init__(AlsaDevice self, unsigned int fs=48000, int nchannels=1):
                cdef int st
                cdef snd_pcm_uframes_t psize, bsize

                self.format.rate = fs
                self.format.nchannels = nchannels

                if not (nchannels > 0 and nchannels < 3):
                        raise ValueError,\
                              "Only mono/stereo signals supported for now"

                self.handle = <snd_pcm_t*>0
                st = snd_pcm_open(&self.handle, "default", SND_PCM_STREAM_PLAYBACK, 0)
                if st < 0:
                        raise AlsaException("Fail opening 'default'")

                set_hw_params(self.handle, self.format, &psize, &bsize)
                print "Period size is", psize, ", Buffer size is", bsize

                set_sw_params(self.handle, psize, bsize)

        cdef cnp.ndarray[cnp.float, ndim=1] sound_generator(AlsaDevice self, cnp.ndarray spectrum, cnp.ndarray time_sample):
                output = np.zeros(len(time_sample))
                for i in xrange(spectrum.shape[1]):
                    output = output + spectrum[1,i]*np.sin(spectrum[0,i]*time_sample)
                #output = np.sin(time_sample)
                return output / np.max(output)
        def play(AlsaDevice self, cnp.ndarray spectrum, conn):
                self._play(spectrum, conn)
        cdef int _play(AlsaDevice self, cnp.ndarray spectrum, conn) except -1:
                cdef cnp.ndarray[cnp.int16_t, ndim=2] tx
                cdef int nr, i, nc
                cdef int bufsize = 1024
                cdef int err = 0
                
                
                input = np.zeros(bufsize)
                input = input[np.newaxis, :]
                if not input.ndim == 2:
                        raise ValueError("Only rank 2 for now")

                nc = input.shape[0]
                if not nc == self.format.nchannels:
                        raise ValueError(
                              "AlsaDevice configured for %d channels, "\
                              "signal has %d channels" % (self.format.nchannels, nc))

                tx = np.empty((nc, bufsize), dtype=np.int16)
                nr = input.size / nc / bufsize

                st = snd_pcm_prepare(self.handle)
                if st:
                        raise AlsaException("Error while preparing the pcm device")

                # We make sure the buffer is in fortran order to deal
                # with interleaved data.
                i = 0
                cdef double time_marker = 0
                cdef double frequency = 440
                cdef double frequency_new = 440
                cdef double echo = 0
                cdef double amplitude = 0.1
                sequence = np.zeros(3*bufsize)
                times = np.arange(bufsize)
                tx = np.asfortranarray(32568 * input[:, i * bufsize:i * bufsize + bufsize],np.int16)
                        
                while True:
                        err = python_exc.PyErr_CheckSignals()
                        if err != 0:
                                break
                        if conn.poll(): #check if there is something in the pipe and so process it
                            signal, value = conn.recv()
                            if signal == 'frequency, amplitude':
                                frequency_new, amplitude = value
                            elif signal == 'echo':
                                echo = value
                            elif signal == 'spectrum':
                                spectrum = value
                            elif signal == 'stop':
                                snd_pcm_drain(self.handle)
                                print "soundio: stop signal recieved"
                                return 0
                        if frequency_new == frequency: #constant frequency -> equidistant time points
                            t = time_marker + times * 2*np.pi*frequency/float(self.format.rate)
                        else: #transition to new frequency -> variable-distanced time points
                            m1 = 2*np.pi*frequency/float(self.format.rate)
                            m2 = 2*np.pi*frequency_new/float(self.format.rate)
                            t = time_marker + m1*times + 0.5*times*times*(m2-m1)/float(bufsize)
                            frequency = frequency_new
                        time_marker = t[-1]
                        #generate chunk
                        new_chunk = amplitude*self.sound_generator(spectrum, t)
                        
                        #add echo
                        #Schroeder’s Reverberator, see https://christianfloisand.wordpress.com/2012/09/04/digital-reverberation/
                        #1027=43.7 ms
                        #1823=41.1 ms
                        #1636=37.1 ms
                        #1310=29.7 ms
                        #g = 0.001 ** (tau/RVT) with RVT ~= 1.0
                        #sequence[bufsize:] = sequence[:2*bufsize]
                        #sequence[:bufsize] = new_chunk
                        #RVT = 1.0
                        #g1 = 0.001 ** (0.0437/RVT)
                        #g2 = 0.001 ** (0.0411/RVT)
                        #g3 = 0.001 ** (0.0371/RVT)
                        #g4 = 0.001 ** (0.0297/RVT) 
                        #sequence[:bufsize] = sequence[:bufsize] + 0.25 * (g1*sequence[1027:bufsize+1027])# + g2*sequence[1823:bufsize+1823] + g3*sequence[1636:bufsize+1636] + g1*sequence[1310:bufsize+1310])
                        #input[0,:] = sequence[:bufsize]
                        
                        #simple echo
                        input[0,:] = echo*input[0,:] + (1-echo)*new_chunk
                        
                        #write data
                        tx = np.asfortranarray(32568 * input[:, i * bufsize:i * bufsize + bufsize],np.int16)
                        st = snd_pcm_writei(self.handle, <void*>tx.data, bufsize)
                        if st < 0:
                            print "Buffer underrun"
                            snd_pcm_prepare(self.handle)
                            #raise AlsaException("Error in writei")

                if err:
                        print "Got SIGINT: draining the pcm device... "
                        snd_pcm_drain(self.handle)
                        return -1
                snd_pcm_drain(self.handle)
                return 0

        def __dealloc__(AlsaDevice self):
                if self.handle:
                        snd_pcm_close(self.handle)

cdef set_hw_params(snd_pcm_t *hdl, format_info info, snd_pcm_uframes_t* period_size, snd_pcm_uframes_t *buffer_size):
        cdef unsigned int nchannels, buftime, pertime, samplerate
        cdef snd_pcm_hw_params_t *params
        cdef int st, dir
        cdef snd_pcm_access_t access
        cdef snd_pcm_format_t format

        access = SND_PCM_ACCESS_RW_INTERLEAVED
        buftime = BUFFER_TIME
        pertime = PERIOD_TIME

        nchannels = info.nchannels
        samplerate = info.rate
        format = SND_PCM_FORMAT_S16_LE

        snd_pcm_hw_params_alloca(&params)
        st = snd_pcm_hw_params_any(hdl, params)
        if st < 0:
                raise AlsaException("Error in _any")

        # Restrict sampling rates to the ones supported by the hardware 
        st = snd_pcm_hw_params_set_rate_resample(hdl, params, 1)
        if st < 0:
                raise AlsaException("Error in _set_rate_resample")

        st = snd_pcm_hw_params_set_access(hdl, params, access)
        if st < 0:
                raise AlsaException("Error in _set_access")

        st = snd_pcm_hw_params_set_format(hdl, params, format)
        if st < 0:
                raise AlsaException("Error in _set_format")

        st = snd_pcm_hw_params_set_channels(hdl, params, nchannels)
        if st < 0:
                raise AlsaException("Error in _set_channels")

        dir = 0
        st = snd_pcm_hw_params_set_rate_near(hdl, params, &samplerate, &dir)
        if st < 0:
                raise AlsaException("Error in _set_rate_near")

        dir = 0
        st = snd_pcm_hw_params_set_buffer_time_near(hdl, params, &buftime, &dir)
        if st < 0:
                raise AlsaException("Error in _set_buffer_near")

        dir = 0
        st = snd_pcm_hw_params_set_period_time_near(hdl, params, &pertime, &dir)
        if st < 0:
                raise AlsaException("Error in _set_period_time_near")

        st = snd_pcm_hw_params(hdl, params)
        if st < 0:
                raise AlsaException("Error in applying hw params")

        dir = 0
        st = snd_pcm_hw_params_get_period_size(params, period_size, &dir)
        if st < 0:
                raise AlsaException("Error in get_period_sizse")

        st = snd_pcm_hw_params_get_buffer_size(params, buffer_size)
        if st < 0:
                raise AlsaException("Error in get_buffer_sizse")

cdef set_sw_params(snd_pcm_t *hdl, unsigned int period_size, unsigned int buffer_size):
        cdef snd_pcm_sw_params_t *params

        snd_pcm_sw_params_alloca(&params)

        st = snd_pcm_sw_params_current(hdl, params)
        if st < 0:
                raise AlsaException("Error in _current")

        st = snd_pcm_sw_params_set_start_threshold(hdl, params, period_size)
        if st < 0:
                raise AlsaException("Error in _set_start_threshold")

        st = snd_pcm_sw_params_set_avail_min(hdl, params, period_size)
        if st < 0:
                raise AlsaException("Error in _set_avail_min")

        st = snd_pcm_sw_params(hdl, params)
        if st < 0:
                raise AlsaException("Error in applying sw params")
