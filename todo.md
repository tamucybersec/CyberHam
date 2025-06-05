# TODO

-   Migrate old data to SQLite
-   Make sure SQLite and Bot have no bugs
    -   Test and run commands for cyberham on the test server (sanity check)
    -   Test to see if the Dashboard is still working fine
-   Change to have attendance table (user_id mapped to code)
    -   Attend to FIXMEs
    -   Make a separate Test Object for use in testing so if other objects expand in scope the test objects don't have to constantly be updated
    -   Make sure Dashboard is still functioning (need to add extra page, change calculations and interfaces)
-   Change to have better data
    -   Make legacy compatible, meaning we save old data and can use if it we desire
    -   Add utils for parsing and formatting dates, it's getting ridiculous
    -   Move register to redirect you to the website (easier to create forms for)
    -   Huge revamp to Dashboard once all the new fields are added
    -   For authentication with the dashboard, just use a query parameter
        -   Log the access attempts (success and failure) for the dashboard as well
        -   Be able to generate auth tokens and revoke them for sponsors from UI
    -   Audit logs for admin-level commands

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
    -   Raises questions like where to store the static files
    -   Need to make sure to prepend files properly
