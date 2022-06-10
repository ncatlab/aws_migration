function search() {
  if (!document.getElementById("search").value) {
    return
  }
  window.location = ROOT_URL +
    "/search?query=" +
    document.getElementById("search").value
}

document.getElementById("search").addEventListener(
  "keypress",
  function (keypress_event) {
    if (keypress_event.key === "Enter") {
      search()
    }
  })
