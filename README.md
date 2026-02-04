# Auckland house prices

Price assessment models for houses in Auckland, New Zealand

![](https://shields.io/badge/dependencies-Python_3.13-blue)
![](https://shields.io/badge/dependencies-trademe.co.nz-blue)



## Install

Create and activate a Python 3.13 virtual environment.

Run the following command.

```
pip install -r requirements.txt
```

Create a PostgreSQL 17 database in [Neon](https://neon.com/) database, or your own PostgreSQL database.

Run `database_schema.sql` in database console to mock the database schema.

Include the following variables into environment variables.

| Variable | Description                                                  |
| -------- | ------------------------------------------------------------ |
| NEON_DB  | Connection string to Neon database. If using other database, set to connection string of your own PostgreSQL database. |

