import matplotlib.pyplot as plt
import numpy as np

from synth.synthesis.signal.sine_wave_oscillator import SineWaveOscillator
from synth.synthesis.signal.square_wave_oscillator import SquareWaveOscillator
from synth.synthesis.signal.sawtooth_wave_oscillator import SawtoothWaveOscillator
from synth.synthesis.signal.triangle_wave_oscillator import TriangleWaveOscillator
from synth.synthesis.signal.mixer import Mixer

# create a signal chain
osc_a = SquareWaveOscillator(sample_rate=44100, frames_per_chunk=1024)
osc_b = SawtoothWaveOscillator(sample_rate=44100, frames_per_chunk=1024)
mixer = Mixer(sample_rate=44100, frames_per_chunk=1024, subcomponents=[osc_a, osc_b])

# set its properties
osc_a.frequency = 110.0
osc_a.amplitude = 1.0

osc_b.frequency = 110.0 
osc_b.amplitude = 1.0

# generate a second of audio
signal_iter = iter(mixer)
samples = next(signal_iter)

# plot the first 1000 samples (~23ms)
plt.plot(samples[:1000])
plt.xlabel("Sample number")
plt.ylabel("Amplitude")
plt.title("Square/Sawtooth mix at 110Hz")
plt.grid(True)
plt.show()
