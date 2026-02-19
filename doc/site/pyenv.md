# Python environments

Find Python version and the requirements file name corresponding to the job.

|                 | Job                  | Environment | Requirements            |
| --------------- | -------------------- | ----------- | ----------------------- |
| Data collection | GitHub Actions       | 3.12        | `requirements.txt`      |
|                 | Self-hosted          | 3.13        | `requirements.txt`      |
|                 | Get CPI              | 3.13        | `requirements.txt`      |
| Applications    | Fuel Price Dashboard | 3.13        | `requirements-dash.txt` |
|                 |                      |             |                         |

Based on Python version corresponding to the job from the table, create a Python virtual environment.

Let `$requirements` be the requirements file name from the table, run the following command.

```
pip install -r $requirements
```

**Activate the Python virtual environment before running any job.**

