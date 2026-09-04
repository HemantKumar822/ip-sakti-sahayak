import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.resilience import is_rate_limit_error, retry_with_backoff

# ---------------------------------------------------------------------------
# Tests for is_rate_limit_error
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error_msg",
    [
        "HTTP 429: Too Many Requests",
        "ResourceExhausted: Quota exceeded for quota metric",
        "Google API quota exceeded, please retry later",
        "Resource exhausted: generating tokens limit reached",
        "Encountered rate limit on Gemini endpoint",
        "Too Many Requests: rate limit reached",
        "RESOURCEEXHAUSTED",
    ],
)
def test_is_rate_limit_error_positive(error_msg: str):
    err = RuntimeError(error_msg)
    assert is_rate_limit_error(err) is True


@pytest.mark.parametrize(
    "error",
    [
        ValueError("Invalid prompt parameter"),
        KeyError("doc_id not found"),
        RuntimeError("Database connection failed"),
        Exception("Internal Server Error (500)"),
        TimeoutError("Connection timed out"),
    ],
)
def test_is_rate_limit_error_negative(error: Exception):
    assert is_rate_limit_error(error) is False


# ---------------------------------------------------------------------------
# Tests for @retry_with_backoff (Async)
# ---------------------------------------------------------------------------


def test_async_success_first_try():
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def sample_async():
        nonlocal call_count
        call_count += 1
        return "success"

    async def run():
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            res = await sample_async()
            assert res == "success"
            assert call_count == 1
            mock_sleep.assert_not_called()

    asyncio.run(run())


def test_async_fails_twice_then_succeeds_with_backoff():
    call_count = 0

    @retry_with_backoff(
        max_retries=3, initial_delay=1.0, backoff_factor=2.0, jitter=False
    )
    async def sample_async():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("429 ResourceExhausted: Quota exceeded")
        return "recovered"

    async def run():
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            res = await sample_async()
            assert res == "recovered"
            assert call_count == 3
            assert mock_sleep.call_count == 2
            # Attempt 0 error: delay = 1.0; Attempt 1 error: delay = 2.0
            assert mock_sleep.call_args_list[0].args[0] == pytest.approx(1.0)
            assert mock_sleep.call_args_list[1].args[0] == pytest.approx(2.0)

    asyncio.run(run())


def test_async_jitter_calculation():
    call_count = 0

    @retry_with_backoff(
        max_retries=2, initial_delay=2.0, backoff_factor=3.0, jitter=True
    )
    async def sample_async():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("429 rate limit")
        return "done"

    async def run():
        # With random.random returning 0.5: sleep_time = delay * (1 + 0.5 * 0.5) = 2.0 * 1.25 = 2.5
        with (
            patch("random.random", return_value=0.5),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            res = await sample_async()
            assert res == "done"
            assert call_count == 2
            mock_sleep.assert_called_once_with(pytest.approx(2.5))

    asyncio.run(run())


def test_async_unrecoverable_error_fails_immediately():
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def sample_async():
        nonlocal call_count
        call_count += 1
        raise ValueError("InvalidApiKey: Key not authorized")

    async def run():
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(ValueError, match="InvalidApiKey"):
                await sample_async()
            assert call_count == 1
            mock_sleep.assert_not_called()

    asyncio.run(run())


def test_async_retry_exhaustion_raises():
    call_count = 0

    @retry_with_backoff(
        max_retries=2, initial_delay=0.5, backoff_factor=2.0, jitter=False
    )
    async def sample_async():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("429 Too Many Requests")

    async def run():
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RuntimeError, match="429 Too Many Requests"):
                await sample_async()
            # Initial attempt + 2 retries = 3 calls
            assert call_count == 3
            assert mock_sleep.call_count == 2

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Tests for @retry_with_backoff (Sync)
# ---------------------------------------------------------------------------


def test_sync_success_first_try():
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def sample_sync():
        nonlocal call_count
        call_count += 1
        return "sync_success"

    with patch("time.sleep") as mock_sleep:
        res = sample_sync()
        assert res == "sync_success"
        assert call_count == 1
        mock_sleep.assert_not_called()


def test_sync_fails_twice_then_succeeds_with_backoff():
    call_count = 0

    @retry_with_backoff(
        max_retries=3, initial_delay=1.0, backoff_factor=2.0, jitter=False
    )
    def sample_sync():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("ResourceExhausted: 429 quota")
        return "sync_recovered"

    with patch("time.sleep") as mock_sleep:
        res = sample_sync()
        assert res == "sync_recovered"
        assert call_count == 3
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list[0].args[0] == pytest.approx(1.0)
        assert mock_sleep.call_args_list[1].args[0] == pytest.approx(2.0)


def test_sync_jitter_calculation():
    call_count = 0

    @retry_with_backoff(
        max_retries=2, initial_delay=4.0, backoff_factor=2.0, jitter=True
    )
    def sample_sync():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("429 rate limit")
        return "sync_done"

    # With random.random returning 0.6: sleep_time = 4.0 * (1 + 0.6 * 0.5) = 4.0 * 1.3 = 5.2
    with (
        patch("random.random", return_value=0.6),
        patch("time.sleep") as mock_sleep,
    ):
        res = sample_sync()
        assert res == "sync_done"
        assert call_count == 2
        mock_sleep.assert_called_once_with(pytest.approx(5.2))


def test_sync_unrecoverable_error_fails_immediately():
    call_count = 0

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def sample_sync():
        nonlocal call_count
        call_count += 1
        raise KeyError("Invalid key provided")

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(KeyError, match="Invalid key provided"):
            sample_sync()
        assert call_count == 1
        mock_sleep.assert_not_called()


def test_sync_retry_exhaustion_raises():
    call_count = 0

    @retry_with_backoff(
        max_retries=2, initial_delay=0.5, backoff_factor=2.0, jitter=False
    )
    def sample_sync():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("429 Too Many Requests")

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError, match="429 Too Many Requests"):
            sample_sync()
        assert call_count == 3
        assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# Tests for Custom Retry Predicate
# ---------------------------------------------------------------------------


def test_custom_predicate_retries_only_matching():
    call_count = 0

    def is_timeout_error(e: BaseException) -> bool:
        return isinstance(e, TimeoutError)

    @retry_with_backoff(
        max_retries=2, initial_delay=1.0, jitter=False, retry_predicate=is_timeout_error
    )
    def custom_fn():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("Socket timed out")
        return "custom_success"

    with patch("time.sleep") as mock_sleep:
        res = custom_fn()
        assert res == "custom_success"
        assert call_count == 2
        mock_sleep.assert_called_once_with(pytest.approx(1.0))


def test_custom_predicate_rejects_rate_limit_error():
    call_count = 0

    def is_timeout_error(e: BaseException) -> bool:
        return isinstance(e, TimeoutError)

    @retry_with_backoff(
        max_retries=2, initial_delay=1.0, jitter=False, retry_predicate=is_timeout_error
    )
    def custom_fn():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("429 Quota Exceeded")

    with patch("time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError, match="429 Quota Exceeded"):
            custom_fn()
        # Custom predicate returned False, so it should not retry
        assert call_count == 1
        mock_sleep.assert_not_called()
