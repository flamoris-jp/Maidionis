#include "maidionis/training.h"
#include <cmath>
#include <limits>
#include <numeric>
#include <regex>

namespace maidionis {
namespace {
void require(bool v,const char* s){if(!v)throw std::invalid_argument(s);}
std::string optimizer_bytes(torch::optim::AdamW& optimizer){torch::serialize::OutputArchive a;optimizer.save(a);std::ostringstream o;a.save_to(o);return o.str();}
void load_optimizer(torch::optim::AdamW& optimizer,const std::string& raw){torch::serialize::InputArchive a;std::istringstream s(raw);a.load_from(s,torch::kCPU);optimizer.load(a);}
std::string rng_bytes(){torch::serialize::OutputArchive a;a.write("cpu",at::detail::getDefaultCPUGenerator().get_state());std::ostringstream s;a.save_to(s);return s.str();}
void load_rng(const std::string& raw){torch::serialize::InputArchive a;std::istringstream s(raw);a.load_from(s,torch::kCPU);torch::Tensor state;a.read("cpu",state);auto g=at::detail::getDefaultCPUGenerator();g.set_state(state);}
std::vector<size_t> epoch_order(size_t count,int64_t seed,int64_t epoch) {
  // Digest sort avoids std::shuffle/toolchain-specific PRNG distributions.
  std::vector<std::pair<std::string,size_t>> scored;for(size_t i=0;i<count;++i)scored.push_back({sha256(std::to_string(seed)+"\n"+std::to_string(epoch)+"\n"+std::to_string(i)),i});
  std::sort(scored.begin(),scored.end());std::vector<size_t> out;for(auto& [s,i]:scored)out.push_back(i);return out;
}
double objective(ModelPtr m,const NumericalComposition& c,const std::vector<Json>& rows,size_t bs){require(!rows.empty(),"empty selection split");m->eval();torch::NoGradGuard no;double total=0;
  for(size_t start=0;start<rows.size();start+=bs){auto stop=std::min(rows.size(),start+bs);std::vector<Json> values(rows.begin()+start,rows.begin()+stop);auto b=c.encode(values);auto loss=c.objective(m->forward(b),b).item<double>();require(std::isfinite(loss),"selection objective nonfinite");total+=loss*values.size();}return total/rows.size();}
}
Json TrainingConfig::json() const{return {{"seed",seed},{"epochs",epochs},{"batch_size",batch_size},{"patience",patience},{"learning_rate",learning_rate},
 {"weight_decay",weight_decay},{"max_grad_norm",max_grad_norm},{"selection_scope",selection_scope},{"scheduler","linear_decay.v1"},{"optimizer","adamw.v1"},
 {"betas",{.9,.999}},{"epsilon",1e-8},{"epoch_order","sha256_sort.v1"},{"device","cpu"},{"dtype","float32"},{"threads",1}};}
void TrainingConfig::validate() const {require(seed>=0&&epochs>0&&epochs<=10000&&batch_size>0&&batch_size<=64&&patience>0&&patience<=10000&&
 std::isfinite(learning_rate)&&learning_rate>0&&learning_rate<=1&&std::isfinite(weight_decay)&&weight_decay>=0&&weight_decay<=1&&
 std::isfinite(max_grad_norm)&&max_grad_norm>0&&max_grad_norm<=1000&&(selection_scope=="dev"||selection_scope=="train_diagnostic"),"training configuration");}
DatasetHandle training_data(const std::filesystem::path& root,const std::string& trusted_digest,const Registry& r) {
  auto raw=immutable_read(root/"manifest.json",4*1024*1024);require(sha256(raw)==trusted_digest,"dataset digest");auto manifest=parse_json(raw,4*1024*1024);validate_record("dataset",manifest);
  safe_path(manifest["descriptor"]["path"].get<std::string>());auto descriptor=immutable_read(root/manifest["descriptor"]["path"].get<std::string>(),4*1024*1024);require(sha256(descriptor)==manifest["descriptor"]["sha256"].get<std::string>()&&parse_json(descriptor,4*1024*1024)==r.descriptor(),"dataset descriptor");
  DatasetHandle data;data.manifest_digest=trusted_digest;
  for(const auto& split:{"train","dev"}) {
    auto name=std::string(split)+".jsonl";Json entry;size_t matches=0;for(const auto& e:manifest["files"])if(e["path"]==name){entry=e;++matches;}
    require(matches==1,"split inventory");auto bytes=immutable_read(root/name,64*1024*1024);require(bytes.size()==entry["bytes"].get<size_t>()&&sha256(bytes)==entry["sha256"].get<std::string>(),"split digest");
    if(!bytes.empty())require(bytes.back()=='\n',"JSONL missing LF");std::istringstream lines(bytes);std::string line;auto& rows=std::string(split)=="train"?data.train:data.dev;std::set<std::string> ids;
    while(std::getline(lines,line)){require(!line.empty(),"blank JSONL");auto row=parse_json(line,128*1024);r.sample(row);require(row["split"]==split&&row["dataset_id"]==manifest["dataset_id"]&&ids.insert(row["sample_id"].get<std::string>()).second,"split record identity");rows.push_back(row);require(rows.size()<=1000000,"record limit");}
    require(rows.size()==manifest["counts"][split]["records"].get<size_t>(),"split count");
  }
  require(!data.train.empty(),"empty train split");return data;
}
TrainingResult train(const NumericalComposition& c,const DatasetHandle& data,const TrainingConfig& config,const std::filesystem::path& root,bool resume,int64_t max_epochs,Fault fault) {
  c.validate();config.validate();require(!root.empty()&&max_epochs>=0&&data.train.size()<=1000000,"training bounds");WriterLock lock(root/"writer.lock");
  require(!data.train.empty()&&(config.selection_scope!="dev"||!data.dev.empty()),"empty training/selection split");
  auto m=make_seeded_model(c.model_config,config.seed);auto best=make_seeded_model(c.model_config,config.seed);
  auto roles=m->decay_roles();torch::optim::AdamW optimizer(m->parameters(),torch::optim::AdamWOptions(config.learning_rate).weight_decay(0));
  const auto planned=int64_t((data.train.size()+config.batch_size-1)/config.batch_size)*config.epochs;
  Files identity={{"descriptor.json",canonical(c.registry.descriptor())},{"config.json",canonical(Json{{"training",config.json()},{"model",c.model_config.json()},{"composition_build",c.registry.build_digest()}})},
    {"environment.json",numerical_environment()},{"data.json",canonical(Json{{"manifest_digest",data.manifest_digest}})}};
  const auto descriptor_sha=sha256(identity["descriptor.json"]),config_sha=sha256(identity["config.json"]),environment_sha=sha256(identity["environment.json"]);
  const auto codec_sha=c.registry.descriptor()["input_codec"]["config_digest"].get<std::string>();
  Json history=Json::array(),state;int64_t next=0,step=0,best_epoch=0,patience=0;double best_value=std::numeric_limits<double>::infinity();bool stopped=false;
  TrainingResult result;
  if(resume) {
    auto pointer=parse_json(immutable_read(root/"latest.json",4096));require(pointer.is_object()&&pointer.size()==2&&pointer.contains("checkpoint")&&pointer.contains("manifest_digest"),"latest pointer fields");
    auto name=pointer["checkpoint"].get<std::string>();require(std::regex_match(name,std::regex("epoch-[0-9]+")),"latest pointer path");
    auto manifest_raw=immutable_read(root/name/"manifest.json",4*1024*1024);require(sha256(manifest_raw)==pointer["manifest_digest"].get<std::string>(),"checkpoint manifest digest");
    auto manifest=parse_json(manifest_raw,4*1024*1024);validate_record("checkpoint",manifest);
    require(manifest["checkpoint_id"]==name&&manifest["descriptor_digest"]==descriptor_sha&&manifest["config_digest"]==config_sha&&
      manifest["environment_digest"]==environment_sha&&manifest["dataset_digest"]==data.manifest_digest&&manifest["codec_digest"]==codec_sha,"checkpoint identity changed");
    auto files=verified_snapshot(root/name,manifest["files"],512*1024*1024,256*1024*1024);
    std::set<std::string> expected={"descriptor.json","config.json","environment.json","data.json","model.pt","best.pt","optimizer.pt","rng.pt","state.json","history.json"};
    require(files.size()==expected.size(),"checkpoint inventory coverage");for(const auto& k:expected)require(files.contains(k),"checkpoint member missing");
    for(const auto& [p,b]:identity)require(files.at(p)==b,"checkpoint identity bytes");
    require(sha256(files.at("state.json"))==manifest["state_digest"].get<std::string>()&&sha256(files.at("history.json"))==manifest["history_digest"].get<std::string>(),"checkpoint state/history binding");
    state=parse_json(files.at("state.json"),4*1024*1024);validate_record("training-state",state);history=parse_json(files.at("history.json"),4*1024*1024);
    require(history==state["history"]&&state["best_weights_digest"]==sha256(files.at("best.pt"))&&state["planned_total_steps"]==planned&&state["selection_scope"]==config.selection_scope,"checkpoint state binding");
    next=state["next_epoch"];step=state["global_step"];best_epoch=state["best_epoch"];best_value=state["best_objective"];patience=state["patience_counter"];stopped=state["stopped"];
    require(next==state["completed_epoch"].get<int64_t>()+1&&next<=config.epochs&&history.size()==size_t(next)&&step==next*(planned/config.epochs),"checkpoint epoch accounting");
    load_model_bytes(m,files.at("model.pt"));load_model_bytes(best,files.at("best.pt"));load_optimizer(optimizer,files.at("optimizer.pt"));load_rng(files.at("rng.pt"));result.checkpoint_digest=sha256(manifest_raw);
  }else {require(!std::filesystem::exists(root/"latest.json"),"existing run requires resume");torch::manual_seed(config.seed);}
  int64_t done=0;
  for(int64_t epoch=next;epoch<config.epochs&&!stopped;++epoch) {
    m->train();auto order=epoch_order(data.train.size(),config.seed,epoch);double total=0;
    for(size_t start=0;start<order.size();start+=config.batch_size) {
      std::vector<Json> rows;for(size_t i=start;i<std::min(order.size(),start+config.batch_size);++i)rows.push_back(data.train[order[i]]);
      auto b=c.encode(rows);optimizer.zero_grad();auto loss=c.objective(m->forward(b),b);require(torch::isfinite(loss).item<bool>(),"nonfinite training loss");loss.backward();
      for(const auto& p:m->parameters()){require(p.grad().defined()&&torch::isfinite(p.grad()).all().item<bool>(),"nonfinite/missing gradient");result.gradient_l1+=p.grad().abs().sum().item<double>();}
      torch::nn::utils::clip_grad_norm_(m->parameters(),config.max_grad_norm);++step;double lr=config.learning_rate*(1-.9*double(step)/planned);
      static_cast<torch::optim::AdamWOptions&>(optimizer.param_groups()[0].options()).lr(lr);
      {torch::NoGradGuard no;for(const auto& [name,decay]:roles)m->named_parameters()[name].mul_(1-lr*config.weight_decay*decay);}
      optimizer.step();m->enforce_constraints();total+=loss.item<double>()*rows.size();
    }
    auto score=objective(m,c,config.selection_scope=="dev"?data.dev:data.train,config.batch_size);
    const bool improved=score<best_value; if(improved){best_value=score;best_epoch=epoch;patience=0;load_model_bytes(best,save_model_bytes(m));}else ++patience;
    stopped=patience>=config.patience;history.push_back({{"epoch",epoch},{"step",step},{"loss",total/data.train.size()},{"objective",score},{"lr",config.learning_rate*(1-.9*double(step)/planned)},{"improved",improved}});
    Files files=identity;files["model.pt"]=save_model_bytes(m);files["best.pt"]=save_model_bytes(best);files["optimizer.pt"]=optimizer_bytes(optimizer);files["rng.pt"]=rng_bytes();files["history.json"]=canonical(history);
    Json groups=Json::array();for(const auto& [name,role]:roles)groups.push_back({{"name",name},{"decay",role}});
    state={{"schema_version","maidionis.training-state.v1"},{"completed_epoch",epoch},{"next_epoch",epoch+1},{"global_step",step},{"planned_total_steps",planned},
      {"scheduler",{{"id","linear_decay"},{"version","1"},{"phase",step},{"base_lr",config.learning_rate}}},{"parameter_groups",groups},
      {"best_objective",best_value},{"best_epoch",best_epoch},{"best_weights_digest",sha256(files["best.pt"])},{"patience_counter",patience},{"stopped",stopped},
      {"selection_scope",config.selection_scope},{"epoch_order_version","sha256_sort.v1"},{"rng_inventory",{"rng.pt"}},{"history",history}};
    validate_record("training-state",state);files["state.json"]=canonical(state);
    const auto name="epoch-"+std::to_string(epoch+1);Json manifest={{"schema_version","maidionis.checkpoint.v1"},{"checkpoint_id",name},{"created_at",utc_now()},
      {"descriptor_digest",descriptor_sha},{"config_digest",config_sha},{"dataset_digest",data.manifest_digest},{"environment_digest",environment_sha},{"codec_digest",codec_sha},
      {"files",inventory(files)},{"state_digest",sha256(files["state.json"])},{"history_digest",sha256(files["history.json"])}};
    validate_record("checkpoint",manifest);auto manifest_bytes=canonical(manifest);files["manifest.json"]=manifest_bytes;
    publish_tree(root/name,files,fault);atomic_pointer(root/"latest.json",canonical(Json{{"checkpoint",name},{"manifest_digest",sha256(manifest_bytes)}}),fault);result.checkpoint_digest=sha256(manifest_bytes);
    ++done;if(max_epochs&&done>=max_epochs)break;
  }
  result.final_model=m;result.best_model=best;result.state=state;return result;
}
}
