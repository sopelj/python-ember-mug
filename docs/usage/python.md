## In order to

```python
from ember_mug.scanner import find_device, discover_devices
from ember_mug.utils import get_model_info_from_advertiser_data
from ember_mug.mug import EmberMug

# if first time with mug in pairing
devices = await discover_devices()

# after paired you can simply use
device, advertisement = await find_device()
model_info = get_model_info_from_advertiser_data(advertisement)
mug = EmberMug(device, model_info)
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
