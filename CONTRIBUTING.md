# Contributing

## Flow

-   Use the project board to coordinate and assign tasks
    -   Fill out the start date, assign yourself, and move it to "in-progress"
-   Create a new git branch named your feature / fix
-   Once you are done, create a [PR](#pull-requests-prs)
    -   Make sure your PR is well formatted and ready for review
-   A maintainer will get around to reviewing the PR

    -   If comments are made, address them or fix the code
    -   If approved, your branch will be squashed onto main

## Issues

Work in progress

## Code Standards

1. Maintain [Clean Code](https://github.com/Gatjuat-Wicteat-Riek/clean-code-book)

    - Take all below with a grain of salt
    - Write [self-documenting code](https://en.wikipedia.org/wiki/Self-documenting_code)
        - Use meaningful variable and function names.
    - Make short (and not excessively indented) functions
        - Split up long functions into shorter, single-purpose functions
    - Don't Repeat Yourself ([DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself))
        - Use helper functions and abstractions where necessary

2. Write It Thrice (WET)

    - Write it
        - Just get it down
        - Don’t worry about quality, elegance, or even correctness
        - The goal is to overcome inertia and produce something
    - Write it right
        - Make it work correctly
        - Fix the errors, make sure it meets requirements, and that it does what it’s supposed to do
    - Write it well
        - Refactor, polish, and optimize
        - Make it clean, efficient, elegant, and maintainable

# Pull Requests (PRs)

## PR Etiquette

1. Accomplish One Goal per PR

    - Do not tackle multiple objectives in a single PR
    - It makes understanding intent and hierarchies difficult when reviewing

2. Separate Features from Refactors

    - They accomplish two separate goals; see 1
    - If you notice a PR that would be helpful during development: note it down in section 6 of the PR and make an issue on it so we know to address it

3. Follow the PR Structure

    - On every PR you make, address every of the 6 parts of a PR ([notated below](#pr-structure))

## PR Structure

1. Summary of the Task

    - State the goal of this PR in one or two sentences
        - Keep it focused: what was the problem, and what does this solve?
        - Keep it high level; do not delve into implementation details
    - [Link the issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) being solved to this PR (if applicable)

2. List of Major Changes

    - Bullet point the key changes
        - Don't just describe files changed; describe conceptually what changed
        - Example: `Refactored UserService to handle null users.` not `Changed UserService.cs.`

3. Self-Review Before Submission

    - Read through your own diff.
      If something looks odd or half-baked, fix it before assigning reviewers
    - Make sure there are no excessive diffs (due to formatter differences, etc.), as they cause difficulties when reviewing
    - Ask yourself: If I saw this in someone else's PR, would I have questions?

4. Call Out Non-Obvious Changes

    - If you touched code outside the main task (cleanup, refactor, bug fix), point it out
    - Explain why you made the change; reviewers shouldn't have to guess

5. Testing Notes (if relevant)

    - Mention how you tested your changes
    - If there are edge cases reviewers should try, call them out

6. Impact Awareness / Future Work

    - Note if this PR introduces breaking changes, performance implications, or requires follow-up work
    - If it did not complete the entirety of the task that it is linked to, notate precisely what still needs to be completed
    - If you notice something useful outside of this PR's scope (a feature that could be expanded upon, additional fields that would be helpful, etc.), notate that as well, and optionally create and mention an issue based on it
