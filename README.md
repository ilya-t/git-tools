# Quickstart
Run `init.sh` to setup python dependencies.
Optionally put `alias.sh` to `~/.profile`, 
**(note that examples are based on these aliases!)**

# Builder
Builder is a tool that can build complex hierarchy of branches 
according to so called "map" which is described by yaml config file.
Builder is convenient when you're dealing with chain of branches. 
Here's a quick sample of that. 

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
- origin/master: # basement branch, on top of which all other will be assembled when its head gets changed
    - feature_x_branch:            # first branch to assemble on top of 'master'
      - commit: feature_x_branch~0 # that consists single commit
        message: "feature POC"     # with specified message
        
    - tests_for_x:                                  # second branch that will be assembled on top of 'feature_x_branch'
      - message: "cover feature x with smoke tests" # 'commit' it will be resolved automatically as `commit: tests_for_x~1`
      - message: "add extra test for test-case #42" # another omitted 'commit', resolves as `commit: tests_for_x~0`
    - bugfixes_for_x:                      # third branch that will be assembled on top of 'tests_for_x' 
      - message: "bugfix of test-case #17" # 

  - feature_2~0 # third branch 'feature_2' in short assemble form:
                # consists of its head~0 commit and will be assembled on top of 'feature_1'```
```

If something went wrong you may check `assembly.log` file that keeps references to all previous commits.
See another samples:
- [config for rebuilding above single branch](./tests/multi_base_workspace.yml)
- [config for rebuilding with multple basement branches](./tests/single_base_workspace.yml)