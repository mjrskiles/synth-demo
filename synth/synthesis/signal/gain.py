import logging
from copy import deepcopy
from typing import List

import numpy as np

from .component import Component

class Gain(Component):
    """
    The gain component multiplies the amplitude of the signal by a constant factor.
    """
    def __init__(self, sample_rate, frames_per_chunk, subcomponents: List['Component'] = [], name="Gain"):
        super().__init__(sample_rate, frames_per_chunk, subcomponents, name)
        self.log = logging.getLogger(__name__)
        self.amp = 0.1

    def __iter__(self):
        self.subcomponent_iter = iter(self.subcomponents[0]) # Gain should only have 1 subcomponent
        return self
    
    def __next__(self):
        chunk = next(self.subcomponent_iter)
        return chunk * self.amp
    
    def __deepcopy__(self, memo):
        return Gain(self.sample_rate, self.frames_per_chunk, subcomponents=[deepcopy(self.subcomponents[0], memo)], name=self.name)
    
    @property
    def amp(self):
        return self._amp
    
    @amp.setter
    def amp(self, value):
        try:
            float_val = float(value)
            if float_val > 1.0 or float_val < 0.0:
                raise ValueError
            self._amp = float_val
        except ValueError:
            self.log.error(f"Gain must be between 0.0 and 1.0, got {value}")