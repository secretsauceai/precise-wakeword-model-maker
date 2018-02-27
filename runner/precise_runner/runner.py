# Python 2 + 3
# Copyright (c) 2017 Mycroft AI Inc.
import atexit
from subprocess import PIPE, Popen
from threading import Thread


class Engine:
    def __init__(self, chunk_size=1024):
        self.chunk_size = chunk_size

    def start(self):
        pass

    def stop(self):
        pass

    def get_prediction(self, chunk):
        raise NotImplementedError


class PreciseEngine(Engine):
    """
    Wraps a binary precise executable

    Args:
        exe_file (Union[str, list]): Either filename or list of arguments
                                     (ie. ['python', 'precise/scripts/engine.py'])
        model_file (str): Location to .pb model file to use (with .pb.params)
        chunk_size (int): Number of samples per prediction. Higher numbers
                          decrease CPU usage but increase latency
    """

    def __init__(self, exe_file, model_file, chunk_size=1024):
        Engine.__init__(self, chunk_size)
        self.exe_args = exe_file if isinstance(exe_file, list) else [exe_file]
        self.model_file = model_file
        self.proc = None

    def start(self):
        self.proc = Popen([*self.exe_args, self.model_file, str(self.chunk_size)], stdin=PIPE,
                          stdout=PIPE)

    def stop(self):
        if self.proc:
            self.proc.kill()
            self.proc = None

    def get_prediction(self, chunk):
        self.proc.stdin.write(chunk)
        self.proc.stdin.flush()
        return float(self.proc.stdout.readline())


class ListenerEngine(Engine):
    def __init__(self, listener, chunk_size=1024):
        Engine.__init__(self, chunk_size)
        self.get_prediction = listener.update


class PreciseRunner:
    """
    Wrapper to use Precise. Example:
    >>> def on_act():
    ...     print('Activation!')
    ...
    >>> p = PreciseRunner(PreciseEngine('./precise-engine'), on_activation=on_act)
    >>> p.start()
    >>> from time import sleep; sleep(10)
    >>> p.stop()

    Args:
        engine (Engine): Object containing info on the binary engine
        trigger_level (int): Number of chunk activations needed to trigger on_activation
                       Higher values add latency but reduce false positives
        sensitivity (float): From 0.0 to 1.0, relates to the network output level required
                             to consider a chunk "active"
        stream (BinaryIO): Binary audio stream to read 16000 Hz 1 channel int16
                           audio from. If not given, the microphone is used
        on_prediction (Callable): callback for every new prediction
        on_activation (Callable): callback for when the wake word is heard
    """

    def __init__(self, engine, trigger_level=3, sensitivity=0.5, stream=None,
                 on_prediction=lambda x: None, on_activation=lambda: None):
        self.engine = engine
        self.trigger_level = trigger_level
        self.sensitivity = sensitivity
        self.stream = stream
        self.on_prediction = on_prediction
        self.on_activation = on_activation
        self.chunk_size = engine.chunk_size

        self.pa = None
        self.thread = None
        self.running = False
        atexit.register(self.stop)

    def start(self):
        """Start listening from stream"""
        if self.stream is None:
            from pyaudio import PyAudio, paInt16
            self.pa = PyAudio()
            self.stream = self.pa.open(
                16000, 1, paInt16, True, frames_per_buffer=self.chunk_size // 2
            )

        self.engine.start()
        self.running = True
        self.thread = Thread(target=self._handle_predictions)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop listening and close stream"""
        self.engine.stop()

        if self.thread:
            self.running = False
            self.thread.join()
            self.thread = None

        if self.pa:
            self.pa.terminate()
            self.stream.stop_stream()
            self.stream = self.pa = None

    def _handle_predictions(self):
        """Continuously check Precise process output"""
        activation = 0
        while self.running:
            chunk = self.stream.read(self.chunk_size)
            prob = self.engine.get_prediction(chunk)
            self.on_prediction(prob)

            if prob > 1 - self.sensitivity or activation < 0:
                activation += 1
                if activation > self.trigger_level:
                    activation = -self.chunk_size // 50
                    self.on_activation()
            elif activation > 0:
                activation -= 1