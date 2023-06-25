import logging

import numpy as np

from .sine_wave_oscillator import SineWaveOscillator

class SquareWaveOscillator(SineWaveOscillator):
    def __init__(self, sample_rate, frames_per_chunk):
        super().__init__(sample_rate, frames_per_chunk)
        self.log = logging.getLogger(__name__)

    def __next__(self):
        """
        This oscillator works by first generating a sine wave, then setting every frame
        to either -1 or 1, depending on the sign of the wave y value at that point.
        This has the effect of filtering it into a square wave
        """
        sine_wave = super().__next__()
        square_wave = np.sign(sine_wave)
        return square_wave
    
    def __deepcopy__(self, memo):
        return SquareWaveOscillator(self.sample_rate, self.frames_per_chunk)