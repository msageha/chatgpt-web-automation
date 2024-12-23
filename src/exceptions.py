class LoginFailedError(Exception):
    pass


class ResponseTimeoutError(Exception):
    pass


class CloudflareChallengeError(Exception):
    pass


class ModelSelectionError(Exception):
    pass


class ImageUploadError(Exception):
    pass
