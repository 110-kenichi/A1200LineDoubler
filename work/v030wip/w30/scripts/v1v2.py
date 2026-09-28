import sys,json;sys.path.insert(0,'/home/claude/tools')
import pcbedit as E
g=json.load(open('/tmp/s2/g6.json'))
b=E.Board(sys.argv[1])
n=0
for t in g['tracks']:
    if t['net']=='1V2' and t['layer']=='B.Cu' and max(t['a'][0],t['b'][0])<44.1:
        b.remove_segment('1V2',tuple(t['a']),tuple(t['b']),layer='B.Cu');n+=1
print('removed',n)
b.add_segment('1V2',(44.0,37.225),(58.0,37.225),layer='In2.Cu',width=.4)
b.save(sys.argv[2])
