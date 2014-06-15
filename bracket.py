import csv
import simplejson as json
from os.path import join as joinpath

# Filenames
# TODO: move out of this file
DATADIR = 'data'
GROUP_MATCH_FILE = joinpath(DATADIR, 'games.json')
KNOCKOUT_MATCH_FILE = joinpath(DATADIR, 'knockout.json')
GROUP_RANK_FILE = joinpath(DATADIR, 'grouprank.json')
SUBMISSIONS_FILE = joinpath(DATADIR, 'submissions.json')


class Bracket(object):

    def __init__(self):
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
        self.predictions = None

    def load_from_csv(self, fname):

        # submission_scaper
        cells = []
        with open(fname) as f:
            reader = csv.reader(f)
            for row in reader:
                cells.append(row)

        # sub_cleanse
        # Spelling mistakes hack
        for r in range(67):
            for c in range(37):
                cells[r][c] = cells[r][c].strip()
                if cells[r][c] == 'Columbia':
                    cells[r][c] = 'Colombia'
                if cells[r][c] == 'Urugay':
                    cells[r][c] = 'Uruguay'

        self.name = cells[7][1]
        self.realname = cells[5][1]

        self.predictions = self.create_entry_dict(cells)

        # TODO
        # check for problems here
        # self.check_entry()

    def _create_entry_dict(self, cells):
        """Takes matrix of strings from submissions"""
        # Takes matrix of strings from submission_scraper, creates entry dict
        gamepreds = {}  # key: gameid. Value: predicted winner (or 'Draw')
        grouprankpreds = {}  # key: group letter. Value: ordered list of teams
        points = country_code  # for checking group ranks
        for c in points:
            points[c] = 0
        #  value:  list of teams through
        ko = {"16": [], "8": [], "4": [], "2": [], "1": []}
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
                        gamepreds[gameid] = 'Draw'
                        points[team1] += 1
                        points[team2] += 1
                    else:
                        gamepreds[gameid] = team1
                        points[team1] += 3
                else:
                    gamepreds[gameid] = team2
                    points[team2] += 3
            # Group Standings + Round of 16
            groupid = group_row[sr]
            gpred = []
            for i in [0, 1]:
                gpred.append(cells[sr+i][11])
                ko["16"].append(cells[sr+i][11])
            for i in [2, 3]:
                gpred.append(cells[sr+i][11])
            grouprankpreds[groupid] = gpred

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

        # Tiebreaker
        tb = cells[21][36]
        return {
            'games': gamepreds,
            'groupranks': grouprankpreds,
            'knockout': ko,
            'tiebreak': tb,
            'points': points
            }

    def _get_group_game_id(self, team1, team2, matches):
        # returns the game # between two teams in group play
        for g in matches:
            if team1 in matches[g]['teams'] and team2 in matches[g]['teams']:
                return g
        return None

    def __repr__(self):
        return "<Bracket '{}' by '{}'>".format(
            self.name,
            self.realname
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
