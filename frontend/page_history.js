TODO: Not sure we need any of this, but can be used in history page. Change S3 user policy for metadata bucket to prevent anybody seeing IP address.

function current_revision() {
  return fetch(LATEST_REVISION_ROOT_URL + "/" + page_name)
    .then(response => {
      if (response.status == 200) {
        return response.text()
      }
      throw new Error("Failed to fetch current revision")
    })
}

function set_last_revised(current_revision) {
  fetch("../../history/metadata/" + current_revision)
    .then(response =>
      if (response.status == 200) {
        return response.json()
      }
      throw new Error("Failed to fetch revision metadata")
    })
    .then(metadata => {
      date = new
      document.getElementById("last_updated").innerHTML =
        "Last revised:
    })
}

current_revision().then(current_revision => {
    set_last_revised(current_revision)
})
