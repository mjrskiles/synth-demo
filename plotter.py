import matplotlib.pyplot as plt
import numpy as np

from synth.synthesis.signal.sine_wave_oscillator import SineWaveOscillator
from synth.synthesis.signal.square_wave_oscillator import SquareWaveOscillator
from synth.synthesis.signal.sawtooth_wave_oscillator import SawtoothWaveOscillator
from synth.synthesis.signal.triangle_wave_oscillator import TriangleWaveOscillator
from synth.synthesis.signal.low_pass_filter import LowPassFilter
from synth.synthesis.signal.mixer import Mixer

# create a signal chain
osc_a = SquareWaveOscillator(sample_rate=44100, frames_per_chunk=2048)
osc_b = SawtoothWaveOscillator(sample_rate=44100, frames_per_chunk=2048)
mixer = Mixer(sample_rate=44100, frames_per_chunk=2048, subcomponents=[osc_a, osc_b])
lpf = LowPassFilter(sample_rate=44100, frames_per_chunk=2048, subcomponents=[mixer])


# set its properties
osc_a.frequency = 110.0
osc_a.amplitude = 1.0

osc_b.frequency = 110.0 
osc_b.amplitude = 1.0

lpf.cutoff_frequency = 400.0

# generate audio
signal_iter = iter(lpf)
samples = next(signal_iter)

# plot 1000 samples
plt.plot(samples[200:1200])
plt.xlabel("Sample number")
plt.ylabel("Amplitude")
plt.title("Square/Sawtooth low-pass filtered at 110Hz (cutoff 400Hz)")
plt.grid(True)
plt.show()
