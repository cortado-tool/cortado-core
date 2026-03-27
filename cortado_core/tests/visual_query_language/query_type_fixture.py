import pytest
from cortado_core.visual_query_language.query import QueryType


@pytest.fixture(params=[QueryType.DFS, QueryType.BFS, QueryType.VM, QueryType.VM_LAZY])
def query_type(request):
    return request.param
