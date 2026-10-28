# luiss-cinemadb

Movie ticketing system for a cinema: MySQL database, Python command-line application, FastAPI + React web app, and embedding-based movie recommendations.

Databases & Big Data, LUISS. Group 7, ASql Roma.

## Repository layout

| Path | Contents |
| --- | --- |
| `ER_diagram.pdf` | ER diagram (source: `docs/er/ER_diagram.drawio`) |
| `schema.sql` | Tables, keys, constraints and indexes |
| `data.sql` | Synthetic test data |
| `queries.sql` | All SQL used by the app, including the five graded queries |
| `src/cinema/` | Core logic and the command-line application |
| `api/cinema_api/` | FastAPI backend for the web app |
| `web/` | React frontend |
| `pipeline/` | Embedding model selection experiments |
| `tests/` | pytest suite |
| `docs/adr/` | Architecture decision records |
| `GLOSSARY.md` | Domain vocabulary |

## Requirements

- MySQL >= 9.0 (the schema uses the `VECTOR` type), or Docker
- Python 3.12 with [uv](https://docs.astral.sh/uv/), or pip
- [bun](https://bun.sh/) for the web app

## Creating the database

TODO

## Populating the database

TODO

## Running the command-line application

TODO

## Running the web app

TODO

## Design assumptions

- An administrator never buys tickets. A user has exactly one role.
- Passwords are stored as bcrypt hashes. Demo credentials are listed below.
- The catalog has about 20-30 movies, more than the suggested 6-8, so recommendations are meaningful.
- TODO

## Booking transaction

TODO: implementation and how it is tested, including the concurrency test.

## Movie recommendations

TODO: movie information used, embedding model, similarity measure, selection of the top three. See `pipeline/` for the model comparison.

## Contributions

| Member | Contribution |
| --- | --- |
| Riccardo Palleschi | TODO |
| Silvia Monteleone | TODO |
| Lapo Chiaselotti | TODO |
| Claudio De Acutis | TODO |
| Luka Burmazevic | TODO |
| Mattia Galentino | TODO |
