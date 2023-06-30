import logging

from . import frequencies

def builder():
    return CommandBuilder()

class MessageBuilder():
    """
    Class for constructing messages to send to the controller.
    Anyone trying to talk to the controller should construct the message with this class.
    """ 

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)
        self._message = ""

    @property
    def message(self):
        return self._message
    
    def build(self) -> str:
        return str(self._message).strip()
    
class CommandBuilder(MessageBuilder):
    def __init__(self) -> None:
        super().__init__()

    def note_on(self):
        self._message += " note_on"
        return NoteParameterBuilder(self.message)
    
    def note_off(self):
        self._message += " note_off"
        return NoteParameterBuilder(self.message)
    
    def control_change(self):
        self._message += " control_change"
        return CCParameterBuilder(self.message)

        
class NoteParameterBuilder(MessageBuilder):
    def __init__(self, message_base: str) -> None:
        super().__init__()
        self._message = message_base
    
    def with_note(self, note):
        try:
            int_val = int(note)
            if int_val < 0 or int_val > 127:
                raise ValueError
            self._message += f" -n {int_val}"
        except ValueError:
            self.log.error(f"Unable to set note: {note}")
            raise

        return NoteParameterBuilder(self._message)
    
    def on_channel(self, channel):
        try:
            int_val = int(channel)
            if int_val < 0 or int_val > 15:
                raise ValueError
            self._message += f" -c {int_val}"
        except ValueError:
            self.log.error(f"Unable to set channel: {channel}")
            raise
        
        return NoteParameterBuilder(self._message)

class CCParameterBuilder(MessageBuilder):
    def __init__(self, message_base: str) -> None:
        super().__init__()
        self._message = message_base

    def on_channel(self, channel):
        try:
            int_val = int(channel)
            if int_val < 0 or int_val > 15:
                raise ValueError
            self._message += f" -c {int_val}"
        except ValueError:
            self.log.error(f"Unable to set channel: {channel}")
            raise
        
        return CCParameterBuilder(self._message)
    
    def with_value(self, value):
        try:
            int_val = int(value)
            if int_val < 0 or int_val > 127:
                raise ValueError("MIDI values are from 0-127")
            self._message += f" -v {int_val}"
        except ValueError:
            self.log.error(f"Unable to set channel: {value}")
            raise

        return CCParameterBuilder(self._message)
    
    def with_control_num(self, value):
        try:
            int_val = int(value)
            if int_val < 0 or int_val > 127:
                raise ValueError("MIDI values are from 0-127")
            self._message += f" -n {int_val}"
        except ValueError:
            self.log.error(f"Unable to set channel: {value}")
            raise

        return CCParameterBuilder(self._message)