"""Seed the database with realistic demo content so the UI can be built without
API keys. No external calls; deterministic (fixed RNG seed) and idempotent
(``update_or_create`` on stable ``demo-*`` external ids), so re-running refreshes
rather than duplicates.
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from anime.models import Anime, AnimeEpisode
from core.sync import replace_trending_ranks
from games.models import Game
from movies.models import Movie
from sports.models import FootballFixture, FootballTeam
from tv.models import TVSeason, TVShow

GENRES = ["Action", "Adventure", "Comedy", "Drama", "Fantasy", "Horror",
          "Mystery", "Romance", "Sci-Fi", "Thriller"]
PLATFORMS = ["PC", "PS5", "Xbox Series X", "Nintendo Switch"]
STUDIOS = ["Studio Aurora", "Pixel Forge", "Nova Animation", "Bright Pictures"]
LEAGUES = {
    "Premier League": 39, "La Liga": 140, "Serie A": 135,
    "Bundesliga": 78, "Ligue 1": 61, "UEFA Champions League": 2,
}
TEAM_NAMES = ["Albion FC", "Rovers", "City United", "Athletic", "Royal SC", "Harbor FC",
              "Mountain CF", "Delta FC", "Lakeside", "Union SC", "Vanguard FC", "Cardinal FC"]
TRENDING_TOP = 20


class Command(BaseCommand):
    help = "Create a few hundred realistic demo rows per content type (no external calls)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=200, help="Rows per content type (default 200).")

    def handle(self, *args, **options):
        count = options["count"]
        self.rng = random.Random(1234)  # deterministic output
        self.today = timezone.localdate()
        self.now = timezone.now()

        self._seed_movies(count)
        self._seed_tv(count)
        self._seed_anime(count)
        self._seed_games(count)
        self._seed_football(count)
        self.stdout.write(self.style.SUCCESS(f"Seeded {count} rows per content type."))

    # -- helpers --
    def _genres(self):
        return self.rng.sample(GENRES, self.rng.randint(1, 3))

    def _spread_date(self, span=180):
        return self.today + timedelta(days=self.rng.randint(-span, span))

    def _popularity(self):
        return round(self.rng.uniform(1, 1000), 2)

    # -- per type --
    def _seed_movies(self, count):
        ids = []
        for i in range(count):
            obj, _ = Movie.objects.update_or_create(
                external_id=f"demo-movie-{i}",
                defaults={
                    "title": f"Demo Movie {i}",
                    "genres": self._genres(),
                    "release_date": self._spread_date(),
                    "rating": round(self.rng.uniform(1, 10), 1),
                    "popularity": self._popularity(),
                    "poster_url": f"https://picsum.photos/seed/movie{i}/300/450",
                },
            )
            ids.append((obj.external_id, obj.popularity))
        self._assign_trending(Movie, ids)

    def _seed_tv(self, count):
        ids = []
        for i in range(count):
            obj, _ = TVShow.objects.update_or_create(
                external_id=f"demo-tv-{i}",
                defaults={
                    "title": f"Demo Series {i}",
                    "genres": self._genres(),
                    "status": self.rng.choice([s for s, _ in TVShow.Status.choices]),
                    "rating": round(self.rng.uniform(1, 10), 1),
                    "popularity": self._popularity(),
                    "first_air_date": self._spread_date(365),
                    "next_episode_air_date": self._spread_date(30),
                    "next_episode_season": 1,
                    "next_episode_number": self.rng.randint(1, 12),
                    "poster_url": f"https://picsum.photos/seed/tv{i}/300/450",
                },
            )
            TVSeason.objects.update_or_create(
                show=obj, season_number=1,
                defaults={"air_date": obj.first_air_date, "state": TVSeason.State.AIRED},
            )
            ids.append((obj.external_id, obj.popularity))
        self._assign_trending(TVShow, ids)

    def _seed_anime(self, count):
        ids = []
        for i in range(count):
            status = self.rng.choice([s for s, _ in Anime.AiringStatus.choices])
            next_at = self.now + timedelta(days=self.rng.randint(1, 14)) if status == "releasing" else None
            obj, _ = Anime.objects.update_or_create(
                external_id=f"demo-anime-{i}",
                defaults={
                    "title": f"Demo Anime {i}",
                    "genres": self._genres(),
                    "airing_status": status,
                    "rating": round(self.rng.uniform(1, 10), 1),
                    "popularity": self._popularity(),
                    "studios": [self.rng.choice(STUDIOS)],
                    "next_airing_at": next_at,
                    "next_airing_episode_number": self.rng.randint(1, 24) if next_at else None,
                    "poster_url": f"https://picsum.photos/seed/anime{i}/300/450",
                },
            )
            if next_at:
                AnimeEpisode.objects.update_or_create(
                    anime=obj, episode_number=obj.next_airing_episode_number,
                    defaults={"aired_at": next_at, "notified": False},
                )
            ids.append((obj.external_id, obj.popularity))
        self._assign_trending(Anime, ids)

    def _seed_games(self, count):
        ids = []
        for i in range(count):
            obj, _ = Game.objects.update_or_create(
                external_id=f"demo-game-{i}",
                defaults={
                    "title": f"Demo Game {i}",
                    "genres": self._genres(),
                    "release_date": self._spread_date(),
                    "platforms": self.rng.sample(PLATFORMS, self.rng.randint(1, 3)),
                    "rating": round(self.rng.uniform(1, 5), 1),       # RAWG scale
                    "metacritic": self.rng.randint(40, 98),
                    "popularity": self._popularity(),
                    "poster_url": f"https://picsum.photos/seed/game{i}/300/450",
                },
            )
            ids.append((obj.external_id, obj.popularity))
        self._assign_trending(Game, ids)

    def _seed_football(self, count):
        teams = []
        for i, name in enumerate(TEAM_NAMES):
            competition = list(LEAGUES)[i % len(LEAGUES)]
            team, _ = FootballTeam.objects.update_or_create(
                external_id=f"demo-team-{i}",
                defaults={"name": name, "competition": competition,
                          "logo_url": f"https://picsum.photos/seed/team{i}/120/120"},
            )
            teams.append(team)
        statuses = [s for s, _ in FootballFixture.Status.choices]
        for i in range(count):
            home, away = self.rng.sample(teams, 2)
            kickoff = self.now + timedelta(days=self.rng.randint(-14, 28), hours=self.rng.randint(0, 23))
            status = FootballFixture.Status.FINISHED if kickoff < self.now else FootballFixture.Status.SCHEDULED
            finished = status == FootballFixture.Status.FINISHED
            FootballFixture.objects.update_or_create(
                external_id=f"demo-fixture-{i}",
                defaults={
                    "home_team": home, "away_team": away,
                    "competition": home.competition,
                    "league_external_id": LEAGUES[home.competition],
                    "kickoff_at": kickoff, "status": status,
                    "home_score": self.rng.randint(0, 4) if finished else None,
                    "away_score": self.rng.randint(0, 4) if finished else None,
                },
            )

    def _assign_trending(self, model, id_pop_pairs):
        top = sorted(id_pop_pairs, key=lambda pair: pair[1], reverse=True)[:TRENDING_TOP]
        replace_trending_ranks(model, [external_id for external_id, _ in top])
