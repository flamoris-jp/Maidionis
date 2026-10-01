#include "maidionis/statistics.h"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace maidionis;
void check(bool b){if(!b)throw std::runtime_error("statistics assertion");}
int main(){try{
 check(sigmoid(0)==.5&&std::abs(sigmoid(1)-sigmoid(1,1))<1e-15);
 check(!percentile({},.5));check(*percentile({0,10,20,30},.25)==7.5);auto bound=wilson(0,10,1.96);check(bound.first==0&&bound.second>.27&&bound.second<.28);
 auto fit=fit_bernoulli_temperature({-2,2,-1,1},{false,true,true,false},.1,10,200,4,1e-6);check(fit.converged&&fit.fitted_loss<=fit.raw_loss);
 auto gate=select_gate({.2,.5,.8},{false,false,true},{.2,.5,.8},2,0,1,1.96);check(gate.enabled&&gate.support==3&&gate.threshold==.2);
 auto failed=select_gate({.2,.5,.8},{true,true,true},{.2,.5,.8},2,0,0,1.96);check(!failed.enabled);
 std::cout<<"statistics fixtures passed\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
