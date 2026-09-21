from typing import Literal

from cyberham.types import GradSemester


def pretty_semester(sem: GradSemester) -> Literal["Spring", "Summer", "Fall", "Winter"]:
    match sem:
        case "spring":
            return "Spring"
        case "summer":
            return "Summer"
        case "fall":
            return "Fall"
        case "winter":
            return "Winter"
