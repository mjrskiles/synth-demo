import logging
from time import sleep

import synth.settings as settings
from synth.playback.stream_player import StreamPlayer
from synth.synthesis.signal.sine_wave_oscillator import SineWaveOscillator
from synth.synthesis.signal.square_wave_oscillator import SquareWaveOscillator
from synth.synthesis.signal.gain import Gain
from synth.synthesis.signal.mixer import Mixer

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s [%(levelname)s] %(module)s [%(funcName)s]: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    
    log = logging.getLogger(__name__)
    log.info(
        """
    __
   |  |
 __|  |___             ______         __        __
/__    __/          __|______|__     |  |      |  |
   |  |            |  |      |  |    |__|______|  |
   |  |     __     |  |      |  |       |______   |
   |__|____|__|    |__|______|__|        ______|__|
      |____|          |______|          |______|

                                                           __              __                                                           
                                                          |  |            |  |
    _______         __        __     __    ____         __|  |___         |  |   ____
 __|_______|       |  |      |  |   |  |__|____|__     /__    __/         |  |__|____|__
|__|_______        |__|______|  |   |   __|    |  |       |  |            |   __|    |  |
   |_______|__        |______   |   |  |       |  |       |  |     __     |  |       |  |
 __________|__|        ______|__|   |  |       |  |       |__|____|__|    |  |       |  |
|__________|          |______|      |__|       |__|          |____|       |__|       |__|
        """
    )

    # Create a sine wave generator
    sine_wave_generator = SineWaveOscillator(settings.sample_rate, settings.frames_per_chunk)
    sine_wave_generator.frequency = 440.0

    square_osc = SquareWaveOscillator(settings.sample_rate, settings.frames_per_chunk)
    square_osc.frequency = 440.0

    sine_gain = Gain(settings.sample_rate, settings.frames_per_chunk, [sine_wave_generator])
    square_gain = Gain(settings.sample_rate, settings.frames_per_chunk, [square_osc])

    mixer = Mixer(settings.sample_rate, settings.frames_per_chunk, [sine_gain, square_gain])

    # Create a stream player
    stream_player = StreamPlayer(sample_rate=settings.sample_rate, frames_per_chunk=settings.frames_per_chunk, input_delegate=mixer)

    try:
        stream_player.play()
        while True:
            sleep(1)
    except KeyboardInterrupt:
        log.info("Caught keyboard interrupt. Exiting the program.")