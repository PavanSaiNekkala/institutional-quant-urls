# =========================================================
# FAILURE HANDLER
# =========================================================

def categorize_failure(error):

    try:

        error_text = str(
            error
        ).lower()

        # =================================================
        # YAHOO RATE LIMIT
        # =================================================

        if (

            "too many requests" in error_text

            or

            "429" in error_text

            or

            "rate limited" in error_text
        ):

            return "RATE_LIMIT"

        # =================================================
        # TIMEOUT
        # =================================================

        if (

            "timeout" in error_text

            or

            "timed out" in error_text
        ):

            return "TIMEOUT"

        # =================================================
        # CONNECTION
        # =================================================

        if (

            "connection" in error_text

            or

            "remote end closed" in error_text

            or

            "connection reset" in error_text
        ):

            return "CONNECTION_ERROR"

        # =================================================
        # JSON / PARSING
        # =================================================

        if (

            "json" in error_text

            or

            "decode" in error_text
        ):

            return "JSON_ERROR"

        # =================================================
        # DELISTED
        # =================================================

        if (

            "possibly delisted" in error_text

            or

            "no data found" in error_text
        ):

            return "DELISTED"

        # =================================================
        # INVALID SYMBOL
        # =================================================

        if (

            "invalid" in error_text

            or

            "not found" in error_text
        ):

            return "INVALID_SYMBOL"

        # =================================================
        # DEFAULT
        # =================================================

        return "UNKNOWN_ERROR"

    except:

        return "UNKNOWN_ERROR"
