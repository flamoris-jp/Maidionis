#include "maidionis/model.h"
#include <iostream>
using namespace maidionis;
void check(bool v){if(!v)throw std::runtime_error("test assertion");}
template<class F>void rejects(F f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}check(failed);}
int main(){try {
  ModelConfig c;auto a=make_seeded_model(c,42);torch::rand({100});auto b=make_seeded_model(c,42),d=make_seeded_model(c,43);
  check(torch::equal(a->parameters()[0],b->parameters()[0]));check(!torch::equal(a->parameters()[0],d->parameters()[0]));
  auto batch=dense_batch({{0,1},{1,0}},{{1,0},{0,1}},2,2);a->eval();auto before=a->forward(batch);
  auto archive=save_model_bytes(a);load_model_bytes(b,archive);b->eval();check(torch::equal(before,b->forward(batch)));
  auto loss=bernoulli_loss(a->forward(batch),batch.targets);loss.backward();check(a->parameters()[0].grad().abs().sum().item<double>()>0);
  auto logits=torch::zeros({2,3},torch::requires_grad());auto masked=categorical_loss(logits,torch::tensor({-999,1},torch::kInt64),torch::tensor({false,true},torch::kBool));masked.backward();
  check(logits.grad()[0].abs().sum().item<double>()==0);rejects([&]{dense_batch({{1}},{{1,0}},2,2);});
  for(const auto& kind:{"pooled","encoder"}) {
    ModelConfig text;text.kind=kind;text.hidden_width=256;text.vocabulary=32;text.controls={2,3};text.dropout_milli=0;
    auto model=make_seeded_model(text,42);model->eval();Batch x;x.inputs=torch::tensor({{2,4,5,0},{2,6,0,0}},torch::kInt64);x.mask=x.inputs.ne(0);x.segments=torch::zeros_like(x.inputs);
    auto out=model->forward(x);Batch one;one.inputs=x.inputs.slice(0,0,1).slice(1,0,3);one.mask=one.inputs.ne(0);one.segments=torch::zeros_like(one.inputs);
    check(torch::allclose(out.slice(0,0,1),model->forward(one),1e-5,1e-6));auto copy=make_seeded_model(text,7);load_model_bytes(copy,save_model_bytes(model));copy->eval();check(torch::equal(out,copy->forward(x)));
    x.mask[0][3]=true;rejects([&]{model->forward(x);});
  }
  std::cout<<"native model contracts passed\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
