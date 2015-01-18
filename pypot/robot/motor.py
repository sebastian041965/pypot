class Motor(object):
    """ Purely abstract class representing any motor object. """

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name
