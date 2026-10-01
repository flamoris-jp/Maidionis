#include "maidionis/contracts.h"
#include <openssl/sha.h>
#include <fstream>
#include <iomanip>
#include <set>
#include <regex>
#include <cmath>
#include <charconv>

namespace maidionis {
std::string compiled_build_digest(){return MAIDIONIS_BUILD_DIGEST;}
namespace {
void require(bool ok,const char* message) { if(!ok) throw std::invalid_argument(message); }
std::string key(const Json& r) { return r.at("id").get<std::string>()+"\n"+r.at("version").get<std::string>(); }
size_t unicode_length(const std::string& s) { size_t n=0;for(unsigned char c:s)if((c&0xc0)!=0x80)++n;return n; }
bool strict_equal(const Json& a,const Json& b) {
  if(a.is_boolean()!=b.is_boolean() || a.is_number()!=b.is_number() || a.is_number_float()!=b.is_number_float())return false;
  return a==b;
}
}
Json parse_json(const std::string& raw,size_t maximum) {
  require(raw.size()<=maximum,"JSON byte limit");
  // nlohmann otherwise coerces oversized integer literals to floating point.
  bool quoted=false,escaped=false;
  for(size_t i=0;i<raw.size();++i){char c=raw[i];
    if(quoted){if(escaped)escaped=false;else if(c=='\\')escaped=true;else if(c=='"')quoted=false;continue;}
    if(c=='"'){quoted=true;continue;}
    if(c=='-'||(c>='0'&&c<='9')){size_t start=i;while(i+1<raw.size()&&(std::isdigit(static_cast<unsigned char>(raw[i+1]))||raw[i+1]=='.'||raw[i+1]=='e'||raw[i+1]=='E'||raw[i+1]=='+'||raw[i+1]=='-'))++i;
      auto literal=raw.substr(start,i-start+1);if(literal.find_first_of(".eE")==std::string::npos){std::errc error;
        if(literal[0]=='-'){int64_t value;error=std::from_chars(literal.data(),literal.data()+literal.size(),value).ec;}
        else {uint64_t value;error=std::from_chars(literal.data(),literal.data()+literal.size(),value).ec;}
        require(error==std::errc{},"integer overflow");}}
  }
  size_t count=0; std::vector<std::set<std::string>> keys;
  auto cb=[&](int depth,Json::parse_event_t event,Json& value) {
    require(depth<=32,"JSON depth limit");
    if(event==Json::parse_event_t::object_start)keys.emplace_back();
    if(event==Json::parse_event_t::object_end)keys.pop_back();
    if(event==Json::parse_event_t::key) {
      const auto k=value.get<std::string>();require(k.size()<=256&&!keys.empty()&&keys.back().insert(k).second,"invalid JSON key");
      require(++count<=65536,"JSON value limit");
    }
    if(event==Json::parse_event_t::value || event==Json::parse_event_t::object_start || event==Json::parse_event_t::array_start)
      require(++count<=65536,"JSON value limit");
    if(value.is_number_float())require(std::isfinite(value.get<double>()),"nonfinite JSON");
    return true;
  };
  return Json::parse(raw,cb,true,false);
}
std::string canonical(const Json& j) { return j.dump(-1,' ',false,Json::error_handler_t::strict)+"\n"; }
std::string sha256(const std::string& raw) {
  unsigned char out[SHA256_DIGEST_LENGTH]; SHA256(reinterpret_cast<const unsigned char*>(raw.data()),raw.size(),out);
  std::ostringstream s;for(auto c:out)s<<std::hex<<std::setw(2)<<std::setfill('0')<<static_cast<int>(c);return s.str();
}
std::string read_file(const std::filesystem::path& p,size_t cap) {
  require(!std::filesystem::is_symlink(p)&&std::filesystem::is_regular_file(p),"not a regular file");
  require(std::filesystem::file_size(p)<=cap,"file byte limit");
  std::ifstream f(p,std::ios::binary);require(bool(f),"read failure");
  std::string bytes;char buffer[8192];while(f){f.read(buffer,sizeof buffer);bytes.append(buffer,f.gcount());require(bytes.size()<=cap,"file byte limit");}
  require(f.eof(),"read failure");return bytes;
}
void validate_schema(const Json& v,const Json& s) {
  static const std::set<std::string> allowed={"$schema","$id","type","properties","required","additionalProperties","items",
   "minItems","maxItems","uniqueItems","minLength","maxLength","pattern","minimum","maximum","enum","const","anyOf"};
  for(auto it=s.begin();it!=s.end();++it)require(allowed.contains(it.key()),"unsupported schema keyword");
  if(s.contains("anyOf")){for(const auto& a:s["anyOf"]){try{validate_schema(v,a);return;}catch(const std::invalid_argument&){}}throw std::invalid_argument("schema alternatives mismatch");}
  if(s.contains("type")) {
    auto t=s["type"].get<std::string>();bool match=(t=="object"&&v.is_object())||(t=="array"&&v.is_array())||
      (t=="string"&&v.is_string())||(t=="integer"&&v.is_number_integer())||(t=="number"&&v.is_number())||
      (t=="boolean"&&v.is_boolean())||(t=="null"&&v.is_null());require(match,"schema type mismatch");
  }
  if(s.contains("const"))require(strict_equal(v,s["const"]),"schema const mismatch");
  if(s.contains("enum")){bool ok=false;for(const auto& x:s["enum"])ok|=strict_equal(v,x);require(ok,"schema enum mismatch");}
  if(v.is_object()) {
    auto props=s.value("properties",Json::object());
    for(const auto& k:s.value("required",Json::array()))require(v.contains(k.get<std::string>()),"missing schema field");
    for(auto it=v.begin();it!=v.end();++it){if(props.contains(it.key()))validate_schema(it.value(),props[it.key()]);else require(s.value("additionalProperties",true),"unknown schema field");}
  } else if(v.is_array()) {
    require(v.size()>=s.value("minItems",size_t(0))&&v.size()<=s.value("maxItems",size_t(65536)),"array length");
    std::set<std::string> unique;for(const auto& x:v){if(s.value("uniqueItems",false))require(unique.insert(canonical(x)).second,"duplicate item");if(s.contains("items"))validate_schema(x,s["items"]);}
  } else if(v.is_string()) {
    auto str=v.get<std::string>();auto n=unicode_length(str);require(n>=s.value("minLength",size_t(0))&&n<=s.value("maxLength",size_t(4*1024*1024)),"string length");
    if(s.contains("pattern"))require(std::regex_search(str,std::regex(s["pattern"].get<std::string>())),"string pattern");
  } else if(v.is_number()) {
    const double x=v.get<double>();require(std::isfinite(x),"nonfinite number");
    if(s.contains("minimum"))require(x>=s["minimum"].get<double>(),"number minimum");
    if(s.contains("maximum"))require(x<=s["maximum"].get<double>(),"number maximum");
  }
}
Json schema(const std::string& name) { safe_path(name);return parse_json(read_file(std::filesystem::path(MAIDIONIS_SCHEMA_DIR)/(name+".schema.json"),4*1024*1024),4*1024*1024); }
void validate_record(const std::string& name,const Json& v){validate_schema(v,schema(name));}
void safe_path(const std::string& path) {
  require(!path.empty()&&path.size()<=1024&&path.front()!='/'&&path.find('\\')==std::string::npos&&path.find('\0')==std::string::npos,"invalid relative path");
  std::istringstream s(path);std::string part;while(std::getline(s,part,'/'))require(!part.empty()&&part!="."&&part!="..","invalid relative path");
  require(path.back()!='/',"invalid relative path");
}
RegistryBuilder::RegistryBuilder(std::string build){require(std::regex_match(build,std::regex("[a-f0-9]{64}")),"build digest");registry_.build_=std::move(build);}
void RegistryBuilder::add_schema(const Json& ref,const Json& definition){require(!frozen_,"registry frozen");require(sha256(canonical(definition))==ref.at("sha256").get<std::string>(),"schema binding");require(registry_.schemas_.emplace(key(ref),std::make_pair(ref,definition)).second,"duplicate schema");}
void RegistryBuilder::add_operation(const Json& ref,const Json& config,std::function<void(const Json&)> operation){require(!frozen_&&bool(operation),"operation registration");require(sha256(canonical(config))==ref.at("config_digest").get<std::string>(),"operation binding");operation(config);require(operations_.emplace(key(ref),std::make_pair(ref,operation)).second,"duplicate operation");}
Registry RegistryBuilder::freeze(const Json& descriptor) {
  require(!frozen_,"registry frozen");validate_record("specialization",descriptor);
  for(const auto& field:{"input_schema","target_schema","output_schema","diagnostics_schema"}) {
    const auto& ref=descriptor.at(field);if(ref.is_null())continue;auto it=registry_.schemas_.find(key(ref));require(it!=registry_.schemas_.end()&&it->second.first==ref,"missing schema binding");
  }
  auto refs=descriptor["heads"];for(const auto& field:{"input_codec","output_codec","architecture","objective","numerical_compatibility"})refs.push_back(descriptor[field]);
  for(const auto& ref:refs){auto it=operations_.find(key(ref));require(it!=operations_.end()&&it->second.first==ref,"missing operation binding");}
  registry_.descriptor_=descriptor;frozen_=true;return registry_;
}
void Registry::payload(const std::string& field,const Json& value) const {const auto& ref=descriptor_.at(field);if(ref.is_null()){require(value.is_null(),"unexpected diagnostics");return;}validate_schema(value,schemas_.at(key(ref)).second);}
void Registry::request(const Json& v) const {
  validate_record("request",v);for(const auto& k:{"specialization_id","specialization_version","task_id","task_version"})require(v[k]==descriptor_[k],"request identity");
  require(v["payload_schema"]==descriptor_["input_schema"],"request schema");payload("input_schema",v["payload"]);
}
void Registry::sample(const Json& v) const {
  validate_record("sample",v);for(const auto& k:{"specialization_id","specialization_version","task_id","task_version","input_schema","target_schema"})require(v[k]==descriptor_[k],"sample identity");
  payload("input_schema",v["input"]);payload("target_schema",v["target"]);
}
void Registry::result(const Json& v,const Json& request,const std::string& artifact) const {
  validate_record("result",v);for(const auto& k:{"request_id","context_ref","specialization_id","specialization_version","task_id","task_version"})require(v[k]==request[k],"result identity");
  require(v["artifact_digest"]==artifact&&v["payload_schema"]==descriptor_["output_schema"],"result binding");
  if(v["status"]=="ok"){require(v["error"].is_null(),"ok error");payload("output_schema",v["payload"]);payload("diagnostics_schema",v["diagnostics"]);}
  else if(v["status"]=="abstain"){require(v["error"].is_null()&&v["payload"].is_null(),"abstention payload");payload("diagnostics_schema",v["diagnostics"]);}
  else require(v["payload"].is_null()&&v["diagnostics"].is_null()&&!v["error"].is_null(),"error payload");
}
}
