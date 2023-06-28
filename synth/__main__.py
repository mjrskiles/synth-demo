import logging
from time import sleep
import queue
import sys

import synth.settings as settings
from synth.midi.midi_listener import MidiListener
from .synthesizer import Synthesizer


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

    listener_mailbox = queue.Queue()
    synth_mailbox = queue.Queue()

    midi_listener = MidiListener(listener_mailbox, synth_mailbox, settings.auto_attach)
    synthesizer = Synthesizer(settings.sample_rate, settings.frames_per_chunk, synth_mailbox)

    try:
        midi_listener.start()
        synthesizer.start()
        while True:
            sleep(1)
    except KeyboardInterrupt:
        log.info("Caught keyboard interrupt. Exiting the program.")

    listener_mailbox.put("exit")
    synth_mailbox.put("exit")
    midi_listener.join()
    synthesizer.join()
    sys.exit(0)