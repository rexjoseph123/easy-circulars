# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, List, Optional, Union

import numpy as np
from docarray import BaseDoc, DocList
from docarray.documents import AudioDoc
from docarray.typing import AudioUrl, ImageUrl
from pydantic import Field, conint, conlist, field_validator


class TopologyInfo:
    # will not keep forwarding to the downstream nodes in the black list
    # should be a pattern string
    downstream_black_list: Optional[list] = []

class TextDoc(BaseDoc, TopologyInfo):
    text: Union[str, List[str]] = None

class DocPath(BaseDoc):
    path: str
    chunk_size: int = 1500
    chunk_overlap: int = 100
    process_table: bool = False
    table_strategy: str = "fast"


class EmbedDoc(BaseDoc):
    text: Union[str, List[str]]
    embedding: Union[conlist(float, min_length=0), List[conlist(float, min_length=0)]]
    search_type: str = "similarity"
    file_name: str
    k: int = 4
    distance_threshold: Optional[float] = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    score_threshold: float = 0.2
    constraints: Optional[Union[Dict[str, Any], List[Dict[str, Any]], None]] = None


class EmbedMultimodalDoc(EmbedDoc):
    # extend EmbedDoc with these attributes
    url: Optional[ImageUrl] = Field(
        description="The path to the image. It can be remote (Web) URL, or a local file path.",
        default=None,
    )
    base64_image: Optional[str] = Field(
        description="The base64-based encoding of the image.",
        default=None,
    )

class SearchedDoc(BaseDoc):
    retrieved_docs: DocList[TextDoc]
    initial_query: str
    top_n: int = 1

    class Config:
        json_encoders = {np.ndarray: lambda x: x.tolist()}


class SearchedMultimodalDoc(SearchedDoc):
    metadata: List[Dict[str, Any]]


class LLMParams(BaseDoc):
    model: Optional[str] = None
    max_tokens: int = 1024
    max_new_tokens: int = 1024
    top_k: int = 10
    top_p: float = 0.95
    typical_p: float = 0.95
    temperature: float = 0.01
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    repetition_penalty: float = 1.03
    stream: bool = True
    language: str = "auto"  # can be "en", "zh"

    chat_template: Optional[str] = Field(
        default=None,
        description=(
            "A template to use for this conversion. "
            "If this is not passed, the model's default chat template will be "
            "used instead. We recommend that the template contains {context} and {question} for rag,"
            "or only contains {question} for chat completion without rag."
        ),
    )

class RerankerParms(BaseDoc):
    top_n: int = 1


class RetrieverParms(BaseDoc):
    search_type: str = "similarity"
    file_name: str
    k: int = 4
    distance_threshold: Optional[float] = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    score_threshold: float = 0.2



