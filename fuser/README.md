# Fuse several UM-Bridge calls into one

## Features
1. Wait until N model evaluation request have arrived.
2. Accumulate all parameters in a list of parameters.
3. Query the fused server with the list of parameters.
4. Return the correct results to each original request.

## Setup
We evaluate `k` different models `f: R^n -> R^m`, by evaluatint `g:R^(k x n) -> R^(k x m)`.

You can set the variables in `Fuser.cpp`:
* `k` = NumberOfFusedSimulations.
* `n` = NumberOfInputs.
* `m` = NumberOfOutputs.

You can specify the `OutwardPort`. This is the port, at which users can query the fuser as if it was a normal model evaluator for `f`.
The `ForwardPort` specifies the port of the fused server, which evaluates `g`.

## Todos
We do not consider the config variable yet.
