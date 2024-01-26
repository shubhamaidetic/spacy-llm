import copy

import pytest
import spacy
from confection import Config  # type: ignore[import]
from thinc.compat import has_torch_cuda_gpu

from ...compat import torch

_PIPE_CFG = {
    "model": {
        "@llm_models": "spacy.HuggingFace.v1",
        "name": "stablelm-base-alpha-3b",
    },
    "task": {"@llm_tasks": "spacy.NoOp.v1"},
    "save_io": True,
}

_NLP_CONFIG = """
[nlp]
lang = "en"
pipeline = ["llm"]
batch_size = 128

[components]

[components.llm]
factory = "llm"

[components.llm.task]
@llm_tasks = "spacy.NoOp.v1"

[components.llm.model]
@llm_models = "spacy.HuggingFace.v1"
name = "stablelm-base-alpha-3b"
"""


@pytest.mark.gpu
@pytest.mark.skipif(not has_torch_cuda_gpu, reason="needs GPU & CUDA")
@pytest.mark.parametrize("name", ("stablelm-base-alpha-3b", "stablelm-tuned-alpha-3b"))
def test_init(name: str):
    """Test initialization and simple run.
    name (str): Name of model to run.
    """
    nlp = spacy.blank("en")
    cfg = copy.deepcopy(_PIPE_CFG)
    cfg["model"]["name"] = name  # type: ignore[index]
    nlp.add_pipe("llm", config=cfg)
    doc = nlp("This is a test.")
    torch.cuda.empty_cache()
    assert not doc.user_data["llm_io"]["llm"]["response"][0].startswith(
        doc.user_data["llm_io"]["llm"]["prompt"][0]
    )


@pytest.mark.gpu
@pytest.mark.skipif(not has_torch_cuda_gpu, reason="needs GPU & CUDA")
def test_init_from_config():
    orig_config = Config().from_str(_NLP_CONFIG)
    nlp = spacy.util.load_model_from_config(orig_config, auto_fill=True)
    assert nlp.pipe_names == ["llm"]
    torch.cuda.empty_cache()


@pytest.mark.gpu
@pytest.mark.skipif(not has_torch_cuda_gpu, reason="needs GPU & CUDA")
def test_init_with_set_config():
    """Test initialization and simple run with changed config."""
    nlp = spacy.blank("en")
    cfg = copy.deepcopy(_PIPE_CFG)
    cfg["model"]["config_run"] = {"temperature": 0.3}
    nlp.add_pipe("llm", config=cfg)
    nlp("This is a test.")
    torch.cuda.empty_cache()


@pytest.mark.gpu
@pytest.mark.skipif(not has_torch_cuda_gpu, reason="needs GPU & CUDA")
def test_invalid_model():
    orig_config = Config().from_str(_NLP_CONFIG)
    config = copy.deepcopy(orig_config)
    config["components"]["llm"]["model"]["name"] = "anything-else"
    with pytest.raises(ValueError, match="unexpected value; permitted:"):
        spacy.util.load_model_from_config(config, auto_fill=True)
