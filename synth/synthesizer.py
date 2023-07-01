import threading
import logging
from queue import Queue
from copy import deepcopy

import numpy as np

from . import midi
from .midi.implementation import Implementation
from .synthesis.voice import Voice
from .synthesis.signal.chain import Chain
from .synthesis.signal.sine_wave_oscillator import SineWaveOscillator
from .synthesis.signal.square_wave_oscillator import SquareWaveOscillator
from .synthesis.signal.sawtooth_wave_oscillator import SawtoothWaveOscillator
from .synthesis.signal.triangle_wave_oscillator import TriangleWaveOscillator
from .synthesis.signal.gain import Gain
from .synthesis.signal.mixer import Mixer
from .synthesis.signal.low_pass_filter import LowPassFilter
from .playback.stream_player import StreamPlayer

class Synthesizer(threading.Thread):
    def __init__(self, sample_rate: int, frames_per_chunk: int, mailbox: Queue, num_voices: int=4) -> None:
        super().__init__(name="Synthesizer Thread")
        self.log = logging.getLogger(__name__)
        self.sample_rate = sample_rate
        self.frames_per_chunk = frames_per_chunk
        self.mailbox = mailbox
        self.num_voices = num_voices
        self.should_run = True

        # Set up the voices
        signal_chain_prototype = self.setup_signal_chain()
        self.log.info(f"Signal Chain Prototype:\n{str(signal_chain_prototype)}")
        self.voices = [Voice(deepcopy(signal_chain_prototype)) for _ in range(self.num_voices)]

        # Set up the stream player
        self.stream_player = StreamPlayer(self.sample_rate, self.frames_per_chunk, self.generator())

        # Set up the lookup values
        self.osc_mix_vals = np.linspace(0, 1, 128, endpoint=True, dtype=np.float32)
        self.lpf_cutoff_vals = np.logspace(4, 14, 128, endpoint=True, base=2, dtype=np.float32) # 2^14=16384 : that is the highest possible cutoff value

    def run(self):
        self.stream_player.play()
        while self.should_run and self.stream_player.is_active():
            # get() is a blocking call
            if message := self.mailbox.get(): 
                self.message_handler(message)
        return
    
    def message_handler(self, message: str):
        match message.split():
            case ["exit"]:
                self.log.info("Got exit command.")
                self.stream_player.stop()
                self.should_run = False
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
            case ["control_change", "-c", channel, "-n", cc_num, "-v", control_val]:
                chan = int(channel)
                int_cc_num = int(cc_num)
                int_cc_val = int(control_val)
                self.control_change_handler(chan, int_cc_num, int_cc_val)
            case _:
                self.log.info(f"Matched unknown command: {message}")
        

    def setup_signal_chain(self) -> Chain:
        osc_a = SawtoothWaveOscillator(self.sample_rate, self.frames_per_chunk)
        osc_b = SquareWaveOscillator(self.sample_rate, self.frames_per_chunk)

        gain_a = Gain(self.sample_rate, self.frames_per_chunk, [osc_a], control_tag="gain_a")
        gain_b = Gain(self.sample_rate, self.frames_per_chunk, [osc_b], control_tag="gain_b")

        mixer = Mixer(self.sample_rate, self.frames_per_chunk, [gain_a, gain_b])

        lpf = LowPassFilter(self.sample_rate, self.frames_per_chunk, [mixer], control_tag="lpf")

        signal_chain = Chain(lpf)
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
            
            mix = np.clip(mix, -1.0, 1.0)
            
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
    
    def control_change_handler(self, channel: int, cc_number: int, val: int):
        self.log.info(f"Control Change: channel {channel}, number {cc_number}, value {val}")
        if cc_number == Implementation.OSCILLATOR_MIX.value:
            gain_b_mix_val = self.osc_mix_vals[val]
            gain_a_mix_val = 1 - gain_b_mix_val
            self.set_gain_a(gain_a_mix_val)
            self.set_gain_b(gain_b_mix_val)
            self.log.info(f"Gain A: {gain_a_mix_val}")
            self.log.info(f"Gain B: {gain_b_mix_val}")
        if cc_number == Implementation.LPF_CUTOFF.value:
            lpf_cutoff = self.lpf_cutoff_vals[val]
            self.set_lpf_cutoff(lpf_cutoff)
            self.log.info(f"LPF Cutoff: {lpf_cutoff}")

    def set_gain_a(self, gain):
        for voice in self.voices:
            gain_a_components = voice.signal_chain.get_components_by_control_tag("gain_a")
            for gain_a in gain_a_components:
                gain_a.amp = gain

    def set_gain_b(self, gain):
        for voice in self.voices:
            gain_b_components = voice.signal_chain.get_components_by_control_tag("gain_b")
            for gain_b in gain_b_components:
                gain_b.amp = gain

    def set_lpf_cutoff(self, cutoff):
        for voice in self.voices:
            lpf_components = voice.signal_chain.get_components_by_control_tag("lpf")
            for lpf in lpf_components:
                lpf.cutoff_frequency = cutoff