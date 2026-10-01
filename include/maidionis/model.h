#pragma once
#include "maidionis/contracts.h"
#include <torch/torch.h>
#include <functional>
#include <mutex>

namespace maidionis {
struct ModelConfig {
  std::string kind="dense";
  int64_t input_width=2, hidden_width=8, output_width=2, dropout_milli=100;
  int64_t vocabulary=0, layers=4, heads=4, ffn_width=1024, max_length=256;
  std::vector<int64_t> controls;
  void validate() const;
  Json json() const;
  static ModelConfig from_json(const Json&);
};
struct Batch { torch::Tensor inputs,targets,mask,segments,target_mask; };
class Model : public torch::nn::Module {
 public:
  explicit Model(const ModelConfig&);
  torch::Tensor forward(const Batch&);
  const ModelConfig& config() const { return config_; }
  void enforce_constraints();
  std::vector<std::pair<std::string,double>> decay_roles() const;
 private:
  ModelConfig config_;
  torch::nn::Linear projection_{nullptr},output_{nullptr};
  torch::nn::Embedding embedding_{nullptr},positions_{nullptr},segments_{nullptr};
  torch::nn::TransformerEncoder encoder_{nullptr};
  torch::nn::Dropout dropout_{nullptr};
};
using ModelPtr=std::shared_ptr<Model>;
ModelPtr make_seeded_model(const ModelConfig&,int64_t seed);
std::recursive_mutex& numerical_mutex();
size_t model_construction_count();
torch::Tensor bernoulli_loss(const torch::Tensor&,const torch::Tensor&);
torch::Tensor categorical_loss(const torch::Tensor&,const torch::Tensor&,const torch::Tensor& eligible);
void validate_text_batch(const Batch&,int64_t vocabulary);
Batch dense_batch(const std::vector<std::vector<float>>&,const std::vector<std::vector<float>>&,int64_t width,int64_t outputs);
struct NumericalComposition {
  Registry registry;
  ModelConfig model_config;
  std::function<Batch(const std::vector<Json>&)> encode;
  std::function<torch::Tensor(const torch::Tensor&,const Batch&)> objective;
  std::function<Json(const torch::Tensor&)> decode;
  // The specialization revalidates semantic roots/eligibility without a teacher.
  std::function<void(const Json&,const Json&,const Json&,const Json&)> verify_dataset_row;
  void validate() const;
};
std::string numerical_environment();
std::string save_model_bytes(ModelPtr);
void load_model_bytes(ModelPtr,const std::string&);
Json tensor_inventory(ModelPtr);
}
