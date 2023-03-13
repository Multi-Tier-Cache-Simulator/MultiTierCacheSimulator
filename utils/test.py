from traces.trace_analysis.TraceDistribution import CSVTraceDistributions

filename = "C:/Users/gl_ai/OneDrive/Documents/multi_tier_cache_simulator/resources/dataset_jedi/eu.csv"
cSVTraceDistributions = CSVTraceDistributions(filename, "jedi_eu")
cSVTraceDistributions.distributions()
