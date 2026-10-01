#include "maidionis/contracts.h"
#include <iostream>
using namespace maidionis;
void check(bool value){if(!value)throw std::runtime_error("contract test assertion");}
template<class F>void rejects(F f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}check(failed);}
int main(){try {
  Json bounded={{"anyOf",Json::array({Json{{"type","integer"}}})},{"maximum",5}};
  validate_schema(5,bounded);rejects([&]{validate_schema(999,bounded);});
  Json closed={{"anyOf",Json::array({Json{{"type","object"}}})},{"required",{"x"}},
    {"properties",{{"x",{{"type","integer"}}}}},{"additionalProperties",false}};
  validate_schema(Json{{"x",1}},closed);
  rejects([&]{validate_schema(Json::object(),closed);});
  rejects([&]{validate_schema(Json{{"x",1},{"extra",2}},closed);});
  auto request=schema("request");check(request["$id"]=="maidionis.request.v1");
  rejects([&]{validate_record("request",Json::object());});
  rejects([&]{schema("../request");});rejects([&]{schema("not-compiled");});
  std::cout<<"compiled schema and anyOf contracts passed\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
