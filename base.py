'''
Scripts to process and score World Cup prediction csvs

Dan Morris - 6/10/14 - 6/11/14
'''
import csv
import simplejson as json
import os

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

groupmatches = 'games.json'
knockoutfile = 'knockout.json'
grouprankfile = 'grouprank.json'
subfile = 'submissions.json'

def load_all_entries():
  # Reads all entry csv's, creates submission json file
  predictions = {} # keyed by submission name
  for f in os.listdir('submissions'):
    data = sub_cleanse(submission_scraper(f))
    k = data[7][1] # submission name
    print 'Creating prediction file for ' + k
    entry = create_entry_dict(data)
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
  with open('submissions/'+entry) as f:
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
      if cells[r][c] == 'Iran :(':
        cells[r][c] = 'Iran'
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
def get_group_game_id(team1,team2,matches):
  # returns the game # between two teams in group play
  for g in matches:
    if team1 in matches[g]['teams'] and team2 in matches[g]['teams']:
      return g
  return None
def score_all():
  # Scores all submissions
  scores = {}
  with open(subfile) as sf:
    entries = json.loads(sf.read())
  with open(groupmatches) as f:
    mr = json.loads(f.read())
  with open(knockoutfile) as f:
    kr = json.loads(f.read())
  with open(grouprankfile) as f:
    rr = json.loads(f.read())
  for e in entries:
    scores[e] = score_entry(entries[e],mr,kr,rr)
  scorecard(scores)
  return
def score_entry(entry,mr,kr,rr):
  # Scores a single entry
  s = 0
  for g in entry['games']:
    if entry['games'][g] == mr[g]['winner']:
      s += scoring_rules['groupgame']
  for group in entry['groupranks']:
    if entry['groupranks'][group] == rr[group]:
      s += scoring_rules['grouporder']
    for t in range(4):
      if entry['groupranks'][group][t] == rr[group][t]:
        s += scoring_rules['grouprank']
  for k in ['16','8','4','2','1']:
    for team in entry['knockout'][k]:
      if team in kr[k]:
        s += scoring_rules[k]
  return s
def scorecard(scores):
  # Prints a current scorecard. Needs work to actually rank scores.
  scorelist = []
  for s in scores:
    scorelist.append((s,scores[s]))
    print s + ': ' + str(scores[s])
  return

if __name__ == "__main__":
  load_all_entries()
