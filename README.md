# Quickstart
Run `init.sh` to setup python dependencies.
Optionally put `alias.sh` to `~/.profile`, 
**(note that examples are based on these aliases!)**

# Builder
Builder is a tool that can build complex hierarchy of branches 
according to so called "map" which is described by yaml config file.
Builder is convenient when you're dealing with chain of branches 
which contents can be amended. Here's a quick sample of that. 

You're working under both `feature_1` branch and under `feature_2` branch
that depends on `feature_1`.  At some point you understand that you need
`feature_1` to be rebased onto fresh master. Once you've rebased `feature_1`
your `feature_2` is no longer based on `feature_1` and rebase above `feature_1`
 will only bring you conflicts.

With builder such rebasement of multiply chained branches can be done in a very
convenient and conflictless way:
```sh
git fetch origin master
git-build branch_map.yml
```

where `branch_map.yml` may look like this:
```yml
- origin/master: # basement branch, on top of which all other will be assembled
  - feature_1: # first branch to assemble on top of 'master'
    - feature_1~2 # that consists of 3 commits
    - feature_1~1 # which applied one by one
    - feature_1~0 # from oldest to newest

  - feature_2~0 # second branch 'feature_2' in short assemble form: 
                # consists of its head~0 commit and will be assembled on top of 'feature_1' 
```

If something went wrong you may check `assembly.log` file that keeps references to all previous commits.
See also another map [sample](./tests/multi_base_workspace.yml)