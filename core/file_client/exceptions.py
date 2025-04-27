class FileClientException(FileNotFoundError):

    def __init__(self, status, error):
        self.status = status
        self.error = error
