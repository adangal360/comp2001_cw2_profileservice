# Basic service health endpoint.
# This endpoint confirms that the API process is running and responsive.
def check():
    return {"status": "ok"}, 200