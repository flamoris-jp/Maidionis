#include "tinybeat_composition.h"
using namespace maidionis;
NumericalComposition tinybeat_composition(const std::filesystem::path& root) {
  auto read=[&](const std::string& file){return parse_json(read_file(root/file,4*1024*1024),4*1024*1024);};
  auto d=read("descriptor.json");RegistryBuilder builder(compiled_build_digest());
  for(const auto& name:{"input","target","output"}){
    Json expected=std::string(name)=="input"?Json{{"type","object"},{"additionalProperties",false},{"required",{"energy","beat_position"}},
      {"properties",{{"energy",{{"type","integer"},{"minimum",0},{"maximum",100}}},{"beat_position",{{"type","integer"},{"minimum",0},{"maximum",15}}}}}}:
      Json{{"type","object"},{"additionalProperties",false},{"required",{"kick","snare"}},{"properties",{{"kick",{{"type","boolean"}}},{"snare",{{"type","boolean"}}}}}};
    const auto& ref=d[std::string(name)+"_schema"];auto definition=read(std::string(name)+".schema.json");
    if(ref["id"]!=std::string("test.tiny-beat.")+name||ref["version"]!="1"||definition!=expected)throw std::invalid_argument("compiled schema binding");
    builder.add_schema(ref,definition);
  }
  for(const auto& name:{"input_codec","output_codec","architecture","objective","numerical_compatibility","head"}) {
    const auto& ref=std::string(name)=="head"?d["heads"][0]:d[name];auto config=read(std::string(name)+".config.json");
    const Json expected=std::string(name)=="input_codec"?Json{{"features",2},{"energy_divisor",100},{"position_divisor",15}}:
      std::string(name)=="output_codec"?Json{{"threshold_milli",500},{"tie","positive"}}:
      std::string(name)=="architecture"?Json{{"input_width",2},{"hidden_width",8},{"output_width",2},{"dropout_milli",100}}:
      std::string(name)=="objective"?Json{{"reduction","mean"},{"kind","bernoulli"}}:
      std::string(name)=="head"?Json{{"outputs",2}}:Json{{"profile","linux.cpu.fp32.serial.v1"},{"libtorch","2.5.1"},{"archive",1}};
    if(ref["id"]!=std::string("test.tiny-beat.")+name||ref["version"]!="1"||config!=expected)throw std::invalid_argument("unknown compiled binding");
    builder.add_operation(ref,config,[expected](const Json& c){if(c!=expected)throw std::invalid_argument("config binding");});
  }
  NumericalComposition c;c.registry=builder.freeze(d);
  if(d["task_id"]!="test.tiny-beat"||d["specialization_id"]!="test.tiny-beat"||d["task_version"]!="1"||d["specialization_version"]!="1"||
     d["diagnostics_schema"]!=nullptr||d["heads"].size()!=1||d["semantic_spec"]["path"]!="semantic.txt"||
     read_file(root/"semantic.txt",4096)!="Tiny Beat synthetic oracle v1: kick when energy >= 50; snare when position >= 8. Mechanics only.\n"||
     sha256(read_file(root/"semantic.txt",4096))!=d["semantic_spec"]["sha256"].get<std::string>())throw std::invalid_argument("test descriptor binding");
  c.encode=[r=c.registry](const std::vector<Json>& rows) {
    std::vector<std::vector<float>> x,y;
    for(const auto& row:rows) {
      if(row.contains("input")){r.sample(row);x.push_back({row["input"]["energy"].get<float>()/100,row["input"]["beat_position"].get<float>()/15});
        y.push_back({row["target"]["kick"].get<bool>()?1.f:0.f,row["target"]["snare"].get<bool>()?1.f:0.f});}
      else {r.payload("input_schema",row);x.push_back({row["energy"].get<float>()/100,row["beat_position"].get<float>()/15});}
    }
    return dense_batch(x,y,2,2);
  };
  c.objective=[](const torch::Tensor& logits,const Batch& b){return bernoulli_loss(logits,b.targets);};
  c.decode=[](const torch::Tensor& logits){if(logits.numel()!=2)throw std::invalid_argument("decode shape");auto p=torch::sigmoid(logits.flatten());return Json{{"kick",p[0].item<float>()>=.5f},{"snare",p[1].item<float>()>=.5f}};};
  c.verify_dataset_row=[](const Json& row,const Json& family,const Json& manifest,const Json& config){
    const auto& input=row["input"];Json root={{"scenario",{{"energy",input["energy"]},{"position",input["beat_position"]}}},{"template","grid-v1"}};
    auto ref=[](const std::string& name,const Json& value){return Json{{"id","test.tiny-beat."+name},{"version","1"},{"config_digest",sha256(canonical(value))}};};
    auto hook=ref("dataset-hooks",Json{{"implementation","test-v1"},{"build_digest",compiled_build_digest()}}),verify=ref("oracle",Json{{"oracle","kick>=50,snare>=8"}});
    auto grouping=ref("group",Json{{"projection","energy-position-v1"}}),dedup=ref("dedup",Json{{"projection","exact-input"}});
    if(family["roots"]!=Json::array({Json{{"digest",sha256(canonical(root))},{"content",root}}})||config["hook"]!=hook||config["grouping"]!=grouping||
       manifest["dedup_profile"]!=dedup||manifest["verification_profile"]!=verify||row["verification_profile"]!=verify||row["supersedes"]!=nullptr||
       manifest["generator"]!=Json{{"code_digest",compiled_build_digest()},{"config_digest",sha256(canonical(Json{{"grid","energy-0..100-step-10,position-0..15"}}))}}||
       row["target"]!=Json{{"kick",input["energy"].get<int>()>=50},{"snare",input["beat_position"].get<int>()>=8}})throw std::invalid_argument("native Tiny Beat frozen eligibility");
  };
  c.validate();return c;
}
