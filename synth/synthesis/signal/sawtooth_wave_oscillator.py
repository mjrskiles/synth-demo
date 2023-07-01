import logging

import numpy as np

from .oscillator import Oscillator

class SawtoothWaveOscillator(Oscillator):
    def __init__(self, sample_rate: int, frames_per_chunk: int, name: str="SawtoothWaveOscillator"):
        super().__init__(sample_rate, frames_per_chunk, name=name)
        self.log = logging.getLogger(__name__)

    def __iter__(self):
        self._chunk_duration = self.frames_per_chunk / self.sample_rate
        self._chunk_start_time = 0.0
        self._chunk_end_time = self._chunk_duration
        return self
    
    def __next__(self):
        # Generate the sample
        if self.frequency <= 0.0:
            if self.frequency < 0.0:
                self.log.error("Overriding negative frequency to 0")
            sample = np.zeros(self.frames_per_chunk)
        
        else:
            # calculate the period
            period = 1.0 / self.frequency
            ts = np.linspace(self._chunk_start_time, self._chunk_end_time, self.frames_per_chunk, endpoint=False)
            sample = self.amplitude * (2 * (ts / period - np.floor(0.5 + ts / period)))

        # Update the state variables for next time
        self._chunk_start_time = self._chunk_end_time
        self._chunk_end_time += self._chunk_duration

        return sample.astype(np.float32)
    
    def __deepcopy__(self, memo):
        return SawtoothWaveOscillator(self.sample_rate, self.frames_per_chunk, name="SawtoothWaveOscillator")
