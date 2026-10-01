#include "maidionis/statistics.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace maidionis {
namespace {void need(bool b){if(!b)throw std::invalid_argument("statistical input");}}
double sigmoid(double x,double t){need(std::isfinite(x)&&std::isfinite(t)&&t>0);x/=t;return x>=0?1/(1+std::exp(-x)):std::exp(x)/(1+std::exp(x));}
std::optional<double> percentile(std::vector<double> x,double p){need(std::isfinite(p)&&p>=0&&p<=1);for(auto v:x)need(std::isfinite(v));if(x.empty())return {};std::sort(x.begin(),x.end());double at=(x.size()-1)*p;size_t lo=at,hi=std::min(lo+1,x.size()-1);return x[lo]+(x[hi]-x[lo])*(at-lo);}
std::pair<double,double> wilson(size_t e,size_t n,double z){need(n>0&&e<=n&&std::isfinite(z)&&z>0);double p=double(e)/n,z2=z*z,d=1+z2/n,c=(p+z2/(2*n))/d,w=z*std::sqrt(p*(1-p)/n+z2/(4*double(n)*n))/d;return {std::max(0.,c-w),std::min(1.,c+w)};}
TemperatureFit fit_bernoulli_temperature(const std::vector<double>& x,const std::vector<bool>& y,double lo,double hi,size_t iterations,size_t support,double tolerance){
 need(!x.empty()&&x.size()==y.size()&&x.size()>=support&&support>0&&x.size()<=1000000&&std::isfinite(lo)&&std::isfinite(hi)&&lo>=.001&&lo<1&&hi>1&&hi<=100&&iterations>0&&iterations<=10000&&std::isfinite(tolerance)&&tolerance>0&&tolerance<=1);
 for(auto v:x)need(std::isfinite(v)&&std::abs(v)<=1e6);
 auto loss=[&](double t){double sum=0;for(size_t i=0;i<x.size();++i){double v=x[i]/t;sum+=std::max(v,0.)-v*y[i]+std::log1p(std::exp(-std::abs(v)));}return sum/x.size();};
 const double minimum=lo,maximum=hi,phi=(std::sqrt(5.)-1)/2;
 for(size_t i=0;i<iterations&&hi-lo>tolerance;++i){double a=hi-phi*(hi-lo),b=lo+phi*(hi-lo);if(loss(a)<=loss(b))hi=b;else lo=a;}
 double t=(lo+hi)/2;double raw=loss(1),fit=loss(t);if(fit>raw){t=1;fit=raw;}
 return {t,raw,fit,x.size(),hi-lo<=tolerance,t-minimum<=2*tolerance||maximum-t<=2*tolerance};
}
Gate select_gate(const std::vector<double>& scores,const std::vector<bool>& errors,const std::vector<double>& grid,size_t minimum,double coverage,double risk,double z){
 need(!scores.empty()&&scores.size()==errors.size()&&scores.size()<=1000000&&!grid.empty()&&grid.size()<=10000&&minimum>0&&std::isfinite(coverage)&&coverage>=0&&coverage<=1&&std::isfinite(risk)&&risk>=0&&risk<=1);
 for(auto x:scores)need(std::isfinite(x));Gate best;
 auto thresholds=grid;std::sort(thresholds.begin(),thresholds.end());need(std::adjacent_find(thresholds.begin(),thresholds.end())==thresholds.end());
 for(auto t:thresholds){need(std::isfinite(t));size_t n=0,e=0;for(size_t i=0;i<scores.size();++i)if(scores[i]>=t){++n;e+=errors[i];}
   if(n<minimum||double(n)/scores.size()<coverage)continue;auto upper=wilson(e,n,z).second;
   // Max coverage, then smallest threshold, explicit positive boundary tie.
   if(upper<=risk&&(!best.enabled||n>best.support))best={true,t,upper,double(n)/scores.size(),n};}
 return best;
}
}
