# Usage

To use Python Ember Mug in a project

```python
from ember_mug.scanner import find_mug, discover_mugs
from ember_mug.mug import EmberMug

# if first time with mug in pairing
mugs = await discover_mugs()
device = mugs[0]
# after paired you can simply use
device = await find_mug()
mug = EmberMug(device)
async with mug.connection() as con:
    print('Connected.\nFetching Info')
    await con.update_all()
    print(mug.formatted_data)
```
