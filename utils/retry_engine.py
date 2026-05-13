# =========================================================
# RETRY ENGINE
# =========================================================

import time

# =========================================================
# RETRY REQUEST
# =========================================================

def retry_request(

    func,

    retries=5,

    delay=2
):

    last_exception = None

    for attempt in range(retries):

        try:

            return func()

        except Exception as e:

            last_exception = e

            time.sleep(
                delay
            )

    raise last_exception
