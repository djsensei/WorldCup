'''
Scripts to process and score World Cup prediction csvs

Dan Morris - 6/10/14 - 6/18/14
'''
import csv
import simplejson as json
import os
from operator import itemgetter
from bracket import *

country_code = \
{'Brazil':1,'Croatia':2,'Mexico':3,'Cameroon':4,\
'Spain':5,'Netherlands':6,'Chile':7,'Australia':8,\
'Colombia':9,'Greece':10,'Ivory Coast':11,'Japan':12,\
'Uruguay':13,'Costa Rica':14,'England':15,'Italy':16,\
'Switzerland':17,'Ecuador':18,'France':19,'Honduras':20,\
'Argentina':21,'Bosnia-Herzegovina':22,'Iran':23,'Nigeria':24,\
'Germany':25,'Portugal':26,'Ghana':27,'United States':28,\
'Belgium':29,'Algeria':30,'Russia':31,'South Korea':32}

code_country = {v:k for k,v in country_code.items()}

scoring_rules = {'groupgame':1,'grouprank':2,'grouporder':5,'16':4,'8':8,\
'4':16,'2':32,'1':64}

group_row = {5:'A',13:'B',21:'C',29:'D',37:'E',45:'F',53:'G',61:'H'}

groupmatches = 'data/results_group.json'
knockoutfile = 'knockout.json'
grouprankfile = 'grouprank.json'
subfile = 'submissions.json'

''' -- Loading Functions -- '''
def load_all_entries():
  # Reads all entry csvs in the Submissions folder
  # Creates submission json file
  predictions = {} # keyed by submission name
  print 'Creating prediction files...'
  for f in os.listdir('submissions'):
    data = sub_cleanse(submission_scraper(f))
    k = data[7][1] # submission name
    name = data[5][1] # real name
    entry = create_entry_dict(data)
    entry['realname'] = name
    problems = check_entry(entry)
    if problems == []:
      predictions[k] = entry
    else:
      print "Something wrong with " + f
      for p in problems:
        print '  ' + p
  with open(subfile,'w') as f:
    print 'Dumping predictions to ' + subfile
    json.dump(predictions,f,indent=0)
  return
def submission_scraper(entry):
  # Reads in the submission csv file 'entry', returns it as a list of lists
  cells = []
  with open('submissions/'+entry,'rb') as f:
    reader = csv.reader(f)
    for row in reader:
      cells.append(row)
  return cells
def sub_cleanse(cells):
  # Fixes errors in the entry sheet. Add more errors as they are found!
  for r in range(67):
    for c in range(37):
      cells[r][c] = cells[r][c].strip()
      if cells[r][c] == 'Columbia':
        cells[r][c] = 'Colombia'
      if cells[r][c] == 'Urugay':
        cells[r][c] = 'Uruguay'
  return cells
def create_entry_dict(cells):
  # Takes matrix of strings from submission_scraper, creates entry dict
  gamepreds = {} # key: gameid. Value: predicted winner (or 'Draw')
  grouprankpreds = {} # key: group letter. Value: ordered list of teams
  points = country_code # for checking group ranks
  for c in points:
    points[c] = 0
  ko = {"16":[],"8":[],"4":[],"2":[],"1":[]} # value: list of teams through
  with open(groupmatches) as mf:
    matches = json.loads(mf.read())
  # Group Stage
  for sr in [5, 13, 21, 29, 37, 45, 53, 61]: # starting rows of each group
    # Group Matches
    for r in range(sr,sr+6): # rows of 6 group games in that group
      team1 = cells[r][6]
      team2 = cells[r][8]
      gameid = get_group_game_id(team1,team2,matches)
      if cells[r][5] != '': # Any "x" works. Make sure empty cells are empty!
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
    for i in [0,1]:
      gpred.append(cells[sr+i][11])
      ko["16"].append(cells[sr+i][11])
    for i in [2,3]:
      gpred.append(cells[sr+i][11])
    grouprankpreds[groupid] = gpred
  # Knockout Stage
  # Round of 8 (R16 winners)
  for r in [7,11,15,19,23,27,31,35]:
    if cells[r][15] != '':
      ko["8"].append(cells[r][16])
    else:
      ko["8"].append(cells[r][18])
  # Round of 4 (R8 winners)
  for r in [6,12,17,23]:
    if cells[r][21] != '':
      ko["4"].append(cells[r][22])
    else:
      ko["4"].append(cells[r+1][22])
  # Round of 2 (R4 winners)
  for r in [9,20]:
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
  return {'games':gamepreds,'groupranks':grouprankpreds,'knockout':ko,\
          'tiebreak':tb,'points':points}
def check_entry(entry):
  # Checks to make sure each group game is predicted and that the other lists
  #   are the right length
  # TODO: Use 'points' to check group ranks
  problems = []
  for i in range(48):
    if str(i+1) not in entry['games']:
      problems.append('Missing game ' + str(i+1))
  for g in ['A','B','C','D','E','F','G','H']:
    if len(entry['groupranks'][g]) != 4:
      problems.append('Group ' + g + ' ranks incorrect length')
    for team in range(1,4):
      p1 = entry['points'][entry['groupranks'][g][team]]
      p0 = entry['points'][entry['groupranks'][g][team-1]]
      if p1 > p0:
        problems.append('Group ' + g + ' ranks out of order')
  for k in [16,8,4,2,1]:
    if len(entry['knockout'][str(k)]) != k:
      problems.append('Round of ' + str(k) + ' incorrect length')
  return problems
def load_submissions():
  # returns a dict of submissions from subfile
  with open(subfile) as sf:
    subs = json.loads(sf.read())
  return subs
def load_games():
  # returns a dict of group games from groupmatches
  with open(groupmatches) as f:
    mr = json.loads(f.read())
  return mr
''' Loading Functions using bracket.py'''
def load_all_entries_bracket():
  # Uses the bracket.py modules to load all entries into a list
  entries = []
  for f in os.listdir('submissions/csv'):
    entries.append(Bracket('submissions/csv/'+f))
  return entries
''' ----------------------- '''

''' -- Helper Functions -- '''
def get_group_game_id(team1,team2,matches):
  # returns the game # between two teams in group play
  for g in matches:
    if team1 in matches[g]['teams'] and team2 in matches[g]['teams']:
      return g
  return None
def select_pickers(pick,game=None,koround=None):
  # Returns a list of all entries who picked a certain outcome.
  # Pick can either be a team name or 'Draw'
  # Either game or koround should exist, but not both.
  #   If game exists, it should be a game id from the group stage
  #   If koround exists, it should be one of ['16','8','4','2','1']
  entries = load_submissions()
  selected = []
  if game != None:
    for e in entries:
      if pick in entries[e]['games'][game]:
        selected.append(e)
  elif koround != None:
    for e in entries:
      if pick in entries[e]['knockout'][koround]:
        selected.append(e)
  else:
    print "Improper select_pickers call. Check your code."
  return selected
def select_pickers_bracket(pick,game=None,koround=None):
  # Same as above, uses bracket class
  entries = load_all_entries_bracket()
  selected = []
  if game != None:
    for e in entries:
      if pick in e.games[game]:
        selected.append(e)
  elif koround != None:
    for e in entries:
      if pick in e.knockout_picks[koround]:
        selected.append(e)
  else:
    print "Improper select_pickers call. Check your code."
  return selected
def realname_from_entryname(entryname):
  # Given an entry name, finds the real name associated with it
  subs = load_submissions()
  for s in subs:
    if s == entryname:
      return subs[s]['realnames']
  return None
def game_pick_distributions():
  # Prints a list of group games and the number of people who made each pick
  subs = load_submissions()
  mr = load_games()
  games = [None] # list of game pick dicts: games[0] = None for indexing
  for i in range(1,49):
    team1 = mr[str(i)]['teams'][0]
    team2 = mr[str(i)]['teams'][1]
    games.append({team1:0,team2:0,'Draw':0})
  for s in subs:
    for g in subs[s]['games']:
      p = subs[s]['games'][g]
      games[int(g)][p] += 1
  for i in range(1,49):
    team1 = mr[str(i)]['teams'][0]
    team2 = mr[str(i)]['teams'][1]
    print 'Game '+str(i)+' picks: '+team1+'-'+str(games[i][team1])+' '+\
          team2+'-'+str(games[i][team2])+' '+'Draw-'+str(games[i]['Draw'])
  return
def game_pick_distributions_bracket():
  # Uses bracket.py entries to print distribution of picks
  entries = load_all_entries_bracket()
  mr = load_games()
  allgames = [None] # list of game pick dicts: games[0] = None for indexing
  for i in range(1,49):
    team1 = mr[str(i)]['teams'][0]
    team2 = mr[str(i)]['teams'][1]
    allgames.append({team1:0,team2:0,'Draw':0})
  for e in entries:
    for g in e.games:
      p = e.games[g]
      allgames[int(g)][p] += 1
  for i in range(1,49):
    team1 = mr[str(i)]['teams'][0]
    team2 = mr[str(i)]['teams'][1]
    print 'Game '+str(i)+' picks: '+team1+'-'+str(allgames[i][team1])+' '+\
          team2+'-'+str(allgames[i][team2])+' '+'Draw-'+str(allgames[i]['Draw'])
  return
''' ---------------------- '''

''' -- Scoring Functions -- '''
def score_all():
  # Scores all submissions
  scores = {}
  names = {}
  entries = load_submissions()
  mr = load_games()
  # Comment out until group stage is over
  '''with open(knockoutfile) as f:
    kr = json.loads(f.read())
  with open(grouprankfile) as f:
    rr = json.loads(f.read())'''
  kr = None # remove once knockout is known
  rr = None # remove once group ranks are known


  for e in entries:
    scores[e] = score_entry(entries[e],mr,kr,rr)
    names[e] = entries[e]['realname']
  scorecard(scores,names)
  return
def score_entry(entry,mr,kr,rr):
  # Scores a single entry
  s = 0
  for g in entry['games']:
    if entry['games'][g] == mr[g]['winner']:
      s += scoring_rules['groupgame']
  # Commented out until group stage is over
  '''for group in entry['groupranks']:
    if entry['groupranks'][group] == rr[group]:
      s += scoring_rules['grouporder']
    for t in range(4):
      if entry['groupranks'][group][t] == rr[group][t]:
        s += scoring_rules['grouprank']
  for k in ['16','8','4','2','1']:
    for team in entry['knockout'][k]:
      if team in kr[k]:
        s += scoring_rules[k]'''
  return s
def scorecard(scores,names):
  # Prints a current scorecard.
  scorelist = []
  for s in scores:
    scorelist.append((s,scores[s],))
  scorelist = sorted(scorelist, key=itemgetter(1), reverse=True)
  print 'Current Scores:'
  for s in scorelist:
    print '  ' + s[0] + ' (' + names[s[0]] + '): ' + str(s[1])
  return
def scorecard_bracket(entries):
  # Prints bracket.py-loaded list of entries by score
  all_scores = {}
  for bracket in entries:
    k = '{} ({})'.format(bracket.name, bracket.realname)
    all_scores[k] = bracket.score
  scorelist = sorted(all_scores.iteritems(), key=itemgetter(1), reverse=True)
  for n,s in scorelist:
    print "{} : {}".format(n,s)
  return
''' ----------------------- '''

if __name__ == "__main__":
  entries = load_all_entries_bracket()
  scorecard_bracket(entries)
