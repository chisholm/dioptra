# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode



from __future__ import annotations 
from dioptra import pyplugs 
from scipy.stats import wasserstein_distance 
from sklearn.metrics.pairwise import paired_distances 
from structlog.stdlib import BoundLogger 
from typing import Any 
from typing import Callable 
from typing import Dict 
from typing import List 
from typing import Optional 
from typing import Tuple 
import numpy as np
import pytest
import structlog 

@pytest.mark.parametrize(
    "request_",
    [
        [],
        [{"name":"a", "func":"l_inf_norm"},{"name":"b", "func":"l_1_norm"},
        {"name":"c", "func":"l_2_norm"},{"name":"d", "func":"paired_cosine_similarities"},
        {"name":"e", "func":"paired_euclidean_distances"},{"name":"f", "func":"paired_manhattan_distances"},
        {"name":"g", "func":"paired_wasserstein_distances"}],
        [{"name":"a", "func":"l_inf_norm"},{"name":"b", "func":"l_1_norm"}],
        [{"name":"c", "func":"l_1_norm"},{"name":"d", "func":"l_inf_norm"}],
        [{"name":"e", "func":"paired_wasserstein_distances"}],
    ]
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_get_distance_metric_list(request_, y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import get_distance_metric_list
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result: list = get_distance_metric_list(request_)
    for res in result:
        assert isinstance(res[0], str)
        dists = res[1](y_true, y_pred)
        assert all([isinstance(dist, float) for dist in dists])

@pytest.mark.parametrize(
    "func",
    [
        "l_inf_norm","l_1_norm","l_2_norm","paired_cosine_similarities","paired_euclidean_distances","paired_manhattan_distances","paired_wasserstein_distances",
    ],
)
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_get_distance_metric(func, y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import get_distance_metric
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    metric = get_distance_metric(func)
    results = metric(y_true,y_pred)
    assert all([isinstance(res, float) for res in results])


@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_l_inf_norm(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import l_inf_norm
    from dioptra_builtins.metrics.distance import _flatten_batch

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result: np.ndarray = l_inf_norm(y_true, y_pred)
        
    y_diff: np.ndarray = _flatten_batch(y_true - y_pred)
    y_diff_l_norm: np.ndarray = np.linalg.norm(y_diff, axis=1, ord=np.inf)
    
    assert all([isinstance(res, float) for res in result])
    assert np.array_equal(y_diff_l_norm, result)


@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_l_1_norm(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import l_1_norm
    from dioptra_builtins.metrics.distance import _flatten_batch
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result: np.ndarray = l_1_norm(y_true, y_pred)
        
    y_diff: np.ndarray = _flatten_batch(y_true - y_pred)
    y_diff_l_norm: np.ndarray = np.linalg.norm(y_diff, axis=1, ord=1)

    
    assert all([isinstance(res, float) for res in result])
    assert np.array_equal(y_diff_l_norm, result)

@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_l_2_norm(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import l_2_norm
    from dioptra_builtins.metrics.distance import _flatten_batch

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result: np.ndarray = l_2_norm(y_true, y_pred)
        
    y_diff: np.ndarray = _flatten_batch(y_true - y_pred)
    y_diff_l_norm: np.ndarray = np.linalg.norm(y_diff, axis=1, ord=2)

    
    assert all([isinstance(res, float) for res in result])
    assert np.array_equal(y_diff_l_norm, result)

@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_paired_cosine_similarities(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import paired_cosine_similarities
    from dioptra_builtins.metrics.distance import _normalize_batch
    from dioptra_builtins.metrics.distance import _flatten_batch
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result: np.ndarray = paired_cosine_similarities(y_true, y_pred)
    
    
    
    y_true_normalized: np.ndarray = _normalize_batch(_flatten_batch(y_true), order=2)
    y_pred_normalized: np.ndarray = _normalize_batch(_flatten_batch(y_pred), order=2)
    metric: np.ndarray = np.sum(y_true_normalized * y_pred_normalized, axis=1)
        
    assert all([isinstance(res, float) for res in result])
    assert np.array_equal(metric, result, equal_nan=True)

@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_paired_euclidean_distances(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import paired_euclidean_distances
    from dioptra_builtins.metrics.distance import _flatten_batch

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result : np.ndarray = paired_euclidean_distances(y_true, y_pred)
        
    y_diff: np.ndarray = _flatten_batch(y_true - y_pred)
    y_diff_l_norm: np.ndarray = np.linalg.norm(y_diff, axis=1, ord=2)

    
    assert all([isinstance(res, float) for res in result])
    assert np.array_equal(y_diff_l_norm, result)

@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_paired_manhattan_distances(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import paired_manhattan_distances
    from dioptra_builtins.metrics.distance import _flatten_batch
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result: np.ndarray = paired_manhattan_distances(y_true, y_pred)
        
    y_diff: np.ndarray = _flatten_batch(y_true - y_pred)
    y_diff_l_norm: np.ndarray = np.linalg.norm(y_diff, axis=1, ord=1)

    
    assert all([isinstance(res, float) for res in result])
    assert np.array_equal(y_diff_l_norm, result)

@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
def test_paired_wasserstein_distances(y_true, y_pred) -> None:
    from dioptra_builtins.metrics.distance import paired_wasserstein_distances
    from dioptra_builtins.metrics.distance import _flatten_batch
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    result : np.ndarray = paired_wasserstein_distances(y_true, y_pred)
    metric: np.ndarray = paired_distances(
        X=_flatten_batch(y_true), Y=_flatten_batch(y_pred), 
        metric=lambda x,y: 
            wasserstein_distance(u_values=x,v_values=y))
    
    assert all([isinstance(res, float) for res in result])
    assert np.array_equal(metric, result)

@pytest.mark.parametrize(
    "X",
    [
        [[[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]],
        [[[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]],
        [[1,2,3,4,5,6],[-2,4,5,-9,0,1]],
        [[10],[1]],
    ]
)
def test__flatten_batch(X) -> None:
    from dioptra_builtins.metrics.distance import _flatten_batch
    
    X = np.array(X)

    result: np.ndarray = _flatten_batch(X)
    expected: np.ndarray = X.reshape(X.shape[0], int(np.prod(X.shape[1:])))
    
    assert result.shape == expected.shape
    assert np.array_equal(expected, result)
    
@pytest.mark.parametrize(
    ("y_true", "y_pred"),
    [
        ([[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]),
        ([[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]),
        ([1,2,3,4,5,6],[-2,4,5,-9,0,1]),
        ([10],[1]),
    ]
)
@pytest.mark.parametrize(
    "order",
    [
        1,2,3,4,5,6,8,20,np.inf
    ],
)
def test__matrix_difference_l_norm(y_true, y_pred, order) -> None:
    from dioptra_builtins.metrics.distance import _matrix_difference_l_norm
    from dioptra_builtins.metrics.distance import _flatten_batch
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    result: np.ndarray = _matrix_difference_l_norm(y_true, y_pred, order)
    expected: np.ndarray = np.linalg.norm(_flatten_batch(y_true - y_pred), axis=1, ord=order)
    
    assert np.array_equal(expected, result)

@pytest.mark.parametrize(
    "X",
    [
        [[[1,2,3],[3,4,5]],[[-2,4,5],[-9,0,1]]],
        [[[1,2],[3,4],[4,5]],[[-2,4],[5,-9],[0,1]]],
        [[1,2,3,4,5,6],[-2,4,5,-9,0,1]],
        [[10],[1]],
    ],
)
@pytest.mark.parametrize(
    "order",
    [
        1,2,3,4,5,6,8,20,np.inf
    ],
)
def test__normalize_batch(X, order) -> None:
    from dioptra_builtins.metrics.distance import _normalize_batch
    from dioptra_builtins.metrics.distance import _flatten_batch
    
    X = _flatten_batch(np.array(X)).astype(float)
    result: np.ndarray = _normalize_batch(X, order)
       
    norm = np.linalg.norm(X, axis=1, ord=order)
    norm = norm.reshape((norm.shape[0], 1))
    unnormed = result * norm 
    assert np.allclose(unnormed, X)