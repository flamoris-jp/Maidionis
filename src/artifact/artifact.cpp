#include "maidionis/artifact.h"
#include <sys/resource.h>
#include <set>
#include <algorithm>
namespace maidionis {
namespace {
void need(bool b,const char* s){if(!b)throw std::invalid_argument(s);}
Json sorted_tensors(Json a){std::sort(a.begin(),a.end(),[](const auto& x,const auto& y){return x["name"]<y["name"];});return a;}
size_t parameter_count(const Json& entries){size_t total=0;std::set<std::string> names;for(const auto& e:entries){need(names.insert(e["name"].get<std::string>()).second,"tensor duplicate");size_t n=1;for(auto dim:e["shape"]){auto d=dim.get<size_t>();need(d>0&&d<=30000000/n,"tensor product overflow");n*=d;}need(n<=30000000-total,"parameter total bound");total+=n;}return total;}
void has_digest(const Files& files,const std::string& digest){bool found=false;for(const auto& [p,b]:files)found|=sha256(b)==digest;need(found,"component binding missing");}
}
Json expected_tensor_inventory(const ModelConfig& c){
 c.validate();Json out=Json::array();auto tensor=[&](const std::string& n,std::vector<int64_t> s){out.push_back({{"name",n},{"dtype","float32"},{"shape",s},{"role","parameter"}});};
 auto linear=[&](const std::string& n,int64_t in,int64_t width){tensor(n+".weight",{width,in});tensor(n+".bias",{width});};
 if(c.kind=="dense")linear("projection",c.input_width,c.hidden_width);
 else {tensor("embedding.weight",{c.vocabulary,c.hidden_width});if(c.kind=="pooled")linear("projection",c.hidden_width,c.hidden_width);
 else {tensor("positions.weight",{c.max_length,c.hidden_width});tensor("segments.weight",{4,c.hidden_width});
  for(int64_t i=0;i<c.layers;++i){auto p="encoder.layers."+std::to_string(i);tensor(p+".self_attn.in_proj_weight",{3*c.hidden_width,c.hidden_width});tensor(p+".self_attn.in_proj_bias",{3*c.hidden_width});
   linear(p+".self_attn.out_proj",c.hidden_width,c.hidden_width);linear(p+".linear1",c.hidden_width,c.ffn_width);linear(p+".linear2",c.ffn_width,c.hidden_width);
   for(const auto& n:{"norm1","norm2"}){tensor(p+"."+n+".weight",{c.hidden_width});tensor(p+"."+n+".bias",{c.hidden_width});}}}}
 linear("output",c.hidden_width,c.output_width);return sorted_tensors(out);
}
std::string evaluated_component_digest(const Files& files){Files components;const std::set<std::string> excluded={"manifest.json","training.json","model-card.json","evaluation-registration.json","evaluation-report.json","evaluation-summary.json"};
 for(const auto& [p,b]:files)if(!excluded.contains(p))components.emplace(p,b);return sha256(canonical(inventory(components)));}
ValidatedBundle validate_bundle(const std::filesystem::path& root,const NumericalComposition& c,const ValidationContext& ctx){
 need(ctx.trusted_provenance&&!ctx.expected_digest.empty(),"trusted provenance/digest required");
 need(ctx.purpose=="offline_evaluation","serving admission requires Runtime R1");
 need(ctx.snapshot_budget>0&&ctx.snapshot_budget<=512*1024*1024,"validation snapshot budget");
 auto raw=immutable_read(root/"manifest.json",4*1024*1024);need(sha256(raw)==ctx.expected_digest,"trusted manifest digest");auto m=parse_json(raw,4*1024*1024);validate_record("artifact",m);
 ValidatedBundle out;out.digest_=ctx.expected_digest;out.manifest_=m;out.files_=verified_snapshot(root,m["files"],ctx.snapshot_budget,256*1024*1024);
 const auto& f=out.files_;for(const auto& p:{"descriptor.json","model.config.json","weights.pt","training.json","model-card.json","evaluation-registration.json"})need(f.contains(p),"required bundle member");
 for(const auto& [p,b]:f)if(p.ends_with(".json"))need(b.size()<=4*1024*1024,"metadata member bound");
 auto d=parse_json(f.at("descriptor.json"),4*1024*1024);need(d==c.registry.descriptor()&&sha256(f.at("descriptor.json"))==m["descriptor_digest"].get<std::string>(),"compiled descriptor binding");
 need(f.contains(d["semantic_spec"]["path"].get<std::string>())&&sha256(f.at(d["semantic_spec"]["path"].get<std::string>()))==d["semantic_spec"]["sha256"].get<std::string>(),"semantic binding");
 for(const auto& k:{"input_schema","target_schema","output_schema","diagnostics_schema"})if(!d[k].is_null())has_digest(f,d[k]["sha256"]);
 auto refs=d["heads"];for(const auto& k:{"architecture","input_codec","output_codec","objective","numerical_compatibility"})refs.push_back(d[k]);
 for(const auto& ref:refs)has_digest(f,ref["config_digest"]);
 auto model_json=parse_json(f.at("model.config.json"));validate_record("model-config",model_json);auto config=ModelConfig::from_json(model_json);
 need(config.json()==c.model_config.json(),"model composition binding");auto expected=expected_tensor_inventory(config);
 need(sorted_tensors(m["tensor_inventory"])==expected,"compiled tensor inventory");auto count=parameter_count(expected);out.parameter_bytes_=count*4;
 need(m["limits"]["parameters"]==count,"parameter count binding");
 auto env=parse_json(numerical_environment());Json compatibility={{"profile","linux.cpu.fp32.serial.v1"},{"build_digest",c.registry.build_digest()},
  {"libtorch",env["libtorch"]},{"compiler_abi",std::to_string(env["abi"].get<int>())},{"platform",env["platform"]},{"dtype","float32"}};
 need(m["compatibility"]==compatibility,"exact numerical compatibility");
 auto training=parse_json(f.at("training.json"),4*1024*1024);validate_record("training-metadata",training);
 need(sha256(f.at("training.json"))==m["evidence"]["training_digest"].get<std::string>()&&training["descriptor_digest"]==m["descriptor_digest"]&&
  training["build_digest"]==c.registry.build_digest()&&training["model_config"]==model_json&&training["weights_digest"]==sha256(f.at("weights.pt"))&&
  training["environment_digest"]==sha256(numerical_environment())&&training["training_run_id"]==m["training_run_id"],"training evidence binding");
 need(training["state"]["best_weights_digest"]==training["weights_digest"],"selected-best export binding");
 auto r=parse_json(f.at("evaluation-registration.json"));validate_record("evaluation-registration",r);out.registration_=r;
 const auto& ev=m["evidence"]["evaluation"];auto rh=sha256(f.at("evaluation-registration.json")),component=evaluated_component_digest(f);
 need(ev["evaluation_registration_digest"]==rh&&ev["evaluated_component_digest"]==component&&r["descriptor_digest"]==m["descriptor_digest"]&&
   r["evaluated_component_digest"]==component&&r["dataset_digest"]==training["dataset_digest"]&&r["environment_digest"]==training["environment_digest"]&&
   r["selection_scope"]==training["state"]["selection_scope"],"evaluation registration/component binding");
 need(m["evidence"]["calibration"]["state"]=="not_applicable"&&r["calibration"]=="not_applicable","calibration profile not registered for archive loading");
 auto card=parse_json(f.at("model-card.json"));validate_record("model-card",card);need(card["status"]==m["status"]&&card["component_digest"]==component,"model card binding");
 if(m["status"]=="research_candidate")need(ev["state"]=="pending"&&!f.contains("evaluation-report.json")&&!f.contains("evaluation-summary.json"),"pending candidate evidence");
 else {
   need(ev["state"]=="completed"&&f.contains("evaluation-report.json")&&f.contains("evaluation-summary.json"),"completed evidence required");
   auto report=parse_json(f.at("evaluation-report.json"),4*1024*1024),summary=parse_json(f.at("evaluation-summary.json"));validate_record("evaluation-report",report);validate_record("evaluation-summary",summary);
   need(ev["report_digest"]==sha256(f.at("evaluation-report.json"))&&ev["summary_digest"]==sha256(f.at("evaluation-summary.json"))&&summary["report_digest"]==ev["report_digest"],"report digest binding");
   for(const auto* p:{&report,&summary})need((*p)["evaluation_registration_digest"]==rh&&(*p)["evaluated_component_digest"]==component,"report identity");
   need(report["descriptor_digest"]==m["descriptor_digest"]&&report["dataset_digest"]==r["dataset_digest"]&&report["split"]==r["split"]&&report["selection_scope"]==r["selection_scope"]&&report["experiment_id"]==r["experiment_id"]&&report["status"]==summary["status"],"report registration");
   if(report["status"]=="complete")need(report["errors"].empty()&&report["expected_samples"]==report["observed_samples"]&&report["expected_samples"].get<size_t>()>=r["minimum_samples"].get<size_t>(),"complete accounting");
   if(summary["passing"]==true)need(report["status"]=="complete","invalid run passing");
   if(m["status"]=="release_candidate")need(summary["passing"]==true&&r["selection_scope"]!="train_diagnostic"&&r["split"]=="test","release requires confirmatory passing evidence");
 }
 return out;
}
struct BundleAccess {static const Files& files(const ValidatedBundle& v){return v.files_;}};
LoadedBundle materialize_model(const ValidatedBundle& bundle,const NumericalComposition& c,const OfflineContext& ctx){
 std::lock_guard<std::recursive_mutex> numerical(numerical_mutex());
 need(bool(ctx.current)&&ctx.current()&&!ctx.operation_id.empty()&&ctx.profile=="linux.cpu.fp32.serial.v1","current explicit offline admission");
 struct rlimit limit;need(::getrlimit(RLIMIT_AS,&limit)==0&&limit.rlim_cur!=RLIM_INFINITY&&limit.rlim_cur<=ctx.process_address_space_budget,"qualified process address-space enforcement required");
 const auto& f=BundleAccess::files(bundle);need(bundle.manifest()["compatibility"]["build_digest"]==c.registry.build_digest()&&f.at("descriptor.json")==canonical(c.registry.descriptor()),"materialization composition binding");
 need(limit.rlim_cur<=ctx.peak_transient_budget&&bundle.parameter_bytes()<=ctx.persistent_budget&&f.at("weights.pt").size()+bundle.parameter_bytes()*3<=ctx.peak_transient_budget,"materialization budget rejected before constructor");
 auto point=[&](const std::string& stage){if(ctx.fault)ctx.fault(stage);need(ctx.current(),"expired materialization admission");};
 point("before_construct");auto m=std::make_shared<Model>(c.model_config);point("after_construct");load_model_bytes(m,f.at("weights.pt"));point("after_load");m->eval();
 need(sorted_tensors(tensor_inventory(m))==sorted_tensors(bundle.manifest()["tensor_inventory"]),"loaded tensor inventory");
 point("before_transfer");struct rusage use;need(::getrusage(RUSAGE_SELF,&use)==0,"allocation observation unavailable");
 Json receipt={{"operation_id",ctx.operation_id},{"artifact_digest",bundle.digest()},{"build_digest",c.registry.build_digest()},{"profile",ctx.profile},
  {"enforcement","linux.rlimit_as.isolated_process"},{"process_address_space_cap",limit.rlim_cur},{"observed_peak_rss_bytes",uint64_t(use.ru_maxrss)*1024},
  {"tensor_bytes",bundle.parameter_bytes()},{"verified_snapshot_bytes",[&]{size_t n=0;for(const auto& [p,b]:f)n+=b.size();return n;}()},
  {"cleanup","host_must_wait_for_process_exit"}};
 return {m,receipt};
}
}
