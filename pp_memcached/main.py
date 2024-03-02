import json
import random
from memcache import Client

mclient = Client([("127.0.0.1", 11211)], 1, cache_cas=True)

# print(json.dumps(mclient.get_stats(), indent=2, sort_keys=True))

li = []

rnumb = random.randint(10001, 999999)
# adds only if not exists
print(mclient.add(str(rnumb).encode(),rnumb))
print(mclient.add(str(rnumb).encode(),rnumb))
# unconditional set
print(mclient.set(str(rnumb).encode(),rnumb))
print(mclient.set(str(rnumb+1).encode(),rnumb))
print(mclient.get(str(rnumb)))
print(mclient.get_multi(str(rnumb))) # wrong, gets empty {}
print(mclient.get_multi([str(rnumb),str(rnumb+1)]))
print(mclient.set ([str(rnumb),str(rnumb+1)]))

exit(0)

for each in range(1, 101):
    rnumb = random.randint(10001, 999999)
    li.append(rnumb)
    print(mclient.set(str(rnumb).encode(),rnumb))
    print(mclient.add(str(rnumb).encode(),rnumb))
    print(mclient.add(str(rnumb).encode(),rnumb,noreply=True))
    print(mclient.get(str(rnumb).encode(),00000))
    print(mclient.get(str(rnumb+1).encode(),00000))
    print(mclient.get_multi(li[:5]))
    print(mclient.get_multi(li[5:15]))
    print(mclient.get_multi(li[:-5]))


# print("adding existing key",mclient.add(str(rnumb),rnumb))
# print("adding new key",mclient.add(str(rnumb+1),rnumb+1))
