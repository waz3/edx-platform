import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from student.models import unique_id_for_user


log = logging.getLogger(__name__)

class Score(models.Model):
    """
    This model stores the scores of different users on FoldIt problems.
    """
    user = models.ForeignKey(User, db_index=True,
                             related_name='foldit_scores')

    # The XModule that wants to access this doesn't have access to the real
    # userid.  Save the anonymized version so we can look up by that.
    unique_user_id = models.CharField(max_length=50, db_index=True)
    puzzle_id = models.IntegerField()
    best_score = models.FloatField(db_index=True)
    current_score = models.FloatField(db_index=True)
    score_version = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)


class PuzzleComplete(models.Model):
    """
    This keeps track of the sets of puzzles completed by each user.

    e.g. PuzzleID 1234, set 1, subset 3.  (Sets and subsets correspond to levels
    in the intro puzzles)
    """
    class Meta:
        # there should only be one puzzle complete entry for any particular
        # puzzle for any user
        unique_together = ('user', 'puzzle_id', 'puzzle_set', 'puzzle_subset')
        ordering = ['puzzle_id']

    user = models.ForeignKey(User, db_index=True,
                             related_name='foldit_puzzles_complete')

    # The XModule that wants to access this doesn't have access to the real
    # userid.  Save the anonymized version so we can look up by that.
    unique_user_id = models.CharField(max_length=50, db_index=True)
    puzzle_id = models.IntegerField()
    puzzle_set = models.IntegerField(db_index=True)
    puzzle_subset = models.IntegerField(db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "PuzzleComplete({0}, id={1}, set={2}, subset={3}, created={4})".format(
            self.user.username, self.puzzle_id,
            self.puzzle_set, self.puzzle_subset,
            self.created)


    @staticmethod
    def completed_puzzles(anonymous_user_id):
        """
        Return a list of puzzles that this user has completed, as an array of
        dicts:

        [ {'set': int,
           'subset': int,
           'created': datetime} ]
        """
        complete = PuzzleComplete.objects.filter(unique_user_id=anonymous_user_id)
        return [{'set': c.puzzle_set,
                 'subset': c.puzzle_subset,
                 'created': c.created} for c in complete]


    @staticmethod
    def is_level_complete(anonymous_user_id, level, sub_level, due=None):
        """
        Return True if this user completed level--sub_level by due.

        Users see levels as e.g. 4-5.

        Args:
            level: int
            sub_level: int
            due (optional): If specified, a datetime.  Ignored if None.
        """
        complete = PuzzleComplete.objects.filter(unique_user_id=anonymous_user_id,
                                                 puzzle_set=level,
                                                 puzzle_subset=sub_level)
        if due is not None:
            complete = complete.filter(created__lte=due)

        return complete.exists()

