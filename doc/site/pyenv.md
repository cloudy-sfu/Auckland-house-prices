# Python environments

There are multiple Python environments. The target is to create separate environments for data crawlers and visualization applications. Therefore, data crawlers can keep minimum environments without analysis packages, analyzing scripts don't need graphic drawing packages, and visualization applications don't need analysis packages.

All environments are listed below.

| Environment name                     | Python version | Requirements file path  |
| ------------------------------------ | -------------- | ----------------------- |
| Data collection - GitHub Actions[^1] | 3.12           | `requirements.txt`      |
| Data collection - Self-hosted        | 3.13           | `requirements.txt`      |
| Dashboard                            | 3.13           | `requirements-dash.txt` |

[^1]: GitHub Actions' environments are defined in workflow files. You don't need to manually manage environments for GitHub Actions.



## Install

Let Python version defined in the table above be `$python_version`.

Let requirements file path defined in the table above be `$req_path`.

Activate Python virtual environment.

Run the following command in terminal.

```
pip install -r $req_path
```

**Always activate one Python environment before executing any script.**

