import csv
import simplejson as json
from warnings import warn
from os.path import join as joinpath

# Filenames
# TODO: move out of this file
DATADIR = 'data'
GROUP_MATCH_FILE = joinpath(DATADIR, 'results_group.json')
KNOCKOUT_MATCH_FILE = joinpath(DATADIR, 'knockout.json')
GROUP_RANK_FILE = joinpath(DATADIR, 'grouprank.json')
SUBMISSIONS_FILE = joinpath(DATADIR, 'submissions.json')


class Bracket(object):

    def __init__(self, csv_file=None):
        """
        This is a base class for a bracket.
        Each submission is a bracket.
        Class will have methods to
            load a submission from file
            output bracket to file
            provide a score
            query for particular predictions
        """

        self.realname = None
        self.name = None
        self.games = None
        self.group_rankings = None
        self.knockout_picks = None
        self.team_points_verify = None
        self.tie_breaker = None

        if csv_file is not None:
            try:
                self.load_from_csv(csv_file)
            except:
                warn('Unable to load from csv {}'.format(csv_file))

    def load_from_csv(self, fname):

        # submission_scaper
        cells = []
        with open(fname) as f:
            reader = csv.reader(f)
            for row in reader:
                cells.append(row)

        # sub_cleanse
        # Spelling mistakes hack
        for idx, row in enumerate(cells):
            nrow = [r.strip() for r in row]
            nrow = [r.replace('Columbia', 'Colombia') for r in nrow]
            nrow = [r.replace('Urugay', 'Uruguay') for r in nrow]
            cells[idx] = nrow

        self.name = cells[7][1]
        self.realname = cells[5][1]

        self._load_predictions(cells)

        # TODO
        # check for problems here
        # self.check_entry()

        # Calculate score immediately upon loading
        self.get_score()

    def get_score(self):
        """Calculate bracket's score"""

        score = 0

        # Load results of group games
        with open(GROUP_MATCH_FILE) as infile:
            mr = json.loads(infile.read())

        for game in self.games:
            if self.games[game] == mr[game]['winner']:
                score += scoring_rules['groupgame']

        self.score = score
        return score


    # Internal Methods

    def _load_predictions(self, cells):
        """Takes matrix of strings from submissions"""
        self.games = {}
        # key: gameid. Value: predicted winner (or 'Draw')

        self.group_rankings = {}
        # key: group letter. Value: ordered list of teams

        # for checking group ranks
        points_check = {k: 0 for k, v in country_code.items()}

        ko = {"16": [], "8": [], "4": [], "2": [], "1": []}
        # value:  list of teams through

        with open(GROUP_MATCH_FILE) as mf:
            matches = json.loads(mf.read())

        # Group Stage
        starting_rows = [5, 13, 21, 29, 37, 45, 53, 61]
        for sr in starting_rows:
            # Group Matches
            for r in range(sr, sr+6):  # rows of 6 group games in that group
                team1 = cells[r][6]
                team2 = cells[r][8]
                gameid = self._get_group_game_id(team1, team2, matches)
                if cells[r][5] != '':
                    # Any "x" works. Make sure empty cells are empty!
                    if cells[r][7] != '':
                        self.games[gameid] = 'Draw'
                        points_check[team1] += 1
                        points_check[team2] += 1
                    else:
                        self.games[gameid] = team1
                        points_check[team1] += 3
                else:
                    self.games[gameid] = team2
                    points_check[team2] += 3
            # Group Standings + Round of 16
            groupid = group_row[sr]
            gpred = []
            for i in [0, 1]:
                gpred.append(cells[sr+i][11])
                ko["16"].append(cells[sr+i][11])
            for i in [2, 3]:
                gpred.append(cells[sr+i][11])
            self.group_rankings[groupid] = gpred

        self.team_points_verify = points_check

        # Knockout Stage
        # Round of 8 (R16 winners)
        for r in [7, 11, 15, 19, 23, 27, 31, 35]:
            if cells[r][15] != '':
                ko["8"].append(cells[r][16])
            else:
                ko["8"].append(cells[r][18])

        # Round of 4 (R8 winners)
        for r in [6, 12, 17, 23]:
            if cells[r][21] != '':
                ko["4"].append(cells[r][22])
            else:
                ko["4"].append(cells[r+1][22])

        # Round of 2 (R4 winners)
        for r in [9, 20]:
            if cells[r][26] != '':
                ko["2"].append(cells[r][27])
            else:
                ko["2"].append(cells[r+1][27])

        # Round of 1 (R2 winner)
        if cells[13][31] != '':
            ko["1"].append(cells[13][32])
        else:
            ko["1"].append(cells[14][32])

        self.knockout_picks = ko

        # Tiebreaker
        self.tie_breaker = cells[21][36]

    def _get_group_game_id(self, team1, team2, matches):
        # returns the game # between two teams in group play
        for g in matches:
            if team1 in matches[g]['teams'] and team2 in matches[g]['teams']:
                return g
        return None

    def __repr__(self):
        return "<Bracket '{}' by '{}': Score {:02}>".format(
            self.name,
            self.realname,
            self.score,
            )


country_code = {
    'Brazil': 1, 'Croatia': 2, 'Mexico': 3, 'Cameroon': 4,
    'Spain': 5, 'Netherlands': 6, 'Chile': 7, 'Australia': 8,
    'Colombia': 9, 'Greece': 10, 'Ivory Coast': 11, 'Japan': 12,
    'Uruguay': 13, 'Costa Rica': 14, 'England': 15, 'Italy': 16,
    'Switzerland': 17, 'Ecuador': 18, 'France': 19, 'Honduras': 20,
    'Argentina': 21, 'Bosnia-Herzegovina': 22, 'Iran': 23, 'Nigeria': 24,
    'Germany': 25, 'Portugal': 26, 'Ghana': 27, 'United States': 28,
    'Belgium': 29, 'Algeria': 30, 'Russia': 31, 'South Korea': 32
    }

group_row = {
    5: 'A', 13: 'B', 21: 'C', 29: 'D',
    37: 'E', 45: 'F', 53: 'G', 61: 'H'
    }

scoring_rules = {
    # These are the number of points awarded
    # for designated prediction.
    'groupgame': 1,
    'grouprank': 2,
    'grouporder': 5,
    '16': 4,
    '8': 8,
    '4': 16,
    '2': 32,
    '1': 64
    }
