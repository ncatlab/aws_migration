class NLabSyntaxError(Exception):
    def __init__(self, message):
        super().__init__(message)

class NotYetSupportedError(Exception):
    def __init__(self, message):
        super().__init__(message)
