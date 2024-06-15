```python
from ember_mug.scanner import find_mug, discover_mugs
from ember_mug.mug import EmberMug

# if first time with mug in pairing
mugs = await discover_mugs()
device = mugs[0]
# after paired you can simply use
device = await find_mug()
mug = EmberMug(device)
await mug.update_all()
print(mug.data.formatted)
await mug.disconnect()

# You can also use connection as a context manager
# if you want to ensure connection before starting and cleanup on exit
async with mug.connection():
    print('Connected.\nFetching Info')
    await mug.update_all()
    print(mug.data.formatted)
```
