#/usr/bin/env python
import redis
import sys

r = redis.StrictRedis(host='localhost', port=6379, db=0)
classes  = (R, B, S) =  ('Nova_VNF_Gold','Nova_VNF_Bronze','Nova_VNF_Silver')

for res in classes:
   print res +  "="  +  (r.get(res) or '0')

if 'cleanup' in sys.argv:
	for res in classes:
	   if res in sys.argv:
		r.set(res, 0)
		print "reset "+res


