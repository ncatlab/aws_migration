function set_latest_revision(page_name) {
  return fetch(LATEST_REVISION_ROOT_URL + "/" + page_name)
    .then(response => {
      if (response.status == 200) {
        document.getElementById("title").setAttribute("has_history", "")
        return response.text()
      } else if (response.status == 404) {
        document.getElementById("top_error_messages").innerText =
          "No page with the name '" +
          page_name +
          "' is able to be edited"
        document.getElementById("top_error_messages").style.display = "block"
      } else {
        document.getElementById("top_error_messages").innerHTML =
          "An unknown error occurred when trying to determine the latest revision of the page. HTTP response status: " +
          response.status +
          ". You will not be able to submit any changes to the page. Please raise this at the <a href=\"" +
          FORUM_ROOT_URL +
          "\">" +
          FORUM_NAME +
          "</a>"
        document.getElementById("top_error_messages").style.display = "block"
      }
    })
    .then(responseText => {
      if (responseText) {
        document.getElementById("title").setAttribute("latest_revision", responseText)
      }
    })
}

function clear_submit_error_messages() {
  document.getElementById("submit_error_messages").style.display = "none"
  document.getElementById("submit_error_messages").innerHTML = ""
}

function passed_checks() {
  if (!document.getElementById("title").hasAttribute("page_found")) {
    return false
  } else if (!document.getElementById("edit_source").value.trim()) {
    return false
  } else if (!document.getElementById("author").value.trim()) {
    document.getElementById("submit_error_messages").innerHTML =
      "Please provide a name in the 'Author' field. Typically, nLab authors use their full, real name. If you do not wish to provide your name, please use 'Anonymous' (without the quotation marks)."
    document.getElementById("submit_error_messages").style.display = "block"
    return false
  } else if (!document.getElementById("title").hasAttribute("latest_revision")) {
    document.getElementById("submit_error_messages").innerHTML =
      "Cannot submit changes as no latest revision information could be fetched for the page. See the error message at the top of the page"
    document.getElementById("submit_error_messages").style.display = "block"
    return false
  } else if (!document.getElementById("title").hasAttribute("has_history")) {
    document.getElementById("submit_error_messages").innerHTML =
      "Editing is not yet permitted for this page as its history has not yet been rendered"
    document.getElementById("submit_error_messages").style.display = "block"
    return false
  }
  return true
}

function parse_render_and_store() {
  fetch(
    STORE_EDIT_ROOT_URL,
    {
      "method": "PUT",
      "body": JSON.stringify({
        "page_name": document.getElementById("title").getAttribute("page_name"),
        "revision_number": parseInt(document.getElementById("title").getAttribute("latest_revision")) + 1,
        "author": document.getElementById("author").value.trim(),
        "source": document.getElementById("edit_source").value
      })
    })
  .then(response => {
    if (response.status != 200) {
      document.getElementById("submit").classList.remove("spinner")
      document.getElementById("edit_preview").style.display = "inline-block"
      document.getElementById("edit_submit").style.display = "inline-block"
      return response.text()
    }
    document.getElementById("edit_submit").setAttribute("edit_store_succeeded", "")
  })
  .then(responseText => {
    if (document.getElementById("edit_submit").hasAttribute("edit_store_succeeded")) {
      var announcement = document.getElementById("announcement").value.trim()
      if (announcement) {
        fetch(
          NFORUM_ANNOUNCEMENT_URL,
          {
            "method": "POST",
            "body": JSON.stringify({
              "page_name": document.getElementById("title").getAttribute("page_name"),
              "author": document.getElementById("author").value.trim(),
              "announcement": announcement,
              "revision_number": parseInt(document.getElementById("title").getAttribute("latest_revision")) + 1
            })
          })
      }
      fetch(
        UPDATE_PAGE_HISTORY_URL + "/" + document.getElementById("title").getAttribute("page_name"),
        {
          "method": "PUT"
        })
      .then(response => {
        if (response.status != 200) {
          document.getElementById("submit").classList.remove("spinner")
          document.getElementById("submit_error_messages").innerHTML =
            "Edit successfully made, but an error occurred when updating the page history. Please raise this at the <a href=\"" +
            FORUM_ROOT_URL +
            "\">" +
            FORUM_NAME +
            ".</a>"
          document.getElementById("submit_error_messages").style.display = "block"
          location.href = "#submit_error_messages"
          document.getElementById("preview").innerHTML = ""
          document.getElementById("preview_separator").style.display = "none"
        } else {
          window.location = ROOT_URL + "/show/" + document.getElementById("title").getAttribute("page_name")
        }
      })
    } else {
      document.getElementById("submit_error_messages").innerText = responseText
      document.getElementById("submit_error_messages").style.display = "block"
      location.href = "#submit_error_messages"
      document.getElementById("preview").innerHTML = ""
      document.getElementById("preview_separator").style.display = "none"
    }
  })
}

function submit_edit() {
  clear_submit_error_messages()
  document.getElementById("edit_submit").removeAttribute("edit_store_succeeded")
  if (!passed_checks()) {
    return
  }
  document.getElementById("edit_submit").style.display = "none"
  document.getElementById("edit_preview").style.display = "none"
  document.getElementById("submit").classList.add("spinner")
  parse_render_and_store()
}

document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("edit_submit").addEventListener("click", submit_edit)
  if (!document.getElementById("title").hasAttribute("page_name")) {
    return
  }
  set_latest_revision(document.getElementById("title").getAttribute("page_name"))
})
