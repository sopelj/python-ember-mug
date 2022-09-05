# Usage

## In Python Project

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

### Using CLI interface

It can also be invoked as a module from command line as `python -m ember_mug --help`.
There are four options with different subsections. You can see them by specifying them before help. eg `python -m ember_mug poll --help`

Basic options:

| Command    | Use                                                                            |
|------------|--------------------------------------------------------------------------------|
| `discover` | Find/List all detected unpaired mugs in pairing mode                           |
| `find`     | Find *one* already paired mugs                                                 |
| `info`     | Connect to *one* mug and print its current state                               |
| `poll`     | Connect to *one* mug and print its current state and keep watching for changes |

![CLI Example](./images/cli-example.png)
