from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from aiarena.core.models import (
    ArenaClient,
    Competition,
    Game,
    GameMode,
    Map,
    Match,
    MatchParticipation,
    Round,
    User,
)
from aiarena.core.models.bot_race import BotRace
from aiarena.core.services.service_implementations._bots import BotsImpl
from aiarena.core.services.service_implementations._competitions import Competitions
from aiarena.core.services.service_implementations._matches import Matches
from aiarena.core.tests.testing_utils import create_bot_for_competition


class MatchPrioritizationTests(TestCase):
    """Tests for match prioritization in _attempt_to_start_a_ladder_match.

    Verifies that:
    - Bots with data enabled are prioritized over those without.
    - Among bots with equal data-enabled status, those that have waited longest
      since their last match start are prioritized.
    """

    def setUp(self):
        self.user = User.objects.create(username="testuser", email="test@test.com")
        self.arenaclient = ArenaClient.objects.create(trusted=True, owner=self.user)
        self.game = Game.objects.create(name="testgame")
        self.game_mode = GameMode.objects.create(name="testgamemode", game=self.game)
        BotRace.create_all_races()
        self.bot_race = BotRace.objects.first()
        self.competition = Competition.objects.create(name="testcompetition", game_mode=self.game_mode)
        self.competition.playable_races.add(self.bot_race)
        self.competition.open()
        self.match_map = Map.objects.create(name="testmap", game_mode=self.game_mode)
        self.match_map.competitions.add(self.competition)

        self.bots_service = BotsImpl()
        self.competitions_service = Competitions()
        self.matches_service = Matches(self.bots_service, self.competitions_service)

    def _create_bot(self, name, bot_data_enabled=False):
        return create_bot_for_competition(
            competition=self.competition,
            for_user=self.user,
            bot_name=name,
            bot_type="python",
            bot_race=self.bot_race,
        )

    def _create_bot_with_data(self, name, bot_data_enabled=True):
        bot = self._create_bot(name)
        bot.bot_data_enabled = bot_data_enabled
        bot.save()
        return bot

    def _create_round_match(self, round_obj, bot1, bot2):
        match = Match.objects.create(map=self.match_map, round=round_obj)
        MatchParticipation.objects.create(match=match, participant_number=1, bot=bot1)
        MatchParticipation.objects.create(match=match, participant_number=2, bot=bot2)
        return match

    def _complete_match(self, match, started_at=None):
        """Simulate starting and completing a match by creating a Result and linking it."""
        started_at = started_at or timezone.now() - timedelta(seconds=10)
        match.started = started_at
        match.first_started = match.started
        completed_at = started_at + timedelta(seconds=10)
        # Use MatchCancelled type to avoid replay_file validation in Result.save().
        # We also need to bypass Result.save() entirely because Result.__str__
        # accesses self.match.started via a reverse OneToOneField which may not be
        # available yet during creation.
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO core_result (type, game_steps, created, replay_file_has_been_cleaned, "
                "arenaclient_log_has_been_cleaned) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                ["MatchCancelled", 100, completed_at, False, False],
            )
            result_id = cursor.fetchone()[0]
        match.result_id = result_id
        match.save()

    def test_data_enabled_bots_prioritized_over_non_data_enabled(self):
        """Matches involving data-enabled bots should be started before others."""
        bot_data1 = self._create_bot_with_data("data_bot1", bot_data_enabled=True)
        bot_data2 = self._create_bot_with_data("data_bot2", bot_data_enabled=True)
        bot_nodata1 = self._create_bot_with_data("nodata_bot1", bot_data_enabled=False)
        bot_nodata2 = self._create_bot_with_data("nodata_bot2", bot_data_enabled=False)

        round_obj = Round.objects.create(competition=self.competition)
        # Create matches: one with data-enabled bots, one without
        match_data = self._create_round_match(round_obj, bot_data1, bot_data2)
        # match_nodata
        self._create_round_match(round_obj, bot_nodata1, bot_nodata2)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, round_obj)

        self.assertIsNotNone(started_match)
        self.assertEqual(started_match.id, match_data.id)

    def test_longest_waiting_bots_prioritized(self):
        """Among bots with same data-enabled status, those waiting longest should be prioritized."""
        bot1 = self._create_bot_with_data("bot1", bot_data_enabled=False)
        bot2 = self._create_bot_with_data("bot2", bot_data_enabled=False)
        bot3 = self._create_bot_with_data("bot3", bot_data_enabled=False)
        bot4 = self._create_bot_with_data("bot4", bot_data_enabled=False)

        now = timezone.now()
        round_obj = Round.objects.create(competition=self.competition)

        # Create previous completed matches with different start times
        # bot1 vs bot2: started 30 minutes ago (waited longest)
        old_match = self._create_round_match(round_obj, bot1, bot2)
        self._complete_match(old_match, started_at=now - timedelta(minutes=30))

        # bot3 vs bot4: started 5 minutes ago (waited less)
        recent_match = self._create_round_match(round_obj, bot3, bot4)
        self._complete_match(recent_match, started_at=now - timedelta(minutes=5))

        # Create new round with available matches
        new_round = Round.objects.create(competition=self.competition)
        match_old_bots = self._create_round_match(new_round, bot1, bot2)
        # match_recent_bots
        self._create_round_match(new_round, bot3, bot4)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        self.assertIsNotNone(started_match)
        self.assertEqual(started_match.id, match_old_bots.id)

    def test_data_enabled_bots_with_no_match_history_highest_priority(self):
        """Data-enabled bots with no match history should get highest priority."""
        bot_data_new = self._create_bot_with_data("data_new", bot_data_enabled=True)
        bot_data_new2 = self._create_bot_with_data("data_new2", bot_data_enabled=True)
        bot_nodata1 = self._create_bot_with_data("nodata1", bot_data_enabled=False)
        bot_nodata2 = self._create_bot_with_data("nodata2", bot_data_enabled=False)

        round_obj = Round.objects.create(competition=self.competition)
        match_data_new = self._create_round_match(round_obj, bot_data_new, bot_data_new2)
        # match_nodata
        self._create_round_match(round_obj, bot_nodata1, bot_nodata2)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, round_obj)

        self.assertIsNotNone(started_match)
        self.assertEqual(started_match.id, match_data_new.id)

    def test_mixed_data_enabled_prioritized_over_none(self):
        """A match with one data-enabled bot should be prioritized over a match with none."""
        bot_data1 = self._create_bot_with_data("data1", bot_data_enabled=True)
        bot_nodata1 = self._create_bot_with_data("nodata1", bot_data_enabled=False)
        bot_nodata2 = self._create_bot_with_data("nodata2", bot_data_enabled=False)
        bot_nodata3 = self._create_bot_with_data("nodata3", bot_data_enabled=False)

        round_obj = Round.objects.create(competition=self.competition)
        match_mixed = self._create_round_match(round_obj, bot_data1, bot_nodata1)
        # match_nodata
        self._create_round_match(round_obj, bot_nodata2, bot_nodata3)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, round_obj)

        self.assertIsNotNone(started_match)
        self.assertEqual(started_match.id, match_mixed.id)

    def test_among_data_enabled_longest_wait_wins(self):
        """Among multiple data-enabled matches, the one with longest-waiting bots wins."""
        bot_data_old1 = self._create_bot_with_data("data_old1", bot_data_enabled=True)
        bot_data_old2 = self._create_bot_with_data("data_old2", bot_data_enabled=True)
        bot_data_new1 = self._create_bot_with_data("data_new1", bot_data_enabled=True)
        bot_data_new2 = self._create_bot_with_data("data_new2", bot_data_enabled=True)

        now = timezone.now()
        setup_round = Round.objects.create(competition=self.competition)

        # old bots started a match 60 minutes ago
        old_match = self._create_round_match(setup_round, bot_data_old1, bot_data_old2)
        self._complete_match(old_match, started_at=now - timedelta(minutes=60))

        # new bots started a match 5 minutes ago
        new_match = self._create_round_match(setup_round, bot_data_new1, bot_data_new2)
        self._complete_match(new_match, started_at=now - timedelta(minutes=5))

        # Create available matches for the new round
        new_round = Round.objects.create(competition=self.competition)
        match_old_bots = self._create_round_match(new_round, bot_data_old1, bot_data_old2)
        # match_new_bots
        self._create_round_match(new_round, bot_data_new1, bot_data_new2)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        self.assertIsNotNone(started_match)
        self.assertEqual(started_match.id, match_old_bots.id)

    def test_fallback_to_non_data_enabled_when_fewer_than_two_data_enabled(self):
        """When only one data-enabled bot exists, fall back to longest-waiting non-data bots."""
        bot_data1 = self._create_bot_with_data("data1", bot_data_enabled=True)
        bot_nodata_old = self._create_bot_with_data("nodata_old", bot_data_enabled=False)
        bot_nodata_recent = self._create_bot_with_data("nodata_recent", bot_data_enabled=False)

        now = timezone.now()
        setup_round = Round.objects.create(competition=self.competition)

        # nodata_old started a match 60 minutes ago
        old_match = self._create_round_match(setup_round, bot_data1, bot_nodata_old)
        self._complete_match(old_match, started_at=now - timedelta(minutes=60))

        # nodata_recent started a match 5 minutes ago
        recent_match = self._create_round_match(setup_round, bot_data1, bot_nodata_recent)
        self._complete_match(recent_match, started_at=now - timedelta(minutes=5))

        # New round: only non-data matches available (data1 has only mixed matches)
        new_round = Round.objects.create(competition=self.competition)
        match_with_old = self._create_round_match(new_round, bot_data1, bot_nodata_old)
        match_with_recent = self._create_round_match(new_round, bot_data1, bot_nodata_recent)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        self.assertIsNotNone(started_match)
        # Both matches have one data-enabled bot (bot_data1) whose last match start was 5 minutes ago.
        # Since bot_data1 is shared between both matches, they have identical priority keys
        # and either may be selected.
        self.assertIn(started_match.id, [match_with_old.id, match_with_recent.id])

    def test_bot_with_no_previous_matches_uses_epoch(self):
        """A bot with no match history should use datetime.min (epoch) as its last match time,
        giving it highest priority among bots with the same data-enabled status."""
        bot_new1 = self._create_bot_with_data("new_bot1", bot_data_enabled=False)
        bot_new2 = self._create_bot_with_data("new_bot2", bot_data_enabled=False)
        bot_old1 = self._create_bot_with_data("old_bot1", bot_data_enabled=False)
        bot_old2 = self._create_bot_with_data("old_bot2", bot_data_enabled=False)

        now = timezone.now()
        setup_round = Round.objects.create(competition=self.competition)

        # old bots started a match 5 minutes ago
        old_match = self._create_round_match(setup_round, bot_old1, bot_old2)
        self._complete_match(old_match, started_at=now - timedelta(minutes=5))

        # new bots have NO match history at all — their last_match_start_times
        # entry is missing, so match_sort_key should fall back to epoch.

        new_round = Round.objects.create(competition=self.competition)
        match_new_bots = self._create_round_match(new_round, bot_new1, bot_new2)
        # match_old_bots
        self._create_round_match(new_round, bot_old1, bot_old2)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        self.assertIsNotNone(started_match)
        # Bots with no history get epoch (datetime.min) which sorts earliest,
        # so their match should be prioritized.
        self.assertEqual(started_match.id, match_new_bots.id)


class RoundOrderingTests(TestCase):
    """Tests that start_next_match_for_competition tries earlier rounds first.

    The rounds query in start_next_match_for_competition must ORDER BY cr.number
    so that matches from lower-numbered (older) rounds are attempted before
    higher-numbered (newer) rounds.
    """

    def setUp(self):
        self.user = User.objects.create(username="testuser", email="test@test.com")
        self.arenaclient = ArenaClient.objects.create(trusted=True, owner=self.user)
        self.game = Game.objects.create(name="testgame")
        self.game_mode = GameMode.objects.create(name="testgamemode", game=self.game)
        BotRace.create_all_races()
        self.bot_race = BotRace.objects.first()
        self.competition = Competition.objects.create(
            name="testcompetition",
            game_mode=self.game_mode,
            max_active_rounds=10,
        )
        self.competition.playable_races.add(self.bot_race)
        self.competition.open()
        self.match_map = Map.objects.create(name="testmap", game_mode=self.game_mode)
        self.match_map.competitions.add(self.competition)

        self.bots_service = BotsImpl()
        self.competitions_service = Competitions()
        self.matches_service = Matches(self.bots_service, self.competitions_service)

    def _create_bot(self, name):
        return create_bot_for_competition(
            competition=self.competition,
            for_user=self.user,
            bot_name=name,
            bot_type="python",
            bot_race=self.bot_race,
        )

    def _create_round_match(self, round_obj, bot1, bot2):
        match = Match.objects.create(map=self.match_map, round=round_obj)
        MatchParticipation.objects.create(match=match, participant_number=1, bot=bot1)
        MatchParticipation.objects.create(match=match, participant_number=2, bot=bot2)
        return match

    def test_earlier_round_matches_are_started_first(self):
        """When multiple rounds have unstarted matches, the earliest round's match should be started first."""
        bot1 = self._create_bot("bot1")
        bot2 = self._create_bot("bot2")
        bot3 = self._create_bot("bot3")
        bot4 = self._create_bot("bot4")

        # Create round 1 (earlier) and round 2 (later)
        round1 = Round.objects.create(competition=self.competition)  # number=1
        round2 = Round.objects.create(competition=self.competition)  # number=2

        self.assertLess(round1.number, round2.number)

        # Put matches in both rounds — each round has a distinct pair of bots
        match_round1 = self._create_round_match(round1, bot1, bot2)
        # match_round2
        self._create_round_match(round2, bot3, bot4)

        started_match = self.matches_service.start_next_match_for_competition(self.arenaclient, self.competition)

        self.assertIsNotNone(started_match)
        self.assertEqual(
            started_match.id,
            match_round1.id,
            "Expected the match from the earlier round to be started first, "
            f"but got match {started_match.id} (round {started_match.round_id}) "
            f"instead of match {match_round1.id} (round {round1.id}).",
        )

    def test_later_round_used_when_earlier_round_fully_started(self):
        """When the earlier round's matches are all started, the later round's match should be used."""
        bot1 = self._create_bot("bot1")
        bot2 = self._create_bot("bot2")
        bot3 = self._create_bot("bot3")
        bot4 = self._create_bot("bot4")

        round1 = Round.objects.create(competition=self.competition)
        round2 = Round.objects.create(competition=self.competition)

        # Round 1 match is already started (in progress)
        match_round1 = self._create_round_match(round1, bot1, bot2)
        match_round1.started = timezone.now()
        match_round1.first_started = match_round1.started
        match_round1.save()

        # Round 2 match is still unstarted
        match_round2 = self._create_round_match(round2, bot3, bot4)

        started_match = self.matches_service.start_next_match_for_competition(self.arenaclient, self.competition)

        self.assertIsNotNone(started_match)
        self.assertEqual(
            started_match.id,
            match_round2.id,
            "Expected the match from round 2 since round 1's match is already started.",
        )


class FallbackMatchStartTests(TestCase):
    """Tests for the fallback behavior in _attempt_to_start_a_ladder_match.

    When all bots are busy with active data-updating matches, the fallback should:
    - Select from all unstarted matches in the round.
    - Disable bot data (use_bot_data=False, update_bot_data=False) so they can
      run concurrently with other active data-updating matches.
    - Actually start the match instead of blocking the queue.
    """

    def setUp(self):
        self.user = User.objects.create(username="testuser", email="test@test.com")
        self.arenaclient = ArenaClient.objects.create(trusted=True, owner=self.user)
        self.game = Game.objects.create(name="testgame")
        self.game_mode = GameMode.objects.create(name="testgamemode", game=self.game)
        BotRace.create_all_races()
        self.bot_race = BotRace.objects.first()
        self.competition = Competition.objects.create(name="testcompetition", game_mode=self.game_mode)
        self.competition.playable_races.add(self.bot_race)
        self.competition.open()
        self.match_map = Map.objects.create(name="testmap", game_mode=self.game_mode)
        self.match_map.competitions.add(self.competition)

        self.bots_service = BotsImpl()
        self.competitions_service = Competitions()
        self.matches_service = Matches(self.bots_service, self.competitions_service)

    def _create_bot_with_data(self, name, bot_data_enabled=True):
        bot = create_bot_for_competition(
            competition=self.competition,
            for_user=self.user,
            bot_name=name,
            bot_type="python",
            bot_race=self.bot_race,
        )
        bot.bot_data_enabled = bot_data_enabled
        bot.save()
        return bot

    def _create_round_match(self, round_obj, bot1, bot2):
        match = Match.objects.create(map=self.match_map, round=round_obj)
        MatchParticipation.objects.create(match=match, participant_number=1, bot=bot1)
        MatchParticipation.objects.create(match=match, participant_number=2, bot=bot2)
        return match

    def _start_match_in_progress(self, match):
        """Start a match without completing it (no result), simulating an in-progress match."""
        match.started = timezone.now()
        match.first_started = match.started
        match.save()

    def test_fallback_starts_match_when_all_bots_busy_with_data(self):
        """When all bots are in active data-updating matches, the fallback should
        start a match with bot data disabled."""
        bot1 = self._create_bot_with_data("bot1", bot_data_enabled=True)
        bot2 = self._create_bot_with_data("bot2", bot_data_enabled=True)

        # Create an active match between bot1 and bot2 with data (use_bot_data=True, update_bot_data=True)
        active_round = Round.objects.create(competition=self.competition)
        active_match = self._create_round_match(active_round, bot1, bot2)
        self._start_match_in_progress(active_match)

        # Now create a new round with an unstarted match between the same bots
        new_round = Round.objects.create(competition=self.competition)
        pending_match = self._create_round_match(new_round, bot1, bot2)

        # Attempt to start a match — should use the fallback
        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        self.assertIsNotNone(started_match, "Fallback should have started a match")
        self.assertEqual(started_match.id, pending_match.id)

    def test_fallback_disables_bot_data_on_participations(self):
        """When the fallback fires, match participations should have
        use_bot_data=False and update_bot_data=False."""
        bot1 = self._create_bot_with_data("bot1", bot_data_enabled=True)
        bot2 = self._create_bot_with_data("bot2", bot_data_enabled=True)

        # Create an active data-updating match
        active_round = Round.objects.create(competition=self.competition)
        active_match = self._create_round_match(active_round, bot1, bot2)
        self._start_match_in_progress(active_match)

        # Create new unstarted match
        new_round = Round.objects.create(competition=self.competition)
        self._create_round_match(new_round, bot1, bot2)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)
        self.assertIsNotNone(started_match)

        # Verify bot data was disabled on the started match's participations
        for mp in MatchParticipation.objects.filter(match=started_match):
            self.assertFalse(mp.use_bot_data, f"use_bot_data should be False for participant {mp.participant_number}")
            self.assertFalse(
                mp.update_bot_data, f"update_bot_data should be False for participant {mp.participant_number}"
            )

    def test_normal_path_keeps_bot_data_enabled(self):
        """When available bots exist (not all busy), the normal path should be used
        and bot data should remain enabled."""
        bot1 = self._create_bot_with_data("bot1", bot_data_enabled=True)
        bot2 = self._create_bot_with_data("bot2", bot_data_enabled=True)

        # No active matches — bots are free
        new_round = Round.objects.create(competition=self.competition)
        pending_match = self._create_round_match(new_round, bot1, bot2)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)
        self.assertIsNotNone(started_match)
        self.assertEqual(started_match.id, pending_match.id)

        # Verify bot data is still enabled (normal path, no fallback)
        for mp in MatchParticipation.objects.filter(match=started_match):
            self.assertTrue(mp.use_bot_data, f"use_bot_data should remain True for participant {mp.participant_number}")
            self.assertTrue(
                mp.update_bot_data, f"update_bot_data should remain True for participant {mp.participant_number}"
            )

    def test_fallback_with_multiple_matches_starts_one(self):
        """When multiple unstarted matches exist and all bots are busy,
        the fallback should start one of them."""
        bot1 = self._create_bot_with_data("bot1", bot_data_enabled=True)
        bot2 = self._create_bot_with_data("bot2", bot_data_enabled=True)
        bot3 = self._create_bot_with_data("bot3", bot_data_enabled=True)
        bot4 = self._create_bot_with_data("bot4", bot_data_enabled=True)

        # All bots are busy with active data-updating matches
        active_round = Round.objects.create(competition=self.competition)
        active_match1 = self._create_round_match(active_round, bot1, bot2)
        self._start_match_in_progress(active_match1)
        active_match2 = self._create_round_match(active_round, bot3, bot4)
        self._start_match_in_progress(active_match2)

        # Create new round with two unstarted matches
        new_round = Round.objects.create(competition=self.competition)
        pending_match1 = self._create_round_match(new_round, bot1, bot3)
        pending_match2 = self._create_round_match(new_round, bot2, bot4)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        self.assertIsNotNone(started_match, "Fallback should have started one of the pending matches")
        self.assertIn(started_match.id, [pending_match1.id, pending_match2.id])

    def test_fallback_does_not_affect_active_match_participations(self):
        """The fallback should only disable bot data on unstarted matches,
        not on the already-active matches."""
        bot1 = self._create_bot_with_data("bot1", bot_data_enabled=True)
        bot2 = self._create_bot_with_data("bot2", bot_data_enabled=True)

        # Create an active data-updating match
        active_round = Round.objects.create(competition=self.competition)
        active_match = self._create_round_match(active_round, bot1, bot2)
        self._start_match_in_progress(active_match)

        # Create new unstarted match
        new_round = Round.objects.create(competition=self.competition)
        self._create_round_match(new_round, bot1, bot2)

        self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        # Verify active match's participations still have data enabled
        for mp in MatchParticipation.objects.filter(match=active_match):
            self.assertTrue(
                mp.use_bot_data, f"Active match use_bot_data should remain True for participant {mp.participant_number}"
            )
            self.assertTrue(
                mp.update_bot_data,
                f"Active match update_bot_data should remain True for participant {mp.participant_number}",
            )

    def test_no_fallback_when_some_bots_available(self):
        """When some bots are available (not busy), the normal path should be used.
        Matches between available bots should be started with data enabled."""
        bot_busy1 = self._create_bot_with_data("busy1", bot_data_enabled=True)
        bot_busy2 = self._create_bot_with_data("busy2", bot_data_enabled=True)
        bot_free1 = self._create_bot_with_data("free1", bot_data_enabled=True)
        bot_free2 = self._create_bot_with_data("free2", bot_data_enabled=True)

        # busy bots are in an active data-updating match
        active_round = Round.objects.create(competition=self.competition)
        active_match = self._create_round_match(active_round, bot_busy1, bot_busy2)
        self._start_match_in_progress(active_match)

        # Create new round with matches: one between free bots, one between busy bots
        new_round = Round.objects.create(competition=self.competition)
        match_free = self._create_round_match(new_round, bot_free1, bot_free2)
        self._create_round_match(new_round, bot_busy1, bot_busy2)

        started_match = self.matches_service._attempt_to_start_a_ladder_match(self.arenaclient, new_round)

        self.assertIsNotNone(started_match)
        self.assertEqual(
            started_match.id,
            match_free.id,
            "Should use normal path and start the match between free bots",
        )
        # Verify bot data remains enabled (normal path, no fallback)
        for mp in MatchParticipation.objects.filter(match=started_match):
            self.assertTrue(mp.use_bot_data)
