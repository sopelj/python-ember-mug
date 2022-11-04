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

It can also be run via command line either directly with `ember-mug --help` or as a module with `python -m ember_mug --help`
There are five options with different subsections. You can see them by specifying them before help. eg `ember-mug poll --help`

```bash
ember-mug discover  # Finds the mug in pairing mode for the first time
ember-mug poll  # fetches info and keeps listening for notifications
ember-mug get name target-temp  # Prints name and target temp of mug
ember-mug set --name "My mug" --target-temp 56.8  # Sets the name and target temp to specified values
```
Basic options:

| Command     | Use                                                                            |
|-------------|--------------------------------------------------------------------------------|
| `discover`  | Find/List all detected unpaired mugs in pairing mode                           |
| `find`      | Find *one* already paired mugs                                                 |
| `info`      | Connect to *one* mug and print its current state                               |
| `poll`      | Connect to *one* mug and print its current state and keep watching for changes |
| `get`       | Get the value(s) of one or more attribute(s) by name                           |
| `set`       | Set one or more values on the mug                                              |

![CLI Example](./images/cli-example.png)
