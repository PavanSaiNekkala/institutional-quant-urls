# =========================================================
# RETRY ENGINE
# =========================================================

import time
import random

# =========================================================
# RETRY REQUEST
# =========================================================

def retry_request(

    func,

    retries=6,

    base_delay=5
):

    last_exception = None

    for attempt in range(retries):

        try:

            return func()

        except Exception as e:

            last_exception = e

            error_text = str(e)

            # =================================================
            # YAHOO RATE LIMIT DETECTION
            # =================================================

            if (

                "Too Many Requests" in error_text

                or

                "429" in error_text

                or

                "Rate limited" in error_text
            ):

                wait_time = (

                    30

                    + random.uniform(
                        5,
                        15
                    )
                )

                print(
                    f"Yahoo cooldown "
                    f"{wait_time:.2f}s"
                )

            else:

                wait_time = (

                    base_delay

                    * (attempt + 1)

                    +

                    random.uniform(
                        2,
                        6
                    )
                )

            print(

                f"Retry {attempt + 1}/{retries}"

                f" | Waiting {wait_time:.2f}s"

            )

            time.sleep(wait_time)

    raise last_exception
