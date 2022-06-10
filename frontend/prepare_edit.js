function page_name() {
  const query_parameters = new Proxy(
    new URLSearchParams(window.location.search),
      {
        get: (query_parameters, key) => query_parameters.get(key),
      }
  )
  const page_name = query_parameters.page_name
  if (!page_name) {
    return
  }
  document.getElementById("title").setAttribute("page_name", page_name)
  document.getElementById("top_header").innerText = "Edit – " + page_name
}

function page_source() {
  fetch(
      "../nlab/source/" + document.getElementById("title").getAttribute("page_name"))
    .then(response => {
      if (response.status != 200) {
        document.getElementById("top_error_messages").innerHTML =
          "<p>There is no page with the name <em>" +
          document.getElementById("title").getAttribute("page_name") +
          "</em></p>"
        document.getElementById("top_error_messages").style.display = "block"
        return ""
      } else {
        document.getElementById("title").setAttribute("page_found", "")
        return response.text()
      }
    })
    .then(source => document.getElementById("edit_source").value = source)
}

function nforum_link() {
  var page_name = document.getElementById("title").getAttribute("page_name")
  fetch(
      DISCUSSION_THREAD_ROOT_URL + page_name)
    .then(response => {
      if (response.status == 200) {
        return response.text()
      }
    })
    .then(discussion_link => {
      if (discussion_link) {
        document.getElementById("where_comments_added").innerHTML =
          "Your comments will be added to the <a href=\"" +
          discussion_link + "\">" +
          FORUM_NAME +
          " discussion thread</a> for this page."
      } else {
        document.getElementById("where_comments_added").innerHTML =
          "A discussion thread for this page will be created at the <a href=\"" +
          FORUM_ROOT_URL +
          "\">" +
          FORUM_NAME +
          "</a>, and your comments added to it."
      }
    })
}

document.addEventListener("DOMContentLoaded", function () {
  page_name()
  if (document.getElementById("title").hasAttribute("page_name")) {
    page_source()
    nforum_link()
  }
})
