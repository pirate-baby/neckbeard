# Neckbeard.py

Are you tired of looking over _every single repo_ that gets posted in the AI circles, only to discover the "exciting new framework" is 3 commits and wrapper on the `openai` api?

Are you a grumpy-ass neckbeard that expects bare-minimum basic software best practices from a project before it starts releasing major versions on PyPi?

Are you constantly explaining to leadership why today's AI _shiny object_ is no more production-ready than the last dozen they wanted to pivot to, and you need to get back to coding real solutions?

Are you miffed that you missed a _really good_ library and rolled your own sub-par solution, because it was a diamond lost in the AI-hype rough?

Well then, `Neckbeard` is for you.

## Features

Neckbeard pulls down a given git repo (**only supports python right now!**) in a container, builds and analyzes it using a blend of interesting and not very scientific techniques, then generates a high-level review and score for the code _as software_.

**Note that I said "as software" above**.

`Neckbeard` is only concerned with the value/validity of github repos as they pertain to application software. There are lots of really interesting and valuable whitepapers on GitHub - but these are not projects or python packages that can be used to get work done. Whitepaper repos are essentially fancy book reports, yet the blurb about one in _TLDR AI_ or _Tech Brew_ will send the uninformed scampering.


## Installation

This is a docker-based runtime, so clone the repo and then do this:
```bash
# this will process the some-org/some-repo repo
docker run --rm neckbeard "https//github.com/some-org/some-repo"
```

## License

This project is licensed under the MIT License.


## What Is Measured

- `is_a_package`: is this set up as an installable package?
- `github_stats`:
    - `language`: primary language, should Python be for this to work.
    - `commits`: count of total commits all time
    - `newest_commit`: date and time of last commit
    - `oldest_commit`: date and time of first commit
- `summary`: an AI generated description based on the readme
- `codebase_size`: how big is the just the code in the project?
- `total_package_size`: how big is all of the project including all the deps?
- `immediate_dependencies`: the number of packages directly required by the project
  "total_number_of_dependencies_in_deps_chain": the number of packages in total in the chain, including those required by requirements
- `deepest_file_path`: how many directories down does this code go?
- `number_of_files`: count of files in the project
- `number_of_tests`: count of individual tests (methods/functions) in the project
- `package_tree_analysis_excluding_test_files`:
    - `count_of_errors_while_parsing`: how many times did ast crap out because the tree was too big/complex?
    - `max_depth`: largest single stack (count of frames)
    - `mean_average_depth`: average of all stacks (count of frames)
    - `max_depth_function`: which function is the big stack offender?
    - `standard_deviation`: what is a single SD for stack frame count across the code base?
    - `mean_average_depth_excluding_ones`: average for stacks with more than one frame
    - `standard_deviation_excluding_ones`: sd for stacks with more than one frame
- `package_complexity`:
    - `mean_average_complexity`: What is the cyclomatic mean score for the codebase?
    - `max_complexity_function`: The most complex function in the codebase
    - `max_complexity`: The highest complexity score in the whole code base
    - `percent_high_complexity`: what % of the codebase is > 30 cyclomatic
- `error_analysis`:
    - `issues`: The number of concerns found by pyFlakes (not Flake8 style!)
    - `errors`: How many times did pyFlakes error out? this happens when stacks are HUGE!

