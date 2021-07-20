import gc
import multiprocessing as mp
from contextlib import suppress

import psutil
import pytest

from hivemind.utils import get_logger
from hivemind.utils.mpfuture import MPFuture


logger = get_logger(__name__)


@pytest.fixture(autouse=True, scope="session")
def cleanup_children():
    yield

    gc.collect()  # Call .__del__() for removed objects

    children = psutil.Process().children(recursive=True)
    if children:
        logger.info(f"Cleaning up {len(children)} leftover child processes")
        for child in children:
            with suppress(psutil.NoSuchProcess):
                child.terminate()
        psutil.wait_procs(children, timeout=1)
        for child in children:
            with suppress(psutil.NoSuchProcess):
                child.kill()

    # Killing child processes may leave the global locks in MPFuture acquired
    # or the global state broken, so we reset them
    MPFuture._initialization_lock = mp.Lock()
    MPFuture._update_lock = mp.Lock()
    MPFuture._active_pid = None  # This will force to reset the global state
