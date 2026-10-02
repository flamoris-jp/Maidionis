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
DatasetHandle training_data(const std::filesystem::path& root,const std::string& trusted_digest,const NumericalComposition& composition) {
  const auto& r=composition.registry;require(bool(composition.verify_dataset_row),"explicit native dataset verifier required");
  auto raw=immutable_read(root/"manifest.json",4*1024*1024);require(sha256(raw)==trusted_digest,"dataset digest");auto manifest=parse_json(raw,4*1024*1024);validate_record("dataset",manifest);
  std::map<std::string,Json> entries;size_t total=0;
  for(const auto& e:manifest["files"]){auto p=e["path"].get<std::string>();safe_path(p);auto bytes=e["bytes"].get<size_t>();
    require(p!="manifest.json"&&entries.emplace(p,e).second&&bytes<=1024*1024*1024-total,"dataset inventory coverage/bound");total+=bytes;}
  std::set<std::string> disk;
  for(const auto& e:std::filesystem::recursive_directory_iterator(root)){require(!e.is_symlink(),"dataset symlink");if(e.is_directory())continue;require(e.is_regular_file(),"dataset nonregular member");auto p=std::filesystem::relative(e.path(),root).generic_string();if(p!="manifest.json")disk.insert(p);}
  require(disk.size()==entries.size(),"extra/missing dataset member");for(const auto& p:disk)require(entries.contains(p),"extra dataset member");
  auto metadata=[&](const std::string& p){require(entries.contains(p),"dataset metadata inventory");auto b=immutable_read(root/p,4*1024*1024);require(b.size()==entries.at(p)["bytes"].get<size_t>()&&sha256(b)==entries.at(p)["sha256"].get<std::string>(),"dataset metadata digest");return parse_json(b,4*1024*1024);};
  safe_path(manifest["descriptor"]["path"].get<std::string>());auto descriptor=immutable_read(root/manifest["descriptor"]["path"].get<std::string>(),4*1024*1024);require(sha256(descriptor)==manifest["descriptor"]["sha256"].get<std::string>()&&parse_json(descriptor,4*1024*1024)==r.descriptor(),"dataset descriptor");
  require(entries.contains("descriptor.json")&&entries["descriptor.json"]["sha256"]==manifest["descriptor"]["sha256"],"descriptor inventory binding");
  auto split_config=metadata("split.config.json"),index=metadata("family-index.json");validate_record("family-index",index);
  require(entries.at("family-index.json")["sha256"]==manifest["split_profile"]["family_registry_digest"]&&entries.at("split.config.json")["sha256"]==manifest["split_profile"]["config_digest"],"family/split config binding");
  require(split_config["algorithm"]==composition.split_algorithm&&split_config["seed"]==manifest["split_profile"]["seed"]&&split_config["grouping"]["version"]==manifest["split_profile"]["grouping_version"],"supported split algorithm");
  require(composition.split_algorithm=="maidionis-split-v1"?!composition.assign_family:bool(composition.assign_family),"explicit partition binding required");
  auto assigned=[&](const std::string& fp,const Json& family){
    if(composition.assign_family){auto s=composition.assign_family(family,manifest,split_config);require(s=="train"||s=="dev"||s=="calibration_fit"||s=="calibration_select"||s=="test","partition result");return s;}
    auto hash=sha256("maidionis-split-v1\n"+std::to_string(manifest["split_profile"]["seed"].get<int64_t>())+"\n"+fp);auto bucket=std::stoull(hash.substr(0,16),nullptr,16)%10000;
    return std::string(bucket<6000?"train":bucket<7500?"dev":bucket<8500?"calibration_fit":bucket<9000?"calibration_select":"test");};
  std::map<std::string,Json> families;std::set<std::string> aliases,members,roots;std::map<std::string,size_t> family_counts,record_counts;
  for(const auto& f:index){auto fp=f["fingerprint"].get<std::string>();require(families.emplace(fp,f).second&&sha256(canonical(f["anchor"]))==fp,"family anchor fingerprint");
    require(f["anchor"]["task_id"]==r.descriptor()["task_id"]&&f["anchor"]["task_version"]==r.descriptor()["task_version"]&&f["anchor"]["grouping_profile"]==split_config["grouping"],"family anchor profile");
    std::vector<std::string> root_digests;for(const auto& root:f["roots"]){auto h=root["digest"].get<std::string>();require(h==sha256(canonical(root["content"]))&&roots.insert(h).second,"forged/shared family root");root_digests.push_back(h);}
    require(std::is_sorted(root_digests.begin(),root_digests.end())&&Json(root_digests)==f["anchor"]["root_digests"],"root ordering/binding");
    for(const auto& a:f["aliases"])require(aliases.insert(a.get<std::string>()).second,"family alias collision");for(const auto& id:f["members"])require(members.insert(id.get<std::string>()).second,"family member collision");
    auto s=assigned(fp,f);++family_counts[s];record_counts[s]+=f["members"].size();}
  for(const auto& s:{"train","dev","calibration_fit","calibration_select","test"})require(manifest["counts"][s]["families"]==family_counts[s]&&manifest["counts"][s]["records"]==record_counts[s],"family split counts");
  DatasetHandle data;data.manifest_digest_=trusted_digest;
  std::set<std::string> all_ids;
  for(const auto& split:{"train","dev"}) {
    auto name=std::string(split)+".jsonl";Json entry;size_t matches=0;for(const auto& e:manifest["files"])if(e["path"]==name){entry=e;++matches;}
    require(matches==1,"split inventory");auto bytes=immutable_read(root/name,64*1024*1024);require(bytes.size()==entry["bytes"].get<size_t>()&&sha256(bytes)==entry["sha256"].get<std::string>(),"split digest");
    if(!bytes.empty())require(bytes.back()=='\n',"JSONL missing LF");std::istringstream lines(bytes);std::string line;auto& rows=std::string(split)=="train"?data.train_:data.dev_;std::set<std::string> ids;
    while(std::getline(lines,line)){require(!line.empty(),"blank JSONL");auto row=parse_json(line,128*1024);r.sample(row);auto id=row["sample_id"].get<std::string>(),fp=row["family_fingerprint"].get<std::string>();
      require(row["split"]==split&&row["dataset_id"]==manifest["dataset_id"]&&ids.insert(id).second&&all_ids.insert(id).second,"split record identity");
      require(families.contains(fp)&&assigned(fp,families.at(fp))==std::string(split),"native family split assignment");const auto& f=families.at(fp);
      require(std::find(f["aliases"].begin(),f["aliases"].end(),row["family_id"])!=f["aliases"].end()&&std::find(f["members"].begin(),f["members"].end(),row["sample_id"])!=f["members"].end(),"family alias/member binding");
      require(row["verification_profile"]==manifest["verification_profile"],"verification profile binding");composition.verify_dataset_row(row,f,manifest,split_config);
      rows.push_back(row);require(rows.size()<=1000000,"record limit");}
    require(rows.size()==manifest["counts"][split]["records"].get<size_t>(),"split count");
  }
  require(!data.train_.empty(),"empty train split");return data;
}
TrainingResult train(const NumericalComposition& c,const DatasetHandle& data,const TrainingConfig& config,const std::filesystem::path& root,bool resume,int64_t max_epochs,Fault fault) {
  std::unique_lock<std::recursive_mutex> numerical(numerical_mutex(),std::try_to_lock);require(numerical.owns_lock(),"concurrent global-RNG training rejected");
  c.validate();config.validate();require(!root.empty()&&max_epochs>=0&&data.train_.size()<=1000000,"training bounds");WriterLock lock(root/"writer.lock");
  require(!data.train_.empty()&&(config.selection_scope!="dev"||!data.dev_.empty()),"empty training/selection split");
  auto m=make_seeded_model(c.model_config,config.seed);auto best=make_seeded_model(c.model_config,config.seed);
  auto roles=m->decay_roles();torch::optim::AdamW optimizer(m->parameters(),torch::optim::AdamWOptions(config.learning_rate).weight_decay(0));
  const auto planned=int64_t((data.train_.size()+config.batch_size-1)/config.batch_size)*config.epochs;
  Files identity={{"descriptor.json",canonical(c.registry.descriptor())},{"config.json",canonical(Json{{"training",config.json()},{"model",c.model_config.json()},{"composition_build",c.registry.build_digest()}})},
    {"environment.json",numerical_environment()},{"data.json",canonical(Json{{"manifest_digest",data.manifest_digest_}})}};
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
      manifest["environment_digest"]==environment_sha&&manifest["dataset_digest"]==data.manifest_digest_&&manifest["codec_digest"]==codec_sha,"checkpoint identity changed");
    auto files=verified_snapshot(root/name,manifest["files"],512*1024*1024,256*1024*1024);
    std::set<std::string> expected={"descriptor.json","config.json","environment.json","data.json","model.pt","best.pt","optimizer.pt","rng.pt","state.json","history.json"};
    require(files.size()==expected.size(),"checkpoint inventory coverage");for(const auto& k:expected)require(files.contains(k),"checkpoint member missing");
    for(const auto& [p,b]:identity)require(files.at(p)==b,"checkpoint identity bytes");
    require(sha256(files.at("state.json"))==manifest["state_digest"].get<std::string>()&&sha256(files.at("history.json"))==manifest["history_digest"].get<std::string>(),"checkpoint state/history binding");
    state=parse_json(files.at("state.json"),4*1024*1024);validate_record("training-state",state);history=parse_json(files.at("history.json"),4*1024*1024);
    require(history==state["history"]&&state["best_weights_digest"]==sha256(files.at("best.pt"))&&state["planned_total_steps"]==planned&&state["selection_scope"]==config.selection_scope,"checkpoint state binding");
    next=state["next_epoch"];step=state["global_step"];best_epoch=state["best_epoch"];best_value=state["best_objective"];patience=state["patience_counter"];stopped=state["stopped"];
    require(next==state["completed_epoch"].get<int64_t>()+1&&next<=config.epochs&&history.size()==size_t(next)&&step==next*(planned/config.epochs),"checkpoint epoch accounting");
    Json expected_roles=Json::array();for(const auto& [name,decay]:roles)expected_roles.push_back({{"name",name},{"decay",decay}});
    require(state["scheduler"]==Json{{"id","linear_decay"},{"version","1"},{"phase",step},{"base_lr",config.learning_rate}}&&state["parameter_groups"]==expected_roles&&
      state["epoch_order_version"]=="sha256_sort.v1"&&state["rng_inventory"]==Json::array({"rng.pt"}),"checkpoint schedule/roles/RNG binding");
    double selected=std::numeric_limits<double>::infinity();int64_t selected_epoch=0,unimproved=0;
    for(int64_t e=0;e<next;++e){const auto& h=history[e];double score=h["objective"];bool improves=score<selected;
      require(h["epoch"]==e&&h["step"]==(e+1)*(planned/config.epochs)&&h["lr"]==config.learning_rate*(1-.9*double((e+1)*(planned/config.epochs))/planned)&&h["improved"]==improves,"checkpoint history accounting");
      if(improves){selected=score;selected_epoch=e;unimproved=0;}else ++unimproved;
      require(e==next-1||unimproved<config.patience,"history continues after early stop");}
    require(best_epoch==selected_epoch&&best_value==selected&&patience==unimproved&&stopped==(unimproved>=config.patience),"checkpoint selection accounting");
    load_model_bytes(m,files.at("model.pt"));load_model_bytes(best,files.at("best.pt"));load_optimizer(optimizer,files.at("optimizer.pt"));
    require(optimizer.param_groups().size()==1&&optimizer.state().size()==m->parameters().size(),"optimizer inventory");
    auto& options=static_cast<torch::optim::AdamWOptions&>(optimizer.param_groups()[0].options());
    require(options.lr()==config.learning_rate*(1-.9*double(step)/planned)&&options.weight_decay()==0&&options.betas()==std::make_tuple(.9,.999)&&options.eps()==1e-8&&!options.amsgrad(),"optimizer configuration binding");
    for(const auto& parameter:m->parameters()){
      auto it=optimizer.state().find(parameter.unsafeGetTensorImpl());require(it!=optimizer.state().end(),"optimizer parameter binding");
      auto* s=dynamic_cast<torch::optim::AdamWParamState*>(it->second.get());require(s&&s->step()==step,"optimizer step continuity");
      for(const auto& t:{s->exp_avg(),s->exp_avg_sq()})require(t.defined()&&t.device().is_cpu()&&t.scalar_type()==torch::kFloat32&&t.sizes()==parameter.sizes()&&torch::isfinite(t).all().item<bool>(),"optimizer moment contract");
      require(s->exp_avg_sq().ge(0).all().item<bool>()&&!s->max_exp_avg_sq().defined(),"optimizer variance contract");}
    load_rng(files.at("rng.pt"));result.checkpoint_digest=sha256(manifest_raw);
  }else {require(!std::filesystem::exists(root/"latest.json"),"existing run requires resume");torch::manual_seed(config.seed);}
  int64_t done=0;
  for(int64_t epoch=next;epoch<config.epochs&&!stopped;++epoch) {
    m->train();auto order=epoch_order(data.train_.size(),config.seed,epoch);double total=0;
    for(size_t start=0;start<order.size();start+=config.batch_size) {
      std::vector<Json> rows;for(size_t i=start;i<std::min(order.size(),start+config.batch_size);++i)rows.push_back(data.train_[order[i]]);
      auto b=c.encode(rows);optimizer.zero_grad();auto loss=c.objective(m->forward(b),b);require(torch::isfinite(loss).item<bool>(),"nonfinite training loss");loss.backward();
      for(const auto& p:m->parameters()){require(p.grad().defined()&&torch::isfinite(p.grad()).all().item<bool>(),"nonfinite/missing gradient");result.gradient_l1+=p.grad().abs().sum().item<double>();}
      torch::nn::utils::clip_grad_norm_(m->parameters(),config.max_grad_norm);++step;double lr=config.learning_rate*(1-.9*double(step)/planned);
      static_cast<torch::optim::AdamWOptions&>(optimizer.param_groups()[0].options()).lr(lr);
      {torch::NoGradGuard no;for(const auto& [name,decay]:roles)m->named_parameters()[name].mul_(1-lr*config.weight_decay*decay);}
      optimizer.step();m->enforce_constraints();total+=loss.item<double>()*rows.size();
    }
    auto score=objective(m,c,config.selection_scope=="dev"?data.dev_:data.train_,config.batch_size);
    const bool improved=score<best_value; if(improved){best_value=score;best_epoch=epoch;patience=0;load_model_bytes(best,save_model_bytes(m));}else ++patience;
    stopped=patience>=config.patience;history.push_back({{"epoch",epoch},{"step",step},{"loss",total/data.train_.size()},{"objective",score},{"lr",config.learning_rate*(1-.9*double(step)/planned)},{"improved",improved}});
    Files files=identity;files["model.pt"]=save_model_bytes(m);files["best.pt"]=save_model_bytes(best);files["optimizer.pt"]=optimizer_bytes(optimizer);files["rng.pt"]=rng_bytes();files["history.json"]=canonical(history);
    Json groups=Json::array();for(const auto& [name,role]:roles)groups.push_back({{"name",name},{"decay",role}});
    state={{"schema_version","maidionis.training-state.v1"},{"completed_epoch",epoch},{"next_epoch",epoch+1},{"global_step",step},{"planned_total_steps",planned},
      {"scheduler",{{"id","linear_decay"},{"version","1"},{"phase",step},{"base_lr",config.learning_rate}}},{"parameter_groups",groups},
      {"best_objective",best_value},{"best_epoch",best_epoch},{"best_weights_digest",sha256(files["best.pt"])},{"patience_counter",patience},{"stopped",stopped},
      {"selection_scope",config.selection_scope},{"epoch_order_version","sha256_sort.v1"},{"rng_inventory",{"rng.pt"}},{"history",history}};
    validate_record("training-state",state);files["state.json"]=canonical(state);
    const auto name="epoch-"+std::to_string(epoch+1);Json manifest={{"schema_version","maidionis.checkpoint.v1"},{"checkpoint_id",name},{"created_at",utc_now()},
      {"descriptor_digest",descriptor_sha},{"config_digest",config_sha},{"dataset_digest",data.manifest_digest_},{"environment_digest",environment_sha},{"codec_digest",codec_sha},
      {"files",inventory(files)},{"state_digest",sha256(files["state.json"])},{"history_digest",sha256(files["history.json"])}};
    validate_record("checkpoint",manifest);auto manifest_bytes=canonical(manifest);files["manifest.json"]=manifest_bytes;
    publish_tree(root/name,files,fault);atomic_pointer(root/"latest.json",canonical(Json{{"checkpoint",name},{"manifest_digest",sha256(manifest_bytes)}}),fault);result.checkpoint_digest=sha256(manifest_bytes);
    ++done;if(max_epochs&&done>=max_epochs)break;
  }
  result.final_model=m;result.best_model=best;result.state=state;return result;
}
}
