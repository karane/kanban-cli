from enum import Enum


class Status(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    TESTING_DEPLOYMENT = "TESTING_DEPLOYMENT"
    DONE = "DONE"

    @classmethod
    def ordered(cls):
        return [
            cls.TODO,
            cls.IN_PROGRESS,
            cls.REVIEW,
            cls.TESTING_DEPLOYMENT,
            cls.DONE,
        ]


VALID_TRANSITIONS = {
    Status.TODO: {Status.IN_PROGRESS},
    Status.IN_PROGRESS: {Status.REVIEW},
    Status.REVIEW: {Status.TESTING_DEPLOYMENT},
    Status.TESTING_DEPLOYMENT: {Status.DONE},
    Status.DONE: set(),
}
