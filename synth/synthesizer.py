import threading
import logging
from queue import Queue
from copy import deepcopy

import numpy as np

from . import midi
from .synthesis.voice import Voice
from .synthesis.signal.chain import Chain
from .synthesis.signal.sine_wave_oscillator import SineWaveOscillator
from .synthesis.signal.square_wave_oscillator import SquareWaveOscillator
from .synthesis.signal.gain import Gain
from .synthesis.signal.mixer import Mixer
from .playback.stream_player import StreamPlayer

class Synthesizer(threading.Thread):
    def __init__(self, sample_rate: int, frames_per_chunk: int, mailbox: Queue, num_voices: int=4) -> None:
        super().__init__(name="Synthesizer Thread")
        self.log = logging.getLogger(__name__)
        self.sample_rate = sample_rate
        self.frames_per_chunk = frames_per_chunk
        self.mailbox = mailbox
        self.num_voices = num_voices

        # Set up the voices
        signal_chain_prototype = self.setup_signal_chain()
        self.log.info(f"Signal Chain Prototype:\n{str(signal_chain_prototype)}")
        self.voices = [Voice(deepcopy(signal_chain_prototype)) for _ in range(self.num_voices)]

        # Set up the stream player
        self.stream_player = StreamPlayer(self.sample_rate, self.frames_per_chunk, self.generator())

    def run(self):
        self.stream_player.play()
        should_run = True
        while should_run and self.stream_player.is_active():
            # get() is a blocking call
            if message := self.mailbox.get(): 
                match message.split():
                    case ["exit"]:
                        self.log.info("Got exit command.")
                        self.stream_player.stop()
                        should_run = False
                    case ["note_on", "-n", note, "-c", channel]:
                        int_note = int(note)
                        chan = int(channel)
                        note_name = midi.note_names[int_note]
                        if chan < self.num_voices:
                            self.note_on(int_note, chan)
                            self.log.info(f"Note on {note_name} ({int_note}), chan {chan}")
                    case ["note_off", "-n", note, "-c", channel]:
                        int_note = int(note)
                        chan = int(channel)
                        note_name = midi.note_names[int_note]
                        if chan < self.num_voices:
                            self.note_off(int_note, chan)
                            self.log.info(f"Note off {note_name} ({int_note}), chan {chan}")
                    case _:
                        self.log.info(f"Matched unknown command: {message}")
        return
        

    def setup_signal_chain(self) -> Chain:
        sine_osc = SineWaveOscillator(self.sample_rate, self.frames_per_chunk)
        sine_osc.frequency = 0.0

        square_osc = SquareWaveOscillator(self.sample_rate, self.frames_per_chunk)
        square_osc.frequency = 0.0

        sine_gain = Gain(self.sample_rate, self.frames_per_chunk, [sine_osc])
        square_gain = Gain(self.sample_rate, self.frames_per_chunk, [square_osc])

        mixer = Mixer(self.sample_rate, self.frames_per_chunk, [sine_gain, square_gain])

        signal_chain = Chain(mixer)
        return signal_chain
    
    def generator(self):
        """
        Generate the signal by mixing the voice outputs
        """
        mix = np.zeros(self.frames_per_chunk, np.float32)
        num_active_voices = 0
        while True:
            for i in range(self.num_voices):
                voice = self.voices[i]
                if voice.active:
                    mix += next(voice.signal_chain)
                    num_active_voices += 1
            
            np.clip(mix, -1.0, 1.0)
            
            yield mix
            mix = np.zeros(self.frames_per_chunk, np.float32)
            num_active_voices = 0

    def note_on(self, note: int, chan: int):
        """
        Set a voice on with the given note.
        If there are no unused voices, drop the voice that has been on for the longest and use that voice
        """
        note_id = self.get_note_id(note, chan)
        freq = midi.frequencies[note]
        for i in range(len(self.voices)):
            voice = self.voices[i]
            if not voice.active:
                voice.note_on(freq, note_id)
                self.voices.append(self.voices.pop(i)) # Move this voice to the back of the list. It should be popped last
                break

            if i == len(self.voices) - 1:
                self.log.debug(f"Had no unused voices!")
                self.voices[0].note_off()
                self.voices[0].note_on(freq, note_id)
                self.voices.append(self.voices.pop(0))


    def note_off(self, note: int, chan: int):
        """
        Find the voice playing the given note and turn it off.
        """
        note_id = self.get_note_id(note, chan)
        for i in range(len(self.voices)):
            voice = self.voices[i]
            if voice.active and voice.note_id == note_id:
                # self.log.debug(f"Setting voice {i} note_off with id {note_id}")
                voice.note_off()
    
    def get_note_id(self, note: int, chan: int):
        """
        Generate an id for a given note and channel
        By hashing the note and channel we can ensure that we are turning off the exact note
        that was turned on
        """
        note_id = hash(f"{note}{chan}")
        return note_id