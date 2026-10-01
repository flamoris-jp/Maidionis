#include "maidionis/model.h"
#include <torch/version.h>
#include <cmath>
#include <sstream>

namespace maidionis {
void ModelConfig::validate() const {
  TORCH_CHECK((kind=="dense"||kind=="pooled"||kind=="encoder")&&hidden_width>=1&&hidden_width<=1024&&
    input_width>=1&&input_width<=256&&output_width>=1&&output_width<=256&&dropout_milli>=0&&dropout_milli<1000,"invalid model shape");
  if(kind!="dense") {
    TORCH_CHECK(vocabulary>=9&&vocabulary<=8192&&hidden_width==256&&max_length==256,"invalid text profile");
    TORCH_CHECK(controls.size()<=16,"control limit");std::set<int64_t> seen;
    for(auto c:controls)TORCH_CHECK(c>0&&c<vocabulary&&seen.insert(c).second,"invalid controls");
  }
  if(kind=="encoder")TORCH_CHECK(layers==4&&heads==4&&ffn_width==1024,"invalid encoder profile");
}
Json ModelConfig::json() const{return {{"kind",kind},{"input_width",input_width},{"hidden_width",hidden_width},{"output_width",output_width},
 {"dropout_milli",dropout_milli},{"vocabulary",vocabulary},{"layers",layers},{"heads",heads},{"ffn_width",ffn_width},{"max_length",max_length},{"controls",controls}};}
ModelConfig ModelConfig::from_json(const Json& j) {
  validate_record("model-config",j);
  ModelConfig c;c.kind=j.at("kind");c.input_width=j.at("input_width");c.hidden_width=j.at("hidden_width");c.output_width=j.at("output_width");
  c.dropout_milli=j.at("dropout_milli");c.vocabulary=j.at("vocabulary");c.layers=j.at("layers");c.heads=j.at("heads");c.ffn_width=j.at("ffn_width");c.max_length=j.at("max_length");c.controls=j.at("controls").get<std::vector<int64_t>>();
  TORCH_CHECK(c.json()==j,"unknown model config");c.validate();return c;
}
Model::Model(const ModelConfig& c):config_(c) {
  c.validate();
  if(c.kind=="dense")projection_=register_module("projection",torch::nn::Linear(c.input_width,c.hidden_width));
  else {
    embedding_=register_module("embedding",torch::nn::Embedding(torch::nn::EmbeddingOptions(c.vocabulary,c.hidden_width).padding_idx(0)));
    if(c.kind=="pooled")projection_=register_module("projection",torch::nn::Linear(c.hidden_width,c.hidden_width));
    else {
      positions_=register_module("positions",torch::nn::Embedding(c.max_length,c.hidden_width));
      segments_=register_module("segments",torch::nn::Embedding(4,c.hidden_width));
      auto layer=torch::nn::TransformerEncoderLayer(torch::nn::TransformerEncoderLayerOptions(c.hidden_width,c.heads)
        .dim_feedforward(c.ffn_width).dropout(c.dropout_milli/1000.0).activation(torch::kGELU));
      encoder_=register_module("encoder",torch::nn::TransformerEncoder(torch::nn::TransformerEncoderOptions(layer,c.layers)));
    }
  }
  dropout_=register_module("dropout",torch::nn::Dropout(c.dropout_milli/1000.0));
  output_=register_module("output",torch::nn::Linear(c.hidden_width,c.output_width));
  enforce_constraints();
}
void validate_text_batch(const Batch& b,int64_t vocabulary) {
  const auto& ids=b.inputs;const auto& mask=b.mask;const auto& seg=b.segments;
  TORCH_CHECK(ids.device().is_cpu()&&mask.device().is_cpu()&&seg.device().is_cpu(),"CPU only");
  TORCH_CHECK(ids.dim()==2&&ids.size(0)>=1&&ids.size(0)<=64&&ids.size(1)>=1&&ids.size(1)<=256,"batch/length limit");
  TORCH_CHECK(ids.scalar_type()==torch::kInt64&&mask.scalar_type()==torch::kBool&&seg.scalar_type()==torch::kInt64,"text dtype");
  TORCH_CHECK(ids.sizes()==mask.sizes()&&ids.sizes()==seg.sizes(),"text shape");
  TORCH_CHECK(ids.min().item<int64_t>()>=0&&ids.max().item<int64_t>()<vocabulary,"token range");
  TORCH_CHECK(seg.min().item<int64_t>()>=0&&seg.max().item<int64_t>()<4,"segment range");
  TORCH_CHECK(mask.select(1,0).all().item<bool>()&&torch::equal(mask,ids.ne(0)),"padding mask");
  TORCH_CHECK(seg.masked_select(~mask).eq(0).all().item<bool>(),"padding segments");
  if(ids.size(1)>1)TORCH_CHECK((mask.slice(1,1).to(torch::kInt64)-mask.slice(1,0,-1).to(torch::kInt64)).le(0).all().item<bool>(),"right padding required");
}
torch::Tensor Model::forward(const Batch& b) {
  torch::Tensor h;
  if(config_.kind=="dense") {
    TORCH_CHECK(b.inputs.device().is_cpu()&&b.inputs.scalar_type()==torch::kFloat32&&b.inputs.dim()==2&&
      b.inputs.size(0)>=1&&b.inputs.size(0)<=64&&b.inputs.size(1)==config_.input_width&&torch::isfinite(b.inputs).all().item<bool>(),"dense input contract");
    h=torch::tanh(projection_->forward(b.inputs));
  } else {
    validate_text_batch(b,config_.vocabulary);
    if(config_.kind=="pooled") {
      auto content=b.mask.clone();for(auto c:config_.controls)content=content&b.inputs.ne(c);
      auto count=content.sum(1,true);TORCH_CHECK(count.gt(0).all().item<bool>(),"no pooled content");
      h=torch::gelu(projection_->forward((embedding_->forward(b.inputs)*content.unsqueeze(-1)).sum(1)/count.to(torch::kFloat32)));
    } else {
      auto pos=torch::arange(b.inputs.size(1),b.inputs.options()).unsqueeze(0);
      auto hidden=dropout_->forward(embedding_->forward(b.inputs)+positions_->forward(pos)+segments_->forward(b.segments))*b.mask.unsqueeze(-1);
      h=encoder_->forward(hidden.transpose(0,1),{},~b.mask).transpose(0,1).select(1,0);
    }
  }
  auto out=output_->forward(dropout_->forward(h));TORCH_CHECK(torch::isfinite(out).all().item<bool>(),"nonfinite output");return out;
}
void Model::enforce_constraints(){if(embedding_){torch::NoGradGuard g;embedding_->weight[0].zero_();}}
std::vector<std::pair<std::string,double>> Model::decay_roles() const {
  // Modules supply explicit roles; the trainer never guesses from names.
  std::set<std::string> decay;
  for(const auto& m:named_modules())if(dynamic_cast<torch::nn::LinearImpl*>(m.value().get()))decay.insert(m.key()+".weight");
  std::vector<std::pair<std::string,double>> result;for(const auto& p:named_parameters())result.push_back({p.key(),decay.contains(p.key())?1.0:0.0});return result;
}
ModelPtr make_seeded_model(const ModelConfig& c,int64_t seed) {
  TORCH_CHECK(seed>=0,"negative seed");torch::set_num_threads(1);torch::globalContext().setDeterministicAlgorithms(true,false);
  torch::manual_seed(seed);return std::make_shared<Model>(c);
}
torch::Tensor bernoulli_loss(const torch::Tensor& logits,const torch::Tensor& target) {
  TORCH_CHECK(logits.device().is_cpu()&&target.device().is_cpu()&&logits.scalar_type()==torch::kFloat32&&target.scalar_type()==torch::kFloat32&&
    logits.dim()==2&&logits.sizes()==target.sizes()&&target.numel()>0&&torch::isfinite(target).all().item<bool>()&&target.ge(0).all().item<bool>()&&target.le(1).all().item<bool>(),"Bernoulli target");
  return torch::nn::functional::binary_cross_entropy_with_logits(logits,target);
}
torch::Tensor categorical_loss(const torch::Tensor& logits,const torch::Tensor& target,const torch::Tensor& eligible) {
  TORCH_CHECK(logits.dim()==2&&target.dim()==1&&eligible.dim()==1&&target.size(0)==logits.size(0)&&target.sizes()==eligible.sizes()&&
    target.scalar_type()==torch::kInt64&&eligible.scalar_type()==torch::kBool,"categorical target");
  auto selected=eligible.nonzero().squeeze(1);if(!selected.numel())return logits.sum()*0;
  auto y=target.index_select(0,selected);TORCH_CHECK(y.min().item<int64_t>()>=0&&y.max().item<int64_t>()<logits.size(1),"eligible target range");
  return torch::nn::functional::cross_entropy(logits.index_select(0,selected),y);
}
Batch dense_batch(const std::vector<std::vector<float>>& x,const std::vector<std::vector<float>>& y,int64_t width,int64_t outputs) {
  TORCH_CHECK(!x.empty()&&x.size()<=64&&width>0&&width<=256&&outputs>0&&outputs<=256&&(y.empty()||y.size()==x.size()),"batch contract");
  std::vector<float> flat;for(const auto& row:x){TORCH_CHECK(row.size()==size_t(width),"feature width");for(auto v:row){TORCH_CHECK(std::isfinite(v),"nonfinite feature");flat.push_back(v);}}
  Batch b;b.inputs=torch::from_blob(flat.data(),{int64_t(x.size()),width},torch::kFloat32).clone();
  if(!y.empty()){flat.clear();for(const auto& row:y){TORCH_CHECK(row.size()==size_t(outputs),"target width");for(auto v:row)flat.push_back(v);}b.targets=torch::from_blob(flat.data(),{int64_t(y.size()),outputs},torch::kFloat32).clone();}return b;
}
void NumericalComposition::validate() const {TORCH_CHECK(bool(encode)&&bool(objective)&&bool(decode),"missing numerical operation");model_config.validate();TORCH_CHECK(!registry.descriptor().is_null(),"unresolved registry");}
std::string numerical_environment() {
  return canonical(Json{{"libtorch",TORCH_VERSION},{"compiler",__VERSION__},{"abi",_GLIBCXX_USE_CXX11_ABI},{"platform","linux.x86_64"},{"dtype","float32"},{"threads",1},{"deterministic",true}});
}
std::string save_model_bytes(ModelPtr m) {torch::serialize::OutputArchive a;m->save(a);std::ostringstream out;a.save_to(out);return out.str();}
void load_model_bytes(ModelPtr m,const std::string& bytes) {
  torch::serialize::InputArchive a;std::istringstream in(bytes);a.load_from(in,torch::kCPU);
  std::map<std::string,torch::Tensor> expected;std::set<std::string> modules,seen;
  for(const auto& p:m->named_parameters())expected.emplace(p.key(),p.value());
  for(const auto& p:m->named_buffers())expected.emplace(p.key(),p.value());
  for(const auto& p:m->named_modules())modules.insert(p.key());
  std::function<void(torch::serialize::InputArchive&,std::string)> inspect;
  inspect=[&](torch::serialize::InputArchive& archive,std::string prefix){for(const auto& k:archive.keys()){
    const auto name=prefix+k;torch::serialize::InputArchive child;
    if(archive.try_read(k,child)){TORCH_CHECK(modules.contains(name),"unknown archive module");inspect(child,name+".");}
    else {torch::Tensor value;TORCH_CHECK(expected.contains(name)&&seen.insert(name).second,"unknown/duplicate archive tensor");
      archive.read(k,value,m->named_buffers().contains(name));auto t=expected.at(name);
      TORCH_CHECK(value.device().is_cpu()&&value.scalar_type()==t.scalar_type()&&value.sizes()==t.sizes()&&torch::isfinite(value).all().item<bool>(),"archive key/shape/dtype contract");
    }} };
  inspect(a,"");TORCH_CHECK(seen.size()==expected.size(),"missing archive tensor");m->load(a);
  for(const auto& p:m->named_parameters())TORCH_CHECK(p.value().scalar_type()==torch::kFloat32&&p.value().device().is_cpu()&&torch::isfinite(p.value()).all().item<bool>(),"archive tensor invalid");
  m->enforce_constraints();
}
Json tensor_inventory(ModelPtr m) {
  Json result=Json::array();for(const auto& p:m->named_parameters())result.push_back({{"name",p.key()},{"dtype","float32"},{"shape",p.value().sizes().vec()},{"role","parameter"}});
  for(const auto& p:m->named_buffers())result.push_back({{"name",p.key()},{"dtype","float32"},{"shape",p.value().sizes().vec()},{"role","buffer"}});return result;
}
}
