VERSION = 'topology-1'

def make_topology():
    assets, connections = [], []
    def add(id, kind, label, parent, p):
        a = dict(id=id, kind=kind, label=label, parent_id=parent, meter_id='meter-'+id,
                 position_m=p, topology_version=VERSION, provenance='synthetic')
        if kind == 'pole': a['meter_id'] = None
        assets.append(a)
        return a
    for f in range(2):
        fx = -34 + f*68
        fid = f'feeder-{f+1:02}'
        add(fid,'feeder',f'Feeder {f+1}',None,[fx,2,-46])
        for t in range(2):
            ti=f*2+t; tid=f'transformer-{ti+1:02}'; tz=-25+t*49
            add(tid,'transformer',f'Transformer {ti+1:02}',fid,[fx,1.5,tz])
            connections.append(dict(id=f'line-{fid}-{tid}',from_asset_id=fid,to_asset_id=tid,approved=True,geometry_points_m=[[fx,8,-46],[fx,8,tz]],topology_version=VERSION))
            for b in range(2):
                bi=ti*2+b; bid=f'branch-{bi+1:02}'; bx=fx+(-16 if b==0 else 16)
                add(bid,'branch',f'Branch {bi+1:02}',tid,[bx,8,tz])
                add('pole-'+bid,'pole',f'Pole B{bi+1:02}',bid,[bx,0,tz])
                connections.append(dict(id=f'line-{tid}-{bid}',from_asset_id=tid,to_asset_id=bid,approved=True,geometry_points_m=[[fx,8,tz],[bx,8,tz]],topology_version=VERSION))
                for h in range(3):
                    hi=bi*3+h; hid=f'household-{hi+1:02}'
                    hp=[bx-9+h*9,1.7,tz+14]
                    add(hid,'household',f'Meter {hi+1:02}',bid,hp)
                    connections.append(dict(id=f'service-{hi+1:02}',from_asset_id=bid,to_asset_id=hid,approved=True,geometry_points_m=[[bx,8,tz],[hp[0],5,tz+10]],topology_version=VERSION))
    return assets, connections

ASSETS, CONNECTIONS = make_topology()
BY_ID = {a['id']:a for a in ASSETS}
CHILDREN = {a['id']:[b['id'] for b in ASSETS if b['parent_id']==a['id'] and b['meter_id']] for a in ASSETS}
SECTIONS = [a for a in ASSETS if a['kind'] in ('feeder','transformer','branch')]

def validate_cut(boundary, cut):
    # P0 supports the exact immediate downstream instrumented cut only.
    if len(cut) != len(set(cut)) or set(cut) != set(CHILDREN[boundary]):
        raise ValueError('Cut must cover immediate downstream meters exactly once; nested descendants are forbidden')
    return True

# P0 10-stream radial slice per PRD v5.0 Section 1 and Section 4:
# 1 feeder, 1 transformer, 2 branches, 6 households = 10 measurement streams.
P0_SLICE_ASSET_IDS = [
    'feeder-01',
    'transformer-02',
    'branch-03', 'branch-04',
    'household-07', 'household-08', 'household-09',
    'household-10', 'household-11', 'household-12'
]
