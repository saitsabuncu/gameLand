from enum import Enum


class Achievement(Enum):
    """Unlockable milestones a player can earn by playing games well.

    Used as the currency for GameEntry.required_achievements: a locked
    game becomes playable once the player holds at least one of its
    required achievements (see GameRegistry/ProgressTracker).
    """

    NUMBER_GUESSING_GOOD_OR_BETTER = "number_guessing_good_or_better"
    MATH_QUIZ_GOOD_OR_BETTER = "math_quiz_good_or_better"
    PRIME_HUNTER_GOOD_OR_BETTER = "prime_hunter_good_or_better"
