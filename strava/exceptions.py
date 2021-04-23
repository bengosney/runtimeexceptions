class StravaError(Exception):
    pass


class StravaNotAuthenticated(StravaError):
    pass


class StravaGenericError(StravaError):
    pass


class StravaPaidFeature(StravaError):
    pass
