# TODO

-   Better UX if register completes and your session expires

-   Document full setup process from scratch

    -   Important for onboarding

# Up Next

-   Add individual user profile viewer so you can see all points, attendance, and other stats all in one spot

    -   In tables, for the cell on user_id, make it so that hovering on it shows their name like a little card and some quick info about them, and clicking the user_id brings you to the profile page
    -   individual attendance per category stats
    -   easily add notes here
        -   on conflict "this has been updated, please refresh"
    -   view resume with click

-   Add individual event analysis (same line as individual profile page, just so it's easy to see stats for a specific event)

-   Integrate old data for [Fall 2023](https://drive.google.com/drive/u/1/folders/1OcKWpQhGeNXsxUbvmfBrgTJcGy5fYCvH) and [Spring 2024](https://drive.google.com/drive/u/1/folders/1J-eDLJycZk1csvFQt2TjY9m5mAFsEN1-)

-   Loading indicator when logging in to dashboard

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
    -   Off the top of my head, a wrapper class or something would get the job done
    -   Use apis/google_apis get_events as a reference - nice descriptive errors that get returned all the way back to the bot and eventually displayed to the user of the command so they know what went wrong
-   Fix the final 6 warnings from GoogleClient
    -   Refactor GoogleClient to have helper functions with clear intentions
-   Clean up some test cases by storing the model in a variable instead of calling the function a million times
-   Joint statistics
    -   Be able to view multiple different event categories overlaid upon each other in the graph for attendance over time
-   Sponsor dashboard time selection
    -   Be able to choose the time frame from which you'd like to view the data
-   Clean up bot commands
    -   With the addition of the dashboard, some commands have become obsolete (create event)
    -   We don't want to maintain the same logic in multiple places (especially in discord where it's much harder to create forms) so we should reduce the number of places that have duplicate functionality when possible
    -   Ideally, the dashboard is the go-to place for management and the discord bot is only used by users or for discord-specific commands (list importing events)
-   More secure token storage
-   Make dates more precise like exact times so we can triangulate when and why a person registered, etc. (red hat academy, informational?)
-   Security
    -   Store a secure cookie using fastapi (1 hour) for the login token
    -   Read the cookie to see if we can bypass login
    -   Logout button on sidebar to delete cookie and redirect to login
-   Automatically distribute tokens to officers by dming people
-   Integrate [TAMU SSO](https://it.tamu.edu/services/accounts-and-id-management/authentication-authorization/netid-integration/)
-   Move the registration validation to a better location, it was chosen in haste
-   Make it so that officers can upload photos to some place (folder? google drive? dashboard?) and then they show up on the website home page
-   RSVP table for events:
    -   code, user_id, response (yes, no, maybe)
-   Schema super admin page
    -   Outlines current database schema and marks whether they have an interface on the frontend or not
    -   Maybe also explanation of what the tables do
    -   Has a download db button
-   Joins over time by year or month graph (maybe just by semester)
-   Active members by semester graph
-   Resume verification page
    -   Shows log of resumes that have been uploaded, sorted by time
    -   Have a button to view, approved, and reject (reject will delete the file)
    -   See which resumes have already been approved
    -   If we really don't want make a separate table for resumes and since we use the modified metadata for upload date, we can set a flag or something like \* in the front of the resume_format in the users table to denote approved
-   Some way to tell in register if they have already submitted a resume
-   Search defaults (pass in a column to be the default search column in the data tables)
-   Develop some system so we can easily display items nicely in forms and tables but send them to the backend in the correct version
    -   i.e. semesters capitalized and boolean values as true or false
    -   It would be very annoying to have different types for just the frontend and backend so ideally this is just a thing we can attach to forms and tables to transform values
-   Any idea on how to clean up the imports for python?
    -   I don't main python so I don't know the best practices
-   Make it obvious that register also updates your information
