#pragma once
#include <vector>
#include <optional>
#include <utility>
namespace maidionis {
double sigmoid(double logit,double temperature=1);
std::optional<double> percentile(std::vector<double>,double p);
std::pair<double,double> wilson(size_t errors,size_t support,double z);
struct TemperatureFit {double temperature,raw_loss,fitted_loss;size_t support;bool converged,boundary;};
TemperatureFit fit_bernoulli_temperature(const std::vector<double>& logits,const std::vector<bool>& targets,
 double minimum,double maximum,size_t iterations,size_t minimum_support,double tolerance);
struct Gate {bool enabled=false;double threshold=0,risk_upper=1,coverage=0;size_t support=0;};
Gate select_gate(const std::vector<double>& scores,const std::vector<bool>& errors,const std::vector<double>& grid,
 size_t minimum_support,double minimum_coverage,double maximum_risk,double z);
}
