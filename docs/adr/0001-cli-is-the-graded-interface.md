# The CLI is the graded interface; the API and web app wrap the same core

The brief requires a Python command-line application with fixed client and administrator menus, and says a web interface is not required. We also want a web frontend, so all business logic (authentication, pricing, screening checks, the booking transaction, recommendations) lives in the modules under `src/`. The CLI (`main`, `client`, `admin`) and the FastAPI backend (`api`) are thin layers over it. No rule may be implemented only in the API or only in the CLI.
