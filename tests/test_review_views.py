import math
import unittest
from hafusion.views import ensure_diagonal_views


class ReviewViews(unittest.TestCase):
    def test_default_coverage_and_repeated_exports(self):
        views = ensure_diagonal_views([], [140,244,140])
        self.assertEqual({v['id'] for v in views}, {q+'_'+m for q in ('se','sw','ne','nw') for m in ('day','night')})
        self.assertEqual(views, ensure_diagonal_views(views, [140,244,140]))
        self.assertEqual(len({(tuple(v['target']),v['spanX'],v['spanZ'],v['width'],v['height']) for v in views}), 1)
        for v in views:
            dx,dy,dz=[v['eye'][i]-v['target'][i] for i in range(3)]
            self.assertAlmostEqual(abs(dx),abs(dz))
            q=v['id'].split('_')[0]
            self.assertEqual(dx>0,q in ('se','ne'))
            self.assertEqual(dz>0,q in ('se','sw'))

    def test_detail_crop_preserved_but_not_used_for_coverage(self):
        detail=dict(id='cut',eye=[10,2,10],target=[0,0,0],spanX=3,cutX=5)
        original=[dict(detail)]
        views=ensure_diagonal_views(original,[12,200,80],night=False)
        self.assertEqual(original,[detail])
        self.assertEqual(views[0],detail)
        for v in views[1:]:
            self.assertNotIn('cutX',v)
            # Project every bbox corner and verify it fits the exported frame.
            eye=v['eye'];t=v['target'];d=[eye[i]-t[i] for i in range(3)]
            length=math.sqrt(sum(n*n for n in d));horizontal=math.hypot(d[0],d[2])
            for x in (0,12):
                for y in (0,200):
                    for z in (0,80):
                        p=[x-t[0],y-t[1],z-t[2]]
                        px=(d[2]*p[0]-d[0]*p[2])/horizontal
                        py=p[1]*horizontal/length-(d[0]*p[0]+d[2]*p[2])*d[1]/(horizontal*length)
                        self.assertLess(abs(px),v['spanX']/2)
                        self.assertLess(abs(py),v['spanZ']/2)

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):ensure_diagonal_views([],[0,2,3])
        with self.assertRaises(ValueError):ensure_diagonal_views([{'id':'same'},{'id':'same'}],[1,2,3])

if __name__=='__main__':unittest.main()
