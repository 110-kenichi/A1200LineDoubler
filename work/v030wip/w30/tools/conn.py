# usage: conn.py board "REF:PIN" "REF:PIN,REF:PIN,..." [more pairs]
import pcbnew as p,sys
b=p.LoadBoard(sys.argv[1]);b.BuildConnectivity();c=b.GetConnectivity()
zm=[(z,{x.m_Uuid.AsString() for x in list(c.GetConnectedTracks(z))+list(c.GetConnectedPads(z))}) for z in b.Zones()]
def pad(s):r,n=s.split(':');return [q for q in b.FindFootprintByReference(r).Pads() if q.GetNumber()==n][0]
def comp(q):
    seen=set();todo=[q]
    while todo:
        x=todo.pop();u=x.m_Uuid.AsString()
        if u in seen:continue
        seen.add(u);todo+=list(c.GetConnectedTracks(x))+list(c.GetConnectedPads(x))+[z for z,m in zm if u in m]
    return seen
bad=0;n=0
for a,zs in zip(sys.argv[2::2],sys.argv[3::2]):
    C=comp(pad(a))
    for z in zs.split(','):
        n+=1
        if pad(z).m_Uuid.AsString() not in C:bad+=1;print('FAIL',a,z)
print('checked',n,'fail',bad)
