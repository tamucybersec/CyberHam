# TODO

-   Migrate old data to SQLite
    -   Write replace and backup functions in sqlite file
-   Make sure SQLite and Bot have no bugs
    -   Test and run commands for cyberham on the test server (sanity check)
    -   Test to see if the Dashboard is still working fine
-   Change to have attendance table (user_id mapped to code)
    -   Attend to FIXMEs
    -   Make a separate Test Object for use in testing so if other objects expand in scope the test objects don't have to constantly be updated
    -   Make sure Dashboard is still functioning (need to add extra page, change calculations and interfaces)
        -   Make sure to update schemas for events
-   Change to have better data
    -   Make legacy compatible, meaning we save old data and can use if it we desire
    -   Add utils for parsing and formatting dates, it's getting ridiculous
    -   Move register to redirect you to the website (easier to create forms for)
    -   Huge revamp to Dashboard once all the new fields are added
    -   For authentication with the dashboard, just use a query parameter
        -   Be able to generate auth tokens and revoke them for sponsors from UI
    -   Audit logs for admin-level commands
-   Actually run it on the server
    -   Need to generate certificates for https
-   Document full setup process from scratch
    -   Important for onboarding

```python
class User(TypedDict):
    user_id: int
    name: str
    points: int
    attended: int
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
