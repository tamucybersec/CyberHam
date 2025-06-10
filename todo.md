# TODO

-   Change to have attendance table (user_id mapped to code)

    -   Create last 2 tests
    -   Double check functions respect the semester and year when it makes sense to
    -   Make sure Dashboard is still functioning (need to add extra page, change calculations, interfaces, and schemas)
        -   Make sure to update schemas for events

-   Prune

    -   Go through events and consolidate legacy ones into modern ones (i.e. change their name so the data looks better) (really simple using the dashboard with the tables!)
    -   Delete obvious test data

-   Change to have better data

    -   Move register to redirect you to the website (easier to create forms for)
    -   Huge revamp to Dashboard once all the new fields are added
    -   For authentication with the dashboard, just use a query parameter
        -   Be able to generate auth tokens and revoke them for sponsors from UI

-   Actually run it on the server
    -   Need to generate certificates for https
-   Document full setup process from scratch
    -   Important for onboarding

```python
class User(TypedDict):
    user_id: int
    name: str
-   points: int
-   attended: int
+   grad_semester: Literal["spring", "summer", "fall", "winter"]
    grad_year: int
    email: str
+   join_date: str
+   active_date: str
```

# Future Projects

-   Migrate website to be served statically from api
    -   Is this even a worthwhile change?
    -   Need to update DNS
    -   Raises questions like where to store the static files
    -   Need to make sure to prepend files properly
-   Add error checking
    -   Currently the app has no error checking, meaning nay rouge error from sqlite commands can break the entire app
    -   Obviously this isn't good, so we need to research where errors can occur and how to properly recover from them (particularly for discord commands)
-   Proper logging
    -   Determine if the current logging actually does anything
    -   Log when commands with elevated privileged rights are used and by who
    -   Log the access attempts (success and failure) for the dashboard
-   Unit tests for discord bot
    -   We know the backend works because of unit tests, but discord command can currently only be tested by hand
    -   We need to come up with an effective way to test the commands so we can quickly tell if something breaks
-   Better error system for backend
    -   Instead of just returning a str, we should return a str marked as err so we know immediately and easily if something went wrong when running the command
    - Off the top of my head, a wrapper class or something would get the job done
-   Fix the final 6 warnings from GoogleClient
    -   Refactor GoogleClient to have helper functions with clear intentions
