# JMeter load test for Taller2-Backend

This folder contains a basic JMeter test plan to run load tests against the analysis endpoint.

Files:
- `test_plan.jmx`: JMeter Test Plan. Uses variables for host/port/project id/threads/ramp/loops.

Quick run (command line):

```powershell
# Example: run 50 threads ramping in 20s, 2 loops, target localhost:8000, project id 1
jmeter -n -t load_tests/jmeter/test_plan.jmx -l load_tests/jmeter/results.jtl -JHOST=localhost -JPORT=8000 -JPROJECT_ID=1 -JTHREADS=50 -JRAMP=20 -JLOOPS=2
```

Notes:
- Install JMeter locally (https://jmeter.apache.org/). Use `jmeter` CLI available in `bin` folder.
- Results are saved in `results.jtl`; open them with the JMeter GUI or convert to HTML report.
- To measure energy during the test, run the server with profiling/energy-monitoring enabled (see `app/services/energy_monitor.py`) and collect per-request metrics or run the analysis endpoint with `?profile=1` for profiling information.
