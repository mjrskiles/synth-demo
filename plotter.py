import matplotlib.pyplot as plt
import numpy as np

from synth.synthesis.signal.sine_wave_oscillator import SineWaveOscillator
from synth.synthesis.signal.square_wave_oscillator import SquareWaveOscillator
from synth.synthesis.signal.mixer import Mixer

# create a signal chain
square_osc = SquareWaveOscillator(sample_rate=44100, frames_per_chunk=1024)
sine_osc = SineWaveOscillator(sample_rate=44100, frames_per_chunk=1024)
mixer = Mixer(sample_rate=44100, frames_per_chunk=1024, subcomponents=[sine_osc, square_osc])

# set its properties
square_osc.frequency = 110.0  # A4 note
square_osc.amplitude = 0.5

sine_osc.frequency = 110.0  # A4 note
sine_osc.amplitude = 0.5
# sine_osc.set_phase_degrees(90)

# generate a second of audio
signal_iter = iter(mixer)
samples = next(signal_iter)

# plot the first 1000 samples (~23ms)
plt.plot(samples[:1000])
plt.xlabel("Sample number")
plt.ylabel("Amplitude")
plt.title("Sine/Square mix at 110Hz")
plt.grid(True)
plt.show()
